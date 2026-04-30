#!/usr/bin/env python3
import requests
from common import build_parser, init_run, write_artifacts, write_meta

def members(base,token,timeout,kind,id_):
    r=requests.get(f"{base}/{kind}/{id_}/members",headers={'PRIVATE-TOKEN':token},timeout=timeout)
    return r.status_code,r.json() if r.status_code==200 else []

def main():
    p=build_parser('Collect GitLab group/project members')
    p.add_argument('--group-ids',nargs='*',default=[]); p.add_argument('--project-ids',nargs='*',default=[]); p.add_argument('--timeout',type=int,default=30)
    a=p.parse_args(); run,run_id=init_run(a,'gitlab_users')
    if a.dry_run: print('Dry run complete'); return 0
    out=[]; errors=[]
    for gid in a.group_ids:
      code,data=members(a.base_url,a.private_token,a.timeout,'groups',gid)
      (out.append({'scope':'group','id':gid,'members':data}) if code==200 else errors.append(f'group {gid} status {code}'))
    for pid in a.project_ids:
      code,data=members(a.base_url,a.private_token,a.timeout,'projects',pid)
      (out.append({'scope':'project','id':pid,'members':data}) if code==200 else errors.append(f'project {pid} status {code}'))
    write_artifacts(run,'members',out); write_meta(run,'gitlab_users',run_id,a,counts={'scopes':len(out),'members':sum(len(i['members']) for i in out)},errors=errors)
    if not a.quiet:
      for item in out: print(item['scope'],item['id'],len(item['members']))
    return 1 if errors else 0
if __name__=='__main__': raise SystemExit(main())
