# AGRIFLOW-AI — Podman WSL2 Bridge Networking Repair Report

| Field | Value |
|---|---|
| **Document type** | Infrastructure repair / validation |
| **Date** | 2026-08-16 |
| **Scope** | Podman Machine bridge networking only |
| **AGRIFLOW repository config changes** | **None** (this report file only) |
| **Destructive actions** | None (`down -v`, volume rm, system reset/prune, DB reset, machine recreate, WSL reset not used) |

---

## 1. Objective

Repair Podman Machine bridge networking on this Windows 11 host so that:

1. Normal default-bridge `podman run` works
2. Container DNS / container-to-container networking works
3. Unchanged `docker-compose.yml` can start the AGRIFLOW `db` service
4. The existing compose healthcheck reaches **healthy**

Do **not** modify AGRIFLOW application architecture, compose, Dockerfile, `.env`, or migrations.

---

## 2. Initial Podman environment

| Item | Value |
|---|---|
| Podman client | **6.0.2** (`windows/amd64`) |
| Podman server | **6.0.2** (`linux/amd64`) |
| Machine | `podman-machine-default` (WSL), **running** |
| Rootful | **true** (`Rootless=false`) |
| User-mode networking | **false** |
| Network backend | **netavark** 2.0.0 |
| DNS | **aardvark-dns** 2.0.0 |
| OCI runtime | **crun** |
| Resources | 8 CPUs / 2 GiB / 100 GiB |
| Initial WSL | **2.6.3.0** |
| Initial guest kernel | **6.6.87.2-microsoft-standard-WSL2** |
| Compose provider | Docker Compose **v5.1.4** via `docker-compose.exe` |

Existing AGRIFLOW artifacts preserved throughout:

- Container `agriflow-ai-db-1` (was `Created`, later started)
- Volume `agriflow-ai_postgres_data`
- Network `agriflow-ai_default`

---

## 3. Initial networking failure

| Command | Result |
|---|---|
| `podman run --rm alpine echo ok` (default bridge) | **FAIL** — `netavark (exit code 1): nftables error: "nft" did not return successfully while applying ruleset:` |
| `podman run --rm --network=host …` | Success |
| `podman run --rm --network=none …` | Success |
| `podman compose up -d db` (prior validation) | Failed at container start with same netavark/nftables error |

With `RUST_LOG` / in-machine debug, the failure occurred while:

```text
Using nftables firewall driver
Creating container chain nv_2f259bab_10_88_0_0_nm16
internal:0:0-0: Error: Could not process rule: No such file or directory
```

---

## 4. Root-cause analysis

| Hypothesis | Finding |
|---|---|
| A. nftables availability | **Not the cause** — `nftables` v1.1.6 installed; simple table add/delete worked |
| B. nftables kernel support | **Partial** — `nf_tables` present, but incomplete FIB support |
| C. missing kernel modules / config | **Yes (primary)** — `# CONFIG_NFT_FIB_IPV6 is not set` on kernel 6.6.87.2; `nft_fib_inet` module missing |
| D. incompatible firewall backend | **Contributing** — netavark defaulted to **nftables**, which requires FIB rules |
| E. Podman Machine config | Default `firewall_driver` unset → netavark selected nftables |
| F. WSL2 networking / kernel | **Yes (root)** — Microsoft WSL kernel historically omitted `CONFIG_NFT_FIB_IPV6` / related FIB options needed by netavark’s host-port rules |
| G. netavark configuration | Defaults correct for modern Podman; broken only on incomplete WSL kernels |
| H. other | Confirmed reproducible with explicit rule: `fib daddr type local` → `No such file or directory` |

**Actual failing operation:** netavark nftables ruleset applying **`fib daddr type local`** (inet family FIB lookup) while creating container/host-port chains. Empty error text after the colon in the outer Podman message hid this; in-machine debug and a direct `nft` repro showed the FIB rule ENOENT.

This matches known upstream reports:

- [containers/podman#25201](https://github.com/containers/podman/issues/25201)
- [microsoft/WSL#13479](https://github.com/microsoft/WSL/issues/13479)

Microsoft fixed FIB support in newer WSL kernels (noted around WSL **2.7.5** / `linux-msft-wsl-6.18.20.1`). This host was on WSL **2.6.3**.

---

## 5. Podman Machine diagnostics

| Check | Result |
|---|---|
| Interfaces | `eth0` up; `podman0` / `podman1` present (down until use) |
| IP forward | `net.ipv4.ip_forward=1` |
| `iptables` initially | **Not installed** |
| `firewall_driver` initially | Unset (default → nftables) |
| Host config mount (Podman 6) | `/etc/containers` ← `C:\Users\skn33\AppData\Roaming\containers` (9p) |
| Pre-existing drop-in | `containers.conf.d/99-podman-machine-provider.conf` → `[machine] provider="wsl"` |

---

## 6. nftables / netavark findings

**Before fix (kernel 6.6.87.2):**

```text
CONFIG_NFT_FIB=m
CONFIG_NFT_FIB_IPV4=m
# CONFIG_NFT_FIB_IPV6 is not set
```

```text
sudo nft add rule inet fibtest PREROUTING fib daddr type local counter accept
→ Error: Could not process rule: No such file or directory
   fib daddr type local
```

**Netavark 2.0.0 constraint:** iptables firewall driver **removed** (`Must provide a valid firewall backend, got iptables`). Documented/valid backends observed: **nftables**, **firewalld** (and containers.conf still mentions **none**). Therefore the older WSL workaround `firewall_driver="iptables"` is **not viable** on Podman 6 / netavark 2.0.

---

## 7. Configuration before change

| Location | State |
|---|---|
| `...\AppData\Roaming\containers\containers.conf.d\` | Only `99-podman-machine-provider.conf` (`provider="wsl"`) |
| `firewall_driver` | **Unset** (implicit **nftables**) |
| Guest packages | netavark, aardvark-dns, nftables present; **no** iptables |
| WSL | 2.6.3.0 / kernel 6.6.87.2 |

**Backup taken before any runtime config experiment:**

`C:\Users\skn33\AppData\Roaming\containers\backup-before-iptables-firewall-20260816-140122\`

(Contains copy of original `containers.conf.d` contents.)

---

## 8. Exact runtime change applied

### Attempted (then reverted) — not the final fix

| Change | Classification | Outcome |
|---|---|---|
| Drop-in `98-netavark-firewall-iptables.conf` with `firewall_driver = "iptables"` | PODMAN MACHINE CHANGE | **Failed** on netavark 2.0: invalid backend |
| `sudo dnf install -y iptables-nft` inside machine | PODMAN MACHINE CHANGE | Package installed (left installed; harmless) |
| Drop-in **removed**; conf.d restored to original provider-only file | PODMAN MACHINE CHANGE | Reverted |

### Final successful fix

| Change | Classification | Detail |
|---|---|---|
| `wsl --update` | **PODMAN MACHINE / WSL HOST CHANGE** (not AGRIFLOW repo) | Updated WSL **2.6.3.0 → 2.7.11.0** |
| Guest kernel after restart | (via WSL update) | **6.6.87.2 → 6.18.33.2-microsoft-standard-WSL2** |
| `podman machine stop` / `start` (+ `wsl -t podman-machine-default` once) | PODMAN MACHINE CHANGE | Load new kernel; restore API pipe |
| `firewall_driver` | Unchanged from original | Remains **default nftables** |

**No AGRIFLOW repository configuration changes.**

---

## 9. Why the change was selected

Priority order followed:

1. Prefer fixing the environment so **default nftables** works (supported path for netavark 2.0)
2. Avoid `firewall_driver = "none"` (disables firewall rule management; not needed once FIB exists)
3. Avoid machine recreate / WSL reset
4. Reject permanent `iptables` driver after proving netavark 2.0 rejects it

`wsl --update` is the least invasive **supported** fix that restores the missing kernel FIB options Microsoft documented for this exact netavark failure.

---

## 10. Security / networking implications

| Aspect | Assessment |
|---|---|
| Final firewall driver | **nftables** (default) — full netavark host-port DNAT / NAT / isolation rules restored |
| `iptables-nft` package | Present but **not** selected as firewall driver; no functional change to netavark path |
| WSL update | Standard Microsoft update; brings current WSL user-mode components + newer kernel |
| Attack surface vs `firewall_driver=none` | Preferable — firewall rules are applied normally |
| AGRIFLOW app security model | Unchanged |

---

## 11. Bridge networking test

```text
podman run --rm alpine echo ok
→ ok
exit 0
```

Repeated after machine restart: `bridge-still-ok` (exit 0).

**Success criterion met** (default bridge, not host/none).

---

## 12. Container-to-container networking test

Temporary artifacts only (`agriflow-nettest*`):

| Step | Result |
|---|---|
| `podman network create agriflow-nettest` | Success |
| Two alpine containers on that network | Started |
| DNS: `getent hosts agriflow-nettest-a` from peer | `10.89.1.2` resolved |
| ICMP: `ping -c 2 agriflow-nettest-a` | 0% loss |
| Cleanup (`podman rm -f`, `podman network rm`) | Completed |

AGRIFLOW volume/network/db container **not** removed by this test cleanup.

---

## 13. AGRIFLOW database container test

| Step | Result |
|---|---|
| `podman compose config` | **Success** (exit 0), using unchanged `docker-compose.yml` |
| `podman compose up -d db` | **Success** — `agriflow-ai-db-1` **Started** |
| Container state | `Created` → **`running`** |
| Image | `timescale/timescaledb:2.28.1-pg17` |
| Sidecar `pg_isready -h db -p 5432` on `agriflow-ai_default` | **accepting connections** |

Migrations **not** run. Backend **not** started. `backend/.env` **not** modified.

---

## 14. Database healthcheck result

| Check | Result |
|---|---|
| Compose healthcheck definition | Unchanged (`pg_isready`) |
| `podman inspect … State.Health.Status` | **`healthy`** (`FailingStreak=0`) |
| Health log sample | `/var/run/postgresql:5432 - accepting connections` (exit 0) |
| `podman ps` STATUS | `Up … (healthy)` |

**Success criterion met.**

---

## 15. Repository files verified unchanged

| Path | Status |
|---|---|
| `docker-compose.yml` | Unchanged (no git diff) |
| `backend/Dockerfile` | Unchanged |
| `backend/.env` | Unchanged (gitignored; not edited by this task) |
| Application code | Unchanged |
| Alembic migrations / Phase 12 | Unchanged |
| Only new repo file from this task | `docs/architecture/PODMAN_NETWORKING_REPAIR_REPORT.md` |

`git status` showed untracked `docs/architecture/` (reports) and an unrelated untracked `backend/.env_backup` (not created by this repair). No tracked file modifications.

---

## 16. Remaining issues

1. **Windows host TCP `localhost:25432`** did not accept connections during this session (`Test-NetConnection` false; no host listener observed), even though the container publishes `0.0.0.0:25432->5432` and is healthy. In-network access to `db:5432` works. This may affect **host-side** tools (e.g. pgAdmin on Windows) and should be diagnosed in the next validation task — it is **separate** from the bridge/nftables root cause fixed here.
2. **`backend/.env` still has `POSTGRES_PORT=25432`** (known from prior runtime validation). Must be corrected before Alembic/backend in Compose. **Out of scope** for this infrastructure task.
3. **`iptables-nft` remains installed** in the machine from the rejected workaround; optional cleanup later; not required for operation.
4. Occasional first-start warning about Docker API pipe missing was cleared by a subsequent `podman machine start`.

---

## 17. Next recommended action

Proceed with the planned follow-up (still using the **same** canonical `docker-compose.yml`):

1. Correct internal DB port in `backend/.env` to **`POSTGRES_PORT=5432`** (host publish mapping stays `25432:5432`)
2. Investigate Windows host publish of `25432` if pgAdmin/host clients are required
3. Start backend, run Alembic, validate FastAPI — **do not** introduce a Podman-specific compose file

---

## Success criteria checklist

| # | Criterion | Result |
|---|---|---|
| 1 | Podman Machine running | **PASS** |
| 2 | Normal Podman bridge networking works | **PASS** |
| 3 | `podman run --rm alpine echo ok` succeeds | **PASS** |
| 4 | Container networking/DNS test succeeds | **PASS** |
| 5 | Existing `docker-compose.yml` validates unchanged | **PASS** |
| 6 | `podman compose up -d db` starts TimescaleDB | **PASS** |
| 7 | Database healthcheck reaches healthy | **PASS** |

---

## Change classification summary

| Change | Type |
|---|---|
| WSL update 2.6.3 → 2.7.11 (kernel 6.18.33.2) | **PODMAN MACHINE / WSL HOST CHANGE** |
| Podman machine stop/start | **PODMAN MACHINE CHANGE** |
| Temporary iptables firewall drop-in (reverted) | **PODMAN MACHINE CHANGE** (reverted) |
| `iptables-nft` package install | **PODMAN MACHINE CHANGE** (retained, unused by netavark) |
| AGRIFLOW compose / app / env / migrations | **NO AGRIFLOW REPOSITORY CHANGE** |
| This report | Documentation only |

**Final recommendation:** Keep default **nftables** on the updated WSL kernel. Do **not** set `firewall_driver=none`. Do **not** add a Podman-specific compose file for this issue.
