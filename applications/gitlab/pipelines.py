#!/usr/bin/env python3
import requests
from common import build_parser, init_run, write_artifacts, write_meta

def main():
    p=build_parser('Collect GitLab pipeline summaries')
    p.add_argument('--project-id',required=True); p.add_argument('--timeout',type=int,default=30)
    a=p.parse_args(); run,run_id=init_run(a,'gitlab_pipelines')
    if a.dry_run: print('Dry run complete'); return 0
    page=1; per_page=100; rows=[]
    while True:
      r=requests.get(f"{a.base_url}/projects/{a.project_id}/pipelines",headers={'PRIVATE-TOKEN':a.private_token},params={'page':page,'per_page':per_page},timeout=a.timeout)
      if r.status_code!=200: (run['exceptions']/ 'request_error.txt').write_text(str(r.status_code)); write_meta(run,'gitlab_pipelines',run_id,a,errors=[f'status {r.status_code}']); return 1
      batch=r.json()
      if not batch: break
      rows.extend(batch); page+=1
    write_artifacts(run,'pipelines',rows); write_meta(run,'gitlab_pipelines',run_id,a,counts={'pipelines':len(rows)})
    if not a.quiet: print(f'Pipelines: {len(rows)}')
    return 0
if __name__=='__main__': raise SystemExit(main())
