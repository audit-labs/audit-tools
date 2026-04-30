#!/usr/bin/env python3
import requests
from common import build_parser, init_run, write_artifacts, write_meta

def main():
    p=build_parser('Collect GitLab merge request approval rules')
    p.add_argument('--project-id',required=True); p.add_argument('--timeout',type=int,default=30)
    a=p.parse_args(); run,run_id=init_run(a,'gitlab_approvals')
    if a.dry_run: print('Dry run complete'); return 0
    r=requests.get(f"{a.base_url}/projects/{a.project_id}/approval_rules",headers={'PRIVATE-TOKEN':a.private_token},timeout=a.timeout)
    if r.status_code!=200:
      err=f"Failed to fetch approval rules: {r.status_code}"; (run['exceptions']/ 'request_error.txt').write_text(err); write_meta(run,'gitlab_approvals',run_id,a,errors=[err]); return 1
    rules=r.json(); write_artifacts(run,'approval_rules',rules); write_meta(run,'gitlab_approvals',run_id,a,counts={'rules':len(rules)})
    if not a.quiet:
      for rule in rules: print(f"Rule: {rule.get('name')} approvals_required={rule.get('approvals_required')}")
    return 0
if __name__=='__main__': raise SystemExit(main())
