> **NOTE**: Authentication uses the standard AWS credential chain (environment
> variables, shared config/credentials, SSO profiles, instance roles). This tool
> never handles access keys directly. Read-only permissions are enough — IAM
> `Get*`/`List*`, S3 `s3:GetBucket*` + `s3:ListAllMyBuckets`, EC2
> `ec2:DescribeRegions`/`DescribeSecurityGroups`, `cloudtrail:DescribeTrails` +
> `GetTrailStatus`, `config:DescribeConfigurationRecorders*`, and for the SSO
> check `sso:List*`/`sso:Describe*`, `identitystore:Describe*`, and
> `organizations:ListAccounts`. The SecurityAudit managed policy covers these.

---

# `audit.py` — Unified AWS Audit Tool

Runs all collectors against the account reachable with your active AWS
credentials and writes a timestamped audit package to disk. This is the tool the
interactive TUI (`audit_tui.py`) drives.

## Setup

```bash
export AWS_PROFILE=my-profile          # optional; else the default chain
export AWS_DEFAULT_REGION=us-east-1    # optional
export AWS_AUDIT_ACCOUNT=my-account    # optional; only for the SSO check
```

If you authenticate with `aws login` / IAM Identity Center (SSO), those
credentials use the AWS Common Runtime provider, which needs the `crt` extra.
It is included via `botocore[crt]` in the `aws` extra (`pip install ".[aws]"`);
if you installed boto3 separately, run `pip install "botocore[crt]"`. Without it you'll see
`MissingDependencyException: ... requires an additional dependency`.

## Usage

```bash
# Basic run — uses the active credentials / default profile
python audit.py

# Named profile and region, custom output directory
python audit.py --profile my-profile --region us-east-1 --out ./output

# SSO assignments for a specific account in the organization
python audit.py --account my-account
```

## Output

Creates a directory: `<out>/aws_audit_<profile>_<YYYY-MM-DD>/`

| File | Contents |
|---|---|
| `iam_users.csv` | IAM users with MFA status, access-key count/age, console password, last use |
| `password_policy.csv` | Account IAM password policy (length, complexity, rotation, reuse) |
| `account_security.csv` | Account summary — root MFA, root access keys, and resource counts |
| `s3_public_access.csv` | Per-bucket Public Access Block, policy public status, and ACL public exposure |
| `open_security_groups.csv` | Security-group ingress rules open to `0.0.0.0/0` or `::/0`, across all regions |
| `cloudtrail.csv` | CloudTrail trails — logging status, multi-region, log-file validation |
| `config_recorders.csv` | AWS Config recording status per region (gaps are flagged) |
| `sso_assignments.csv` | IAM Identity Center permission-set assignments per account (Identity Center + Organizations) |
| `summary.txt` | Row counts per section |

`open_security_groups.csv` and `config_recorders.csv` scan every enabled region,
so they take longer on accounts with many regions.

Checks that aren't available (no password policy, no Identity Center instance,
missing permissions) are skipped with a warning; the rest still run.

The shell scripts below remain for CloudShell or CLI-only environments where
Python and boto3 aren't set up.

---

# `aws_iam_users.sh`

*Note*: This example uses an account titled `cmc`, which has access provisioned to it through IAM.

``` bash
chmod +x aws_iam_users.sh
./aws_iam_users.sh
```

``` text
Fetching IAM Identity Center and Account details...
Successfully found Account 'cmc' with ID: 214941490075
---
Step 2: Finding all permission sets provisioned to 'cmc'...
Found provisioned permission sets. Now checking assignments for each...
---
  -> Fetching policies for Permission Set: arn:aws:sso:::permissionSet/ssoins-68041bff81588aa3/ps-6ea9be6a2332b891
  -> Found Assignment: testgroup1 (GROUP) -> AdministratorAccess
  -> Found Assignment: iamtestuser1 (USER) -> AdministratorAccess
  -> Found Assignment: testgroup2 (GROUP) -> AdministratorAccess
  -> Fetching policies for Permission Set: arn:aws:sso:::permissionSet/ssoins-68041bff81588aa3/ps-590510f2a285016d
  -> Found Assignment: iamtestuser1 (USER) -> Billing
---
Success! Report saved to 'report_cmc.json'
The file contains all user/group assignments and their policies for account 'cmc'.
```

``` bash
cat report_cmc.json
```

```json
[
  {
    "principal": {
      "type": "GROUP",
      "name": "testgroup1"
    },
    "permission_set": {
      "name": "AdministratorAccess",
      "policies": {
        "managed_policies": [
          "arn:aws:iam::aws:policy/AdministratorAccess"
        ],
        "inline_policy": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"Statement2\",\"Effect\":\"Deny\",\"Action\":[\"a4b:*\"],\"Resource\":[\"*\"]}]}"
      }
    }
  },
  {
    "principal": {
      "type": "USER",
      "name": "iamtestuser1"
    },
    "permission_set": {
      "name": "AdministratorAccess",
      "policies": {
        "managed_policies": [
          "arn:aws:iam::aws:policy/AdministratorAccess"
        ],
        "inline_policy": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"Statement2\",\"Effect\":\"Deny\",\"Action\":[\"a4b:*\"],\"Resource\":[\"*\"]}]}"
      }
    }
  },
  {
    "principal": {
      "type": "GROUP",
      "name": "testgroup2"
    },
    "permission_set": {
      "name": "AdministratorAccess",
      "policies": {
        "managed_policies": [
          "arn:aws:iam::aws:policy/AdministratorAccess"
        ],
        "inline_policy": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"Statement2\",\"Effect\":\"Deny\",\"Action\":[\"a4b:*\"],\"Resource\":[\"*\"]}]}"
      }
    }
  },
  {
    "principal": {
      "type": "USER",
      "name": "iamtestuser1"
    },
    "permission_set": {
      "name": "Billing",
      "policies": {
        "managed_policies": [
          "arn:aws:iam::aws:policy/job-function/Billing"
        ],
        "inline_policy": ""
      }
    }
  }
]
```

# `aws_password_policy`

To test a password policy against AWS, I have created two steps:

**Step 1: Gather AWS Policy**

Run the script on your CloudShell or using the `aws` command

``` bash
chmod +x gather_policy.sh
./gather_policy.sh
```

This will produce a JSON file as the output, with both metadata and the password policy/

``` json
{
  "metadata": {
    "report_timestamp_utc": "2025-12-15T01:29:52Z",
    "os_user": "cloudshell-user",
    "hostname": "",
    "working_directory": "/home/cloudshell-user",
    "aws_profile": "default",
    "aws_region": "eu-west-1",
    "aws_caller_identity": {
      "UserId": "214941490075",
      "Account": "214941490075",
      "Arn": "arn:aws:iam::214941490075:root"
    }
  },
  "PasswordPolicy": {
    "MinimumPasswordLength": 8,
    "RequireSymbols": true,
    "RequireNumbers": true,
    "RequireUppercaseCharacters": true,
    "RequireLowercaseCharacters": true,
    "AllowUsersToChangePassword": true,
    "ExpirePasswords": true,
    "MaxPasswordAge": 90,
    "PasswordReusePrevention": 4,
    "HardExpiry": false
  }
}
```

**Step 2: Test AWS**

Use this file as the input to the `evaluate_policy.py` script. This Python script will ask you what you expect the values to be (e.g., what are the requirements in the company's policy?).

``` bash
uv run evaluate_policy.py policy_report.json
```

This will ask you for inputs dynamically (all are optional) and will return both a table of results in the shell, as well as a CSV file for further testing and/or documentation.

*Shell Output:*

``` text
=== Expected / Minimum Values (press <Enter> for N/A) ===

Enter expected value for 'Minimum password length' (int) or press <Enter> to skip: 8
Enter expected value for 'Require symbols (!@#$…)' (bool) or press <Enter> to skip: true
Enter expected value for 'Require numbers (0‑9)' (bool) or press <Enter> to skip: true
Enter expected value for 'Require uppercase letters (A‑Z)' (bool) or press <Enter> to skip: true
Enter expected value for 'Require lowercase letters (a‑z)' (bool) or press <Enter> to skip: true
Enter expected value for 'Allow users to change password' (bool) or press <Enter> to skip: true
Enter expected value for 'Expire passwords (enable aging)' (bool) or press <Enter> to skip: true
Enter expected value for 'Maximum password age (days)' (int) or press <Enter> to skip: 90
Enter expected value for 'Prevent password reuse (last N)' (int) or press <Enter> to skip: 4
Enter expected value for 'Hard expiry (no grace period)' (bool) or press <Enter> to skip: false

Audit CSV written to: policy_audit_20251215T014323Z.csv

Summary:
   1. Minimum password length             → PASS
   2. Require symbols (!@#$…)             → PASS
   3. Require numbers (0‑9)               → PASS
   4. Require uppercase letters (A‑Z)     → PASS
   5. Require lowercase letters (a‑z)     → PASS
   6. Allow users to change password      → PASS
   7. Expire passwords (enable aging)     → PASS
   8. Maximum password age (days)         → PASS
   9. Prevent password reuse (last N)     → PASS
  10. Hard expiry (no grace period)       → PASS

--- End of report ---
```

*CSV Output:*

``` csv
# report_timestamp_utc: 2025-12-15T01:29:52Z
# os_user: cloudshell-user
# hostname:
# working_directory: /home/cloudshell-user
# aws_profile: default
# aws_region: eu-west-1
"# aws_caller_identity: {'UserId': '214941490075', 'Account': '214941490075', 'Arn': 'arn:aws:iam::214941490075:root'}"

Rule#,Policy‑Item,Expected,Actual,Result
1,Minimum password length,8,8,PASS
2,Require symbols (!@#$…),true,true,PASS
3,Require numbers (0‑9),true,true,PASS
4,Require uppercase letters (A‑Z),true,true,PASS
5,Require lowercase letters (a‑z),true,true,PASS
6,Allow users to change password,true,true,PASS
7,Expire passwords (enable aging),true,true,PASS
8,Maximum password age (days),90,90,PASS
9,Prevent password reuse (last N),4,4,PASS
10,Hard expiry (no grace period),false,false,PASS
```

# `aws_s3_buckets.sh`

This script requires one non-interactive step. Simply run the script:

``` bash
chmod +x aws_s3_buckets.sh
./aws_s3_buckets.sh
```

The shell will show you each bucket discovered during the scanning process, as well as the final result. This final result is a combination of the bucket's Public Access Block (PAB), Policy Status (IsPublic), and ACLs (AllUsers Group).

``` text
Starting FULL S3 Public Access Audit for the CURRENT account...
---
1. Retrieving all bucket names...
Processing bucket: 13bf5920-a09f-47bc-a75a-394a09f18d6a
  Region determined: eu-west-1
  Final Status: FALSE
Processing bucket: c67fa6bd-2fd5-4bc5-825d-587fb535bf2e
  Region determined: eu-west-1
  Final Status: FALSE
---
✅ Audit Complete.
Final report saved to **s3_full_public_access_audit.csv**
BucketName,Region,PAB_FullyRestricted,Policy_IsPublic,ACL_AllUsersRead,ACL_AllUsersWrite,OverallPublicStatus
13bf5920-a09f-47bc-a75a-394a09f18d6a,eu-west-1,FALSE-VULNERABLE,No Policy,FALSE,FALSE,"FALSE"
c67fa6bd-2fd5-4bc5-825d-587fb535bf2e,eu-west-1,TRUE,No Policy,FALSE,FALSE,"FALSE"
```

It will also save the results shown above to the `s3_full_public_access_audit.csv` file:

``` csv
BucketName,Region,PAB_FullyRestricted,Policy_IsPublic,ACL_AllUsersRead,ACL_AllUsersWrite,OverallPublicStatus
13bf5920-a09f-47bc-a75a-394a09f18d6a,eu-west-1,FALSE-VULNERABLE,No Policy,FALSE,FALSE,"FALSE"
c67fa6bd-2fd5-4bc5-825d-587fb535bf2e,eu-west-1,TRUE,No Policy,FALSE,FALSE,"FALSE"
```