#!/usr/bin/env python3
"""Verify local benchmark checkouts against the frozen upstream manifest."""
from __future__ import annotations
import argparse, json, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'data'/'upstreams.json'

def git(cwd,*args): return subprocess.check_output(['git',*args],cwd=cwd,text=True).strip()

def main():
    p=argparse.ArgumentParser(); p.add_argument('--external',default='external'); p.add_argument('--name',action='append')
    a=p.parse_args(); m=json.loads(MANIFEST.read_text())['sources']; names=a.name or list(m); failures=0
    for name in names:
        spec=m[name]; checkout=Path(a.external)/Path(spec['repo']).stem
        if not checkout.exists(): print(f'SKIP {name}: missing {checkout}'); continue
        head=git(checkout,'rev-parse','HEAD'); expected=spec['pinned_commit']; ok=head==expected
        print(f'{"OK" if ok else "FAIL"} {name}: HEAD {head} expected {expected}')
        failures += 0 if ok else 1
        if name=='ult' and ok:
            for path_key,sha_key in [('path_hint','git_blob_sha'),('lite_path_hint','lite_git_blob_sha'),('plt_path_hint','plt_git_blob_sha')]:
                rel=spec[path_key]; actual=git(checkout,'hash-object',rel); want=spec[sha_key]; same=actual==want
                print(f'  {"OK" if same else "FAIL"} {rel}: blob {actual} expected {want}')
                failures += 0 if same else 1
    return 1 if failures else 0

if __name__=='__main__': raise SystemExit(main())
