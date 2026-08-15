#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path


def canonical_bytes(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def unresolved(obj: object, path: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items(): hits.extend(unresolved(v, f"{path}.{k}" if path else str(k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj): hits.extend(unresolved(v, f"{path}[{i}]"))
    elif isinstance(obj, str) and "TBD" in obj:
        hits.append(path)
    return hits


def main() -> int:
    p=argparse.ArgumentParser(description="Freeze and hash the confirmatory analysis plan.")
    p.add_argument("--input", required=True); p.add_argument("--output", required=True)
    p.add_argument("--section", default="analysis", help="Top-level section to freeze; use empty string for full file")
    a=p.parse_args(); src=Path(a.input); out=Path(a.output); root=json.loads(src.read_text(encoding="utf-8"))
    obj=root[a.section] if a.section else root
    missing=unresolved(obj)
    if missing: raise SystemExit("Refusing to freeze unresolved fields: " + ", ".join(missing))
    digest=hashlib.sha256(canonical_bytes(obj)).hexdigest(); envelope={"sha256":digest,"source":str(src),"section":a.section or None,"plan":obj}
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(envelope,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(digest); return 0
if __name__=="__main__": raise SystemExit(main())
