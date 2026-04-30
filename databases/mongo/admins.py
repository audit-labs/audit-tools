#!/usr/bin/env python3
"""Collect MongoDB admin users into standardized output tree."""
import argparse, json, sys
from pymongo import MongoClient
from shared.python.cli import add_standard_flags
from shared.python.outputs import ensure_run_tree
from shared.python.metadata import build_metadata

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--uri',default='mongodb://localhost:27017/')
    p=add_standard_flags(p,formats=('json',))
    a=p.parse_args()
    run=ensure_run_tree(a.output_dir,'mongo_admins'); run_id=run['root'].name
    if a.dry_run: print('Dry run: would query MongoDB admin users'); return
    client=MongoClient(a.uri)
    users=list(client.admin.system.users.find({}, {'user':1,'db':1,'roles':1,'userSource':1,'_id':0}))
    (run['raw']/ 'users_raw.json').write_text(json.dumps(users,indent=2,default=str))
    (run['parsed']/ 'admins.json').write_text(json.dumps(users,indent=2,default=str))
    (run['evidence']/ 'admins.json').write_text(json.dumps(users,indent=2,default=str))
    meta=build_metadata(tool='mongo_admins',run_id=run_id,command=' '.join(sys.argv),record_counts={'users':len(users)})
    (run['root']/ 'metadata.json').write_text(json.dumps(meta,indent=2))
    if not a.quiet:
        for u in users: print(u)
if __name__=='__main__': main()
