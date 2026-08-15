#!/usr/bin/env python3
"""Deterministically hash a file or directory used as an external experiment artifact."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

CHUNK = 1024 * 1024

def file_sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        while True:
            b=f.read(CHUNK)
            if not b: break
            h.update(b)
    return h.hexdigest()

def tree_manifest(root: Path):
    rows=[]
    for p in sorted(x for x in root.rglob('*') if x.is_file()):
        rel=p.relative_to(root).as_posix()
        rows.append({'path':rel,'bytes':p.stat().st_size,'sha256':file_sha256(p)})
    return rows

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('path')
    ap.add_argument('--output')
    args=ap.parse_args()
    p=Path(args.path).resolve()
    if not p.exists(): raise SystemExit(f'not found: {p}')
    if p.is_file():
        result={'type':'file','path':str(p),'bytes':p.stat().st_size,'sha256':file_sha256(p)}
    else:
        files=tree_manifest(p)
        canonical=''.join(f"{r['path']}\0{r['bytes']}\0{r['sha256']}\n" for r in files).encode()
        result={'type':'directory','path':str(p),'files':len(files),'tree_sha256':hashlib.sha256(canonical).hexdigest(),'manifest':files}
    text=json.dumps(result,indent=2)+"\n"
    if args.output: Path(args.output).write_text(text,encoding='utf-8')
    else: print(text,end='')
    return 0

if __name__=='__main__': raise SystemExit(main())
