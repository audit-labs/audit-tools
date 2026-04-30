#!/usr/bin/env python3
"""Evaluate SQL login password settings with standardized outputs."""
import argparse, json, sys
import pandas as pd
from shared.python.cli import add_standard_flags
from shared.python.outputs import ensure_run_tree
from shared.python.metadata import build_metadata

def apply_rules_and_report(df):
    report=[]
    for _,row in df.iterrows():
        reason=[]
        t='SQL_LOGIN' if row['type_desc']=='SQL_LOGIN' else ('N/A' if row['type_desc']=='WINDOWS_LOGIN' else 'Manual Review')
        if t=='N/A': reason.append('Refer to Windows password policy.')
        if t=='Manual Review': reason.append('Reviewer to manually review.')
        policy='PASS' if row['is_policy_checked']==1 else 'FAIL'
        reason.append('Password policy is enforced.' if policy=='PASS' else 'Password policy is not enforced.')
        exp='PASS' if row['is_expiration_checked']==1 else 'FAIL'
        reason.append('Password expiration is enforced.' if exp=='PASS' else 'Password expiration is not enforced.')
        report.append({'Name':row['name'],'Type Check':t,'Policy Check':policy,'Expiration Check':exp,'Reason':' '.join(reason)})
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',default='./data.csv')
    p=add_standard_flags(p,formats=('csv','json'))
    a=p.parse_args(); run=ensure_run_tree(a.output_dir,'sql_passwords'); run_id=run['root'].name
    if a.dry_run: print(f'Dry run: would read {a.input}'); return
    df=pd.read_csv(a.input); rep=apply_rules_and_report(df); rdf=pd.DataFrame(rep)
    rdf.to_csv(run['evidence']/ 'password_review.csv',index=False)
    (rdf.to_json(run['parsed']/ 'password_review.json',orient='records',indent=2) if a.format=='json' else rdf.to_csv(run['parsed']/ 'password_review.csv',index=False))
    df.to_csv(run['raw']/ 'input.csv',index=False)
    (run['root']/ 'metadata.json').write_text(json.dumps(build_metadata(tool='sql_passwords',run_id=run_id,command=' '.join(sys.argv),record_counts={'input_rows':len(df),'report_rows':len(rdf)}),indent=2))
    if not a.quiet: print(rdf)
if __name__=='__main__': main()
