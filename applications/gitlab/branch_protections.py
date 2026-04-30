#!/usr/bin/env python3
import requests
from common import build_parser, init_run, write_artifacts, write_meta

def main():
    p=build_parser('Collect GitLab protected branches')
    p.add_argument('--project-id',required=True); p.add_argument('--timeout',type=int,default=30)
    a=p.parse_args(); run,run_id=init_run(a,'gitlab_branch_protections')
    if a.dry_run: print('Dry run complete'); return 0
    r=requests.get(f"{a.base_url}/projects/{a.project_id}/protected_branches",headers={'PRIVATE-TOKEN':a.private_token},timeout=a.timeout)
    if r.status_code!=200: (run['exceptions']/ 'request_error.txt').write_text(str(r.status_code)); write_meta(run,'gitlab_branch_protections',run_id,a,errors=[f'status {r.status_code}']); return 1
    data=r.json(); write_artifacts(run,'protected_branches',data); write_meta(run,'gitlab_branch_protections',run_id,a,counts={'branches':len(data)})
    if not a.quiet: print(data)
    return 0
if __name__=='__main__': raise SystemExit(main())
