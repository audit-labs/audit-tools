#!/usr/bin/env python3
import requests
from common import build_parser, init_run, write_artifacts, write_meta

def main():
    p=build_parser('Collect GitLab password policy settings')
    p.add_argument('--timeout',type=int,default=30)
    a=p.parse_args(); run,run_id=init_run(a,'gitlab_passwords')
    if a.dry_run: print('Dry run: would collect /application/settings'); return 0
    r=requests.get(f"{a.base_url}/application/settings",headers={'PRIVATE-TOKEN':a.private_token},timeout=a.timeout)
    if r.status_code!=200:
        err=f"Failed to fetch settings: {r.status_code}"
        (run['exceptions']/ 'request_error.txt').write_text(err)
        write_meta(run,'gitlab_passwords',run_id,a,errors=[err]); return 1
    settings=r.json(); keep={k:settings.get(k) for k in ['minimum_password_length','password_number_required','password_symbol_required','password_uppercase_required','password_lowercase_required']}
    write_artifacts(run,'password_settings',keep); write_meta(run,'gitlab_passwords',run_id,a,counts={'settings_fields':len(keep)})
    if not a.quiet:
      for k,v in keep.items(): print(f"{k}: {v}")
    return 0
if __name__=='__main__': raise SystemExit(main())
