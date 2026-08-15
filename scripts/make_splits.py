from __future__ import annotations
import argparse, hashlib, json, random
from pathlib import Path

PARTITIONS = (('pilot', .10), ('calibration_fit', .30), ('policy_tuning', .25), ('heldout_final', .35))

def stable_hash(obj: object) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def main() -> None:
    ap=argparse.ArgumentParser(description='Create deterministic group-level GreenUTest split manifest.')
    ap.add_argument('--groups', required=True, help='Text file: one repository/project/group id per line')
    ap.add_argument('--output', required=True)
    ap.add_argument('--seed', type=int, default=20260815)
    args=ap.parse_args()
    groups=sorted({x.strip() for x in Path(args.groups).read_text(encoding='utf-8').splitlines() if x.strip()})
    if len(groups) < 4:
        raise SystemExit('Need at least 4 unique groups to produce all four partitions.')
    rng=random.Random(args.seed); rng.shuffle(groups)
    n=len(groups); cursor=0; assignments={}
    for i,(name, frac) in enumerate(PARTITIONS):
        end=n if i == len(PARTITIONS)-1 else cursor + max(1, round(n*frac))
        end=min(end, n-(len(PARTITIONS)-i-1))
        for g in groups[cursor:end]: assignments[g]=name
        cursor=end
    manifest={'schema_version':1,'seed':args.seed,'group_count':n,'assignments':dict(sorted(assignments.items()))}
    manifest['sha256']=stable_hash(manifest)
    out=Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(f"{out}  sha256={manifest['sha256']}")
if __name__=='__main__': main()
