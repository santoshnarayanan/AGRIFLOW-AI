# Git hooks (optional)

To automatically strip AI co-author lines from commit messages:

```bash
git config core.hooksPath .githooks
```

On Windows (Git Bash or PowerShell from repo root), the same command applies.

The `.githooks/commit-msg` hook removes Cursor/Claude `Co-authored-by` trailers before a commit is created.
