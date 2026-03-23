# os/windows

> Planned PowerShell scripts for Windows security audits. Mirrors the structure of `os/linux/`.
>
> Open architectural decision: scripts can target local accounts only (`Get-LocalUser`),
> Active Directory (`Get-ADUser`), or both. This affects cmdlet choices across most scripts
> below and should be settled before implementation.

## Planned Scripts

### `local_admins.ps1`
List members of the local Administrators group via `Get-LocalGroupMember`.

### `passwords.ps1`
Dump local password policy via `net accounts`. If domain-joined, also pull
`Get-ADDefaultDomainPasswordPolicy` (min length, max age, lockout threshold, history).

### `audit_policy.ps1`
Read the Windows audit policy via `auditpol /get /category:*`. Flag whether logon,
account management, and privilege use events are being logged.

### `rdp_settings.ps1`
Check if RDP is enabled, whether NLA is required, and which users/groups hold
"Allow log on through Remote Desktop Services" rights.

### `inactive_users.ps1`
List local user accounts with last logon date. Flag accounts inactive past a
configurable threshold (e.g., 90 days).

### `ad_admins.ps1`
If domain-joined: list members of Domain Admins, Enterprise Admins, and Schema Admins.
AD equivalent of `../../../applications/github/github_admins.py`.

### `scheduled_tasks.ps1`
List scheduled tasks running as SYSTEM or with stored credentials.
Windows analog of a cron audit.
