# databases/snowflake

> Planned SQL scripts for Snowflake security audits. Mirrors the style of `databases/postgres/`
> and `databases/mysql/`. All queries target `SNOWFLAKE.ACCOUNT_USAGE` views, which require
> the ACCOUNTADMIN role or a role granted the SNOWFLAKE database privilege.

## Planned Scripts

### `admins.sql`
List users and roles holding `ACCOUNTADMIN`, `SECURITYADMIN`, or `SYSADMIN` via
`SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES` and `GRANTS_TO_USERS`.

### `passwords.sql`
Read account-level password policy parameters from `SNOWFLAKE.ACCOUNT_USAGE.ACCOUNT_PARAMETERS`
(min length, max age, lockout attempts, MFA enforcement).

### `users.sql`
List all users from `SNOWFLAKE.ACCOUNT_USAGE.USERS` with `last_success_login`, `disabled`,
`must_change_password`, and `has_password` flags.

### `network_policies.sql`
List all network policies and their assignments. Flag users with no network policy attached.

### `stale_users.sql`
Filter `SNOWFLAKE.ACCOUNT_USAGE.USERS` for accounts inactive for 90+ days or that have
never logged in.

### `service_accounts.sql`
Identify likely service accounts: no email set and `has_rsa_public_key = TRUE`.
Join against role grants to show what access each holds.
