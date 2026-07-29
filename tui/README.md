# Audit Tools — Interactive TUI

A terminal UI that walks you through running an audit. It presents a platform
menu, collects connection details and check selection, then runs the existing
collectors with live progress.

GitHub and GitLab are supported. Adding a platform is a matter of writing a
runner and a `Platform` descriptor in `tui/platforms.py` — the screens are
platform-agnostic.

## Run it

```bash
pip install -r requirements.txt
python audit_tui.py
```

The connection fields are pre-filled from environment variables if set:

```bash
# GitHub
export GITHUB_ORG=my-org
export GITHUB_TOKEN=ghp_...     # needs read:org and repo scopes

# GitLab
export GITLAB_GROUP=my-group
export GITLAB_TOKEN=glpat-...   # needs read_api scope
export GITLAB_URL=https://gitlab.example.com/api/v4   # self-hosted only
```

## Walkthrough

1. **Platform** — choose GitHub or GitLab.
2. **Connection** — the audit subject (org / group), a masked token, and any
   platform-specific fields (branch for GitHub; API base URL for GitLab).
3. **Checks** — toggle which checks to run. Plan-restricted checks (GitHub's
   Enterprise audit log; GitLab's Premium and self-hosted checks) are off by
   default.
4. **Run** — a progress bar and live log show each check completing with its row
   count. Errors on a single check are reported without stopping the run.

## Output

The TUI writes the same package the platform's `audit.py` produces:
`<output>/github_audit_<org>_<date>/` or `<output>/gitlab_audit_<group>_<date>/`,
one CSV per check plus a `summary.txt`. It reuses each platform's collectors and
CSV reporter unchanged — the TUI is only an interactive driver around them.

## Keys

- `Esc` — back / return to menu
- `Ctrl+P` — command palette
- `q` — quit (from the menu)

## Tests

```bash
python -m pytest tui/tests
```

The tests stub the network-bound collectors, so they run offline: one suite
covers the run orchestration, another drives the app headlessly through every
screen.
