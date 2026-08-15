from __future__ import annotations
import argparse, json, platform, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path


def run(cmd: list[str]) -> str | None:
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, timeout=15).strip()
    except Exception:
        return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', default='artifacts/environment.json')
    args = ap.parse_args()
    payload = {
        'captured_at_utc': datetime.now(timezone.utc).isoformat(),
        'python': sys.version,
        'platform': platform.platform(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'git_commit': run(['git', 'rev-parse', 'HEAD']),
        'git_status': run(['git', 'status', '--porcelain']),
        'nvidia_smi': run(['nvidia-smi', '--query-gpu=name,uuid,memory.total,driver_version,power.limit', '--format=csv,noheader']),
        'pip_freeze': (run([sys.executable, '-m', 'pip', 'freeze']) or '').splitlines(),
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(out)

if __name__ == '__main__':
    main()
