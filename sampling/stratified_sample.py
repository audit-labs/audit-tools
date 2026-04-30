#!/usr/bin/env python3
"""Stratified sampling helper with standardized outputs."""
import argparse, json, math
import pandas as pd
from shared.python.cli import add_standard_flags
from shared.python.outputs import ensure_run_tree
from shared.python.metadata import build_metadata

TOOL="sampling_stratified"

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("input_file")
    p.add_argument("--sample-size",type=int,default=25)
    p.add_argument("--stratify-column",required=True)
    p.add_argument("--proportions",required=True,help='JSON object like {"A":0.5,"B":0.5}')
    p=add_standard_flags(p,formats=("csv","json"))
    a=p.parse_args()
    run=ensure_run_tree(a.output_dir,TOOL); run_id=run['root'].name
    if a.dry_run:
        print("Dry run complete"); return
    df=pd.read_excel(a.input_file) if a.input_file.endswith((".xlsx",".xls")) else pd.read_csv(a.input_file)
    props=json.loads(a.proportions)
    if not math.isclose(sum(props.values()),1.0): raise ValueError("Proportions must sum to 1")
    samples=[]
    for k,v in props.items():
        s=df[df[a.stratify_column]==k]
        n=math.floor(a.sample_size*v)
        samples.append(s.sample(n=n,random_state=42))
    out=pd.concat(samples).reset_index(drop=True)
    if len(out)<a.sample_size: out=pd.concat([out,df.sample(n=a.sample_size-len(out),random_state=42)])
    out.to_csv(run['evidence']/"sample.csv",index=False)
    (out.to_json(run['parsed']/"sample.json",orient='records',indent=2) if a.format=='json' else out.to_csv(run['parsed']/"sample.csv",index=False))
    meta=build_metadata(tool=TOOL,run_id=run_id,command=" ".join(__import__('sys').argv),record_counts={"input_rows":len(df),"sample_rows":len(out)})
    (run['root']/"metadata.json").write_text(json.dumps(meta,indent=2))
    if not a.quiet: print(out)

if __name__=='__main__': main()
