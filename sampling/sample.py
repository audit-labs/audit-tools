#!/usr/bin/env python3
"""Simple random sampling helper with standardized outputs."""
import argparse, json
from pathlib import Path
import pandas as pd
from shared.python.cli import add_standard_flags
from shared.python.outputs import ensure_run_tree
from shared.python.metadata import build_metadata

TOOL="sampling_random"

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("input_file")
    p.add_argument("--sample-size",type=int,default=25)
    p=add_standard_flags(p,formats=("csv","json"))
    a=p.parse_args()
    run=ensure_run_tree(a.output_dir,TOOL)
    run_id=run['root'].name
    if a.dry_run:
        print(f"Dry run: would sample {a.sample_size} rows from {a.input_file}")
        return
    df=pd.read_excel(a.input_file) if a.input_file.endswith((".xlsx",".xls")) else pd.read_csv(a.input_file)
    sample=df.sample(a.sample_size)
    sample.to_csv(run['evidence']/"sample.csv",index=False)
    if a.format=="json":
        sample.to_json(run['parsed']/"sample.json",orient="records",indent=2)
    else:
        sample.to_csv(run['parsed']/"sample.csv",index=False)
    (run['raw']/"input_snapshot.csv").write_text(df.head(200).to_csv(index=False))
    meta=build_metadata(tool=TOOL,run_id=run_id,command=" ".join(__import__('sys').argv),record_counts={"input_rows":len(df),"sample_rows":len(sample)})
    (run['root']/"metadata.json").write_text(json.dumps(meta,indent=2))
    if not a.quiet:
        print(sample)

if __name__=='__main__':
    main()
