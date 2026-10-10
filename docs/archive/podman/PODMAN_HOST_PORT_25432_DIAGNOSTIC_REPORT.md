# AGRIFLOW-AI — Podman Windows Host Port 25432 Diagnostic Report

| Field | Value |
|---|---|
| **Document type** | Diagnostic only (no fixes applied) |
| **Date** | 2026-08-16 |
| **Target** | Why `localhost:25432` fails on Windows while `db:5432` works in Podman |
| **Repository changes** | **This report only** |

---

## Executive summary

**Diagnosis:** Published port `25432` is correctly configured and PostgreSQL is healthy. Port forwarding works **inside the Podman WSL VM** and from **Windows to the VM’s eth0 IP**, but **not** from Windows to `127.0.0.1` / `localhost`.

**Root cause:** Podman 6.0.2 with **`UserModeNetworking=false`** publishes ports via **netavark nftables DNAT inside the Linux VM** (no TCP `LISTEN` socket on port 25432). Default WSL2 **does not forward Windows loopback** (`127.0.0.1`) to that in-VM DNAT path. Traffic to the **WSL VM IP** (`192.168.54.63`) reaches the VM network stack and is DNAT’d to the container.

**Classification:** **Podman + WSL2 + Windows host forwarding** — not AGRIFLOW, PostgreSQL, or Compose.

**Smallest safe fix (recommended, not implemented here):** Connect from Windows using the **Podman Machine WSL IP** (currently `192.168.54.63:25432`), or enable **WSL mirrored networking** so Windows `localhost` reaches published Podman ports consistently.

---

## 1. Current Podman container mapping

Commands: `podman ps`, `podman port agriflow-ai-db-1`, `podman inspect agriflow-ai-db-1`

| Field | Value |
|---|---|
| Container | `agriflow-ai-db-1` |
| Status | **running (healthy)** |
| Image | `timescale/timescaledb:2.28.1-pg17` |
| Container port | **5432/tcp** |
| Published mapping | **`0.0.0.0:25432 → 5432/tcp`** |
| Network mode | `bridge` (`agriflow-ai_default`) |
| Container IP | **10.89.0.2** |
| Gateway | **10.89.0.1** (`podman1`) |
| Port bindings JSON | `{"5432/tcp":[{"HostIp":"0.0.0.0","HostPort":"25432"}]}` |

`podman port` output:

```text
5432/tcp -> 0.0.0.0:25432
```

Compose mapping is correctly reflected in Podman metadata. **No mapping error.**

---

## 2. PostgreSQL listening state

Commands: `podman exec agriflow-ai-db-1 pg_isready …`, `ss -lntp` inside container

| Check | Result |
|---|---|
| `pg_isready -U agriflow -d agriflow` | **`/var/run/postgresql:5432 - accepting connections`** |
| Listen addresses | **`0.0.0.0:5432`** and **`:::5432`** |

PostgreSQL is listening on the expected container port. **Not a PostgreSQL configuration issue.**

In-network check (prior repair validation, reconfirmed pattern):

```text
pg_isready -h db -p 5432  → accepting connections
```

---

## 3. Podman Machine networking state

### Machine configuration

| Item | Value |
|---|---|
| Machine | `podman-machine-default` (WSL2), **running** |
| Podman | **6.0.2** (rootful) |
| WSL | **2.7.11.0** |
| Guest kernel | **6.18.33.2-microsoft-standard-WSL2** |
| Network backend | **netavark** |
| **UserModeNetworking** | **`false`** (from `podman machine inspect` and machine JSON `WSLHypervisor.UserModeNetworking`) |
| Guest eth0 IP | **192.168.54.63/20** (dynamic WSL NAT address) |

### How port 25432 is implemented

Inside the Podman Machine:

| Observation | Detail |
|---|---|
| `ss -lntp \| grep 25432` | **No LISTEN socket** on 25432 |
| Forwarding mechanism | **nftables DNAT** (netavark `NETAVARK-HOSTPORT-DNAT`) |

Relevant rules:

```text
chain NETAVARK-HOSTPORT-DNAT {
    tcp dport 25432 jump nv_ee33ae73_10_89_0_0_nm24_dnat
}
chain nv_ee33ae73_10_89_0_0_nm24_dnat {
    tcp dport 25432 dnat ip to 10.89.0.2:5432
}
```

### Connectivity from **inside** the Podman Machine

| Target | Result |
|---|---|
| `127.0.0.1:25432` | **OPEN** (DNAT → container) |
| `192.168.54.63:25432` | **OPEN** |
| `10.89.0.2:25432` | **FAIL** (container IP, not host publish path) |
| `10.89.0.2:5432` | **OPEN** (direct to PostgreSQL) |

**Conclusion:** In-VM port publishing works. There is **no gvproxy/rootlessport** process binding 25432 on Windows; forwarding is **entirely inside the Linux VM**.

---

## 4. Windows host networking state

Commands: `Get-NetTCPConnection`, `netstat`, `Test-NetConnection`

### Listeners on Windows

| Check | Result |
|---|---|
| `Get-NetTCPConnection -LocalPort 25432` | **No connections** (count 0) |
| `netstat -ano \| findstr :25432` | **No output** |

**Category A:** **No Windows listener** on 25432. Expected for this Podman mode — Windows is not binding the port.

### `Test-NetConnection` from Windows

| Target | TcpTestSucceeded |
|---|---|
| `127.0.0.1:25432` | **False** |
| `localhost:25432` (resolved to `::1`) | **False** |
| `::1:25432` | **False** |
| **`192.168.54.63:25432`** (WSL eth0) | **True** |

**Category D / Windows host forwarding:** Windows loopback is **not** bridged to the Podman VM’s nftables DNAT for published ports. The **WSL VM IP path works**.

This is **not** category B (listener blocked) — there is no listener. Firewall is **not** blocking the working path (machine IP succeeds).

### WSL configuration

| File | Present |
|---|---|
| `%USERPROFILE%\.wslconfig` | **No** |
| `%WINDIR%\System32\.wslconfig` | **No** |

Default WSL NAT mode (not mirrored). No explicit `localhostForwarding` configuration.

---

## 5. Docker / Rancher port conflict check

| Runtime | State | Port 25432 |
|---|---|---|
| Docker Desktop WSL | **Stopped** | Not bound |
| Rancher Desktop WSL | **Stopped** | Not bound |
| Podman Machine WSL | **Running** | Published via netavark (in VM) |
| `docker ps` | Fails (daemon not running) | N/A |

**No conflict** from Docker Desktop or Rancher Desktop on port 25432.

---

## 6. Temporary port test result

Temporary container (removed after test):

```text
podman run -d --name agriflow-porttest-25433 -p 25433:80 nginx:alpine
```

| Check | Result |
|---|---|
| Mapping | `80/tcp -> 0.0.0.0:25433` |
| Windows `127.0.0.1:25433` | **False** |
| Windows `192.168.54.63:25433` | **True** |
| Cleanup | `podman rm -f agriflow-porttest-25433` ✓ |

**AGRIFLOW artifacts preserved:** `agriflow-ai-db-1` and `agriflow-ai_postgres_data` untouched.

**Conclusion:** **Podman Windows host-port forwarding to localhost is generally broken** in this configuration — not specific to TimescaleDB or port 25432.

---

## 7. Root cause

### Precise failure chain

```text
Windows client
    → localhost:25432 (127.0.0.1 / ::1)
        → No Windows listener
        → WSL2 default localhost forwarding does NOT deliver traffic
           to Podman VM nftables PREROUTING/DNAT for published ports
        → Test-NetConnection FAIL

Windows client
    → 192.168.54.63:25432 (WSL VM eth0)
        → Packet enters Podman Machine network stack
        → netavark nftables: tcp dport 25432 dnat to 10.89.0.2:5432
        → PostgreSQL accepts connection
        → Test-NetConnection SUCCESS
```

### Contributing factors

| Factor | Role |
|---|---|
| `UserModeNetworking=false` | Ports published **inside VM** via netavark, not bound on Windows by gvproxy |
| nftables DNAT without LISTEN | WSL localhost forwarding typically expects a listening socket or mirrored networking integration |
| No `.wslconfig` mirrored mode | Default NAT does not map Windows `127.0.0.1` → VM published ports |
| Dynamic WSL IP | Machine IP (`192.168.54.63`) may change after reboot |

### Ruled out

| Cause | Evidence |
|---|---|
| Wrong compose mapping | `0.0.0.0:25432→5432` confirmed |
| PostgreSQL not listening | `0.0.0.0:5432` inside container |
| DB unhealthy | Healthcheck **healthy** |
| Bridge networking broken | Container-to-container DNS/ping works |
| Port conflict on 25432 | No other runtime bound |
| Windows firewall blocking VM IP | Machine IP connection succeeds |
| AGRIFLOW-specific bug | Identical failure on temp nginx `:25433` |

---

## 8. Problem classification

| Layer | Responsible? |
|---|---|
| AGRIFLOW application | **No** |
| PostgreSQL / TimescaleDB | **No** |
| `docker-compose.yml` / Compose | **No** (mapping correct) |
| Podman port publish model | **Yes** (in-VM netavark DNAT, no Windows bind) |
| WSL2 | **Yes** (localhost forwarding gap with this publish model) |
| Windows host forwarding | **Yes** (primary symptom surface) |
| Windows firewall | **No** (machine IP works) |
| Docker / Rancher interference | **No** |
| Other | Dynamic WSL IP complicates workarounds |

---

## DIAGNOSIS (summary)

`localhost:25432` on Windows cannot reach `db:5432` because:

1. Podman reports `0.0.0.0:25432→5432` at the **API/metadata** level.
2. The actual datapath is **nftables DNAT inside the Podman WSL VM**, not a Windows or WSL `LISTEN` on 25432.
3. **Windows loopback is not forwarded** to that DNAT path under default WSL NAT + `UserModeNetworking=false`.
4. The same port **does work** from Windows when targeting the **Podman Machine WSL eth0 IP** (`192.168.54.63:25432` at time of test).

---

## RECOMMENDED FIX (minimum safe options — **not applied in this task**)

Priority order (least invasive first):

### Option 1 — Immediate workaround (no host config change)

Use the **Podman Machine WSL IP** instead of `localhost`:

```text
Host: 192.168.54.63   (verify after each machine restart)
Port: 25432
```

- **Pros:** Works now; no Podman/Compose changes.
- **Cons:** IP is **dynamic**; pgAdmin/clients must use current IP; `backend/.env` still needs internal port fix separately for Compose backend (`5432`, not `25432`).

Discover current IP:

```powershell
podman machine ssh "ip -4 -o addr show eth0 | awk '{print \$4}' | cut -d/ -f1"
```

### Option 2 — WSL mirrored networking (host-level, recommended structural fix)

Create `%USERPROFILE%\.wslconfig`:

```ini
[wsl2]
networkingMode=mirrored
localhostForwarding=true
```

Then:

```powershell
wsl --shutdown
podman machine start
```

- **Pros:** Intended to improve Windows ↔ WSL localhost behavior for published ports; aligns with Microsoft/Podman guidance for Windows dev.
- **Cons:** Affects **all WSL distros**; requires shutdown; verify Podman bridge still works after enable (some mirrored-mode + Podman edge cases reported upstream).

**Classification:** **PODMAN MACHINE / WSL HOST CHANGE** — not an AGRIFLOW repo change.

### Option 3 — Podman user-mode networking (larger change)

Recreate or reconfigure Podman Machine with **`--user-mode-networking`** so gvproxy binds ports on the Windows host.

- **Pros:** Can bind published ports on Windows directly.
- **Cons:** **Machine recreate** may be required; out of scope for this diagnostic; user explicitly said to stop rather than auto-recreate.

### Option 4 — Windows port proxy (fragile)

`netsh interface portproxy` from `127.0.0.1:25432` → `<WSL-IP>:25432`.

- **Cons:** Must update when WSL IP changes; maintenance burden.

### Not recommended as primary fix

| Approach | Why |
|---|---|
| Change compose port mapping | Mapping is correct; problem is Windows reachability |
| Change PostgreSQL `listen_addresses` | Already listens on `0.0.0.0:5432` |
| Disable firewall globally | Machine IP path already works; not a firewall block |

---

## Success criterion

| Question | Answer |
|---|---|
| Why does `localhost:25432` fail? | Windows loopback is not forwarded to Podman VM nftables DNAT; no Windows/WSL listener on 25432 |
| Why does `db:5432` work in Podman? | Direct container network — unrelated to host publish path |
| Smallest safe fix? | Use **WSL VM IP:25432** now; enable **WSL mirrored networking** for durable `localhost` behavior |

**Do not proceed to Alembic or backend startup in this task.** Next steps remain: apply host networking fix (if desired), then correct `backend/.env` internal `POSTGRES_PORT=5432` in a separate task.

---

## Appendix — Commands run (non-destructive)

- `podman ps`, `podman port`, `podman inspect`
- `podman exec … pg_isready`, `ss -lntp`
- `podman machine inspect`, `podman machine ssh` (`ss`, `ip`, `nft`, TCP probes)
- `Get-NetTCPConnection`, `netstat`, `Test-NetConnection` (127.0.0.1, localhost, ::1, 192.168.54.63)
- `wsl -l -v`, `wsl --version`
- Temporary `podman run -p 25433:80 nginx:alpine` → tested → removed

No secrets included. No AGRIFLOW repository configuration modified.
