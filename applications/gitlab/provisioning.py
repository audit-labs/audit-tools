#!/usr/bin/env python3
import requests
from common import build_parser, init_run, write_artifacts, write_meta

def main():
    p=build_parser('Collect GitLab group provisioning audit events')
    p.add_argument('--group-id',required=True); p.add_argument('--timeout',type=int,default=30)
    a=p.parse_args(); run,run_id=init_run(a,'gitlab_provisioning')
    if a.dry_run: print('Dry run complete'); return 0
    r=requests.get(f"{a.base_url}/groups/{a.group_id}/audit_events",headers={'PRIVATE-TOKEN':a.private_token},timeout=a.timeout)
    if r.status_code!=200: (run['exceptions']/ 'request_error.txt').write_text(str(r.status_code)); write_meta(run,'gitlab_provisioning',run_id,a,errors=[f'status {r.status_code}']); return 1
    events=[e for e in r.json() if e.get('event_name') in ['member_created','member_destroyed','member_updated']]
    write_artifacts(run,'provisioning_events',events); write_meta(run,'gitlab_provisioning',run_id,a,counts={'events':len(events)})
    if not a.quiet:
      for e in events: print(e.get('created_at'),e.get('event_name'))
    return 0
if __name__=='__main__': raise SystemExit(main())
