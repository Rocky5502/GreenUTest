#!/usr/bin/env python3
from __future__ import annotations
import argparse, time
from greenutest.harness import NVMLPowerSampler, integrate_joules

def main() -> int:
    p=argparse.ArgumentParser(description='Smoke-test NVML power sampling before any model run.')
    p.add_argument('--seconds',type=float,default=5.0); p.add_argument('--interval-ms',type=int,default=100)
    a=p.parse_args(); sampler=NVMLPowerSampler(interval_s=a.interval_ms/1000.0); sampler.start(); time.sleep(a.seconds); samples=sampler.stop(); energy=integrate_joules(samples)
    print(f'samples={len(samples)} joules={energy:.3f} wh={energy/3600:.6f}'); return 0
if __name__=='__main__': raise SystemExit(main())
