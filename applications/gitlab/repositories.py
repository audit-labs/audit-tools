#!/usr/bin/env python3
import requests
from common import build_parser, init_run, write_artifacts, write_meta

def main():
    p=build_parser('Collect GitLab group repositories')
    p.add_argument('--group-id',required=True); p.add_argument('--timeout',type=int,default=30)
    a=p.parse_args(); run,run_id=init_run(a,'gitlab_repositories')
    if a.dry_run: print('Dry run complete'); return 0
    page=1; rows=[]
    while True:
      r=requests.get(f"{a.base_url}/groups/{a.group_id}/projects",headers={'PRIVATE-TOKEN':a.private_token},params={'page':page,'per_page':100},timeout=a.timeout)
      if r.status_code!=200: (run['exceptions']/ 'request_error.txt').write_text(str(r.status_code)); write_meta(run,'gitlab_repositories',run_id,a,errors=[f'status {r.status_code}']); return 1
      batch=r.json()
      if not batch: break
      rows.extend(batch); page+=1
    write_artifacts(run,'repositories',rows); write_meta(run,'gitlab_repositories',run_id,a,counts={'repositories':len(rows)})
    if not a.quiet:
      for p in rows: print(f"{p.get('name')} ({p.get('id')})")
    return 0
if __name__=='__main__': raise SystemExit(main())
