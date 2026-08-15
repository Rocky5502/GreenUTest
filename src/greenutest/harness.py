from __future__ import annotations

import hashlib
import json
import math
import random
import subprocess
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable

from .schemas import CandidateTest, Evidence, Outcome, Task


class TaskAdapter(ABC):
    @abstractmethod
    def tasks(self) -> Iterable[Task]: ...


class ToyAdapter(TaskAdapter):
    def tasks(self):
        rows=[("abs_boundary","def abs_like(x): return x if x >= 0 else -x",2),("clamp","def clamp(x, lo, hi): return min(max(x, lo), hi)",3),("safe_div","def safe_div(a, b): return None if b == 0 else a / b",3),("grade","def grade(x): return 'A' if x >= 90 else ('B' if x >= 80 else 'C')",4)]
        for i,(name,code,cx) in enumerate(rows):
            yield Task(f"toy/{i:03d}/{name}","toy",f"Generate concise Python tests for `{name}`.",code,"toy",float(cx),{"smoke_only":True})


class ULTAdapter(TaskAdapter):
    """ULT task adapter with strict generator/evaluator separation.

    Upstream ULT files use a `.jsonl` suffix but released variants may be a JSON array.
    Reference tests (`test_list`) are retained only in an evaluator-side store and are never
    placed in Task.metadata or model prompts.
    """
    def __init__(self,path):
        self.path=Path(path); self._reference_tests={}
    def _rows(self):
        text=self.path.read_text(encoding="utf-8").lstrip()
        if not text: return []
        if text.startswith("["):
            rows=json.loads(text)
            if not isinstance(rows,list): raise ValueError("ULT JSON root must be a list")
            return rows
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    def tasks(self):
        if not self.path.exists(): raise FileNotFoundError(self.path)
        for i,row in enumerate(self._rows()):
            tid=str(row.get("task_id") or row.get("id") or row.get("problem_id") or f"ult/{i}")
            code=str(row.get("code") or row.get("function") or row.get("source") or row.get("prompt") or "")
            cx=row.get("cyclomatic_complexity") or row.get("complexity")
            refs=row.get("test_list") or row.get("tests") or []
            self._reference_tests[tid]=tuple(str(x) for x in refs)
            safe_meta={k:v for k,v in row.items() if k not in {"test_list","tests","reference_tests","gold_tests"}}
            safe_meta["reference_tests_present"]=bool(refs)
            yield Task(tid,"ult",str(row.get("prompt") or "Generate unit tests for the supplied function."),code,row.get("repo") or row.get("repository"),float(cx) if cx is not None else None,{"upstream":safe_meta})
    def reference_tests(self,task_id):
        """Evaluator-only access; never pass this output to a model backend."""
        return self._reference_tests.get(str(task_id),())


class BugsInPyAdapter(TaskAdapter):
    def __init__(self,root): self.root=Path(root)
    def tasks(self):
        projects=self.root/"projects"
        if not projects.exists(): raise FileNotFoundError(projects)
        for proj in sorted(p for p in projects.iterdir() if p.is_dir()):
            bugs=proj/"bugs"
            if not bugs.exists(): continue
            for bug in sorted((p for p in bugs.iterdir() if p.is_dir()),key=lambda p:p.name):
                yield Task(f"bugsinpy/{proj.name}/{bug.name}","bugsinpy","Generate a regression test that distinguishes buggy and fixed behavior.",repository=proj.name,metadata={"bug_dir":str(bug)})


class ManifestOnlyAdapter(TaskAdapter):
    def __init__(self,name,root): self.name=name; self.root=Path(root)
    def tasks(self):
        if not self.root.exists(): raise FileNotFoundError(self.root)
        raise RuntimeError(f"{self.name} requires a pinned upstream-schema audit before execution; do not guess field names.")


class ModelBackend(ABC):
    model_id:str
    @abstractmethod
    def generate(self,task:Task,*,seed:int)->CandidateTest: ...


class FakeModel(ModelBackend):
    def __init__(self,model_id:str,quality:float): self.model_id=model_id; self.quality=quality
    def generate(self,task:Task,*,seed:int)->CandidateTest:
        r=random.Random(f"{seed}:{task.task_id}:{self.model_id}"); conf=min(.99,max(.01,self.quality+r.uniform(-.25,.25))); nll=max(.01,2.3*(1-conf))
        text=f"# synthetic dry-run candidate for {task.task_id}\ndef test_generated():\n    assert {str(conf >= .45)}\n"
        return CandidateTest(text,self.model_id,conf,nll,{"synthetic":True,"quality":self.quality})


class TransformersLocalModel(ModelBackend):
    def __init__(self,model_id,revision=None,max_new_tokens=1024):
        try:
            from transformers import AutoModelForCausalLM,AutoTokenizer
        except ImportError as exc: raise RuntimeError("Install GreenUTest with the local-hf extra") from exc
        self.model_id=model_id; self.revision=revision; self.max_new_tokens=max_new_tokens; self._M=AutoModelForCausalLM; self._T=AutoTokenizer; self.model=None; self.tok=None
    def load(self):
        if self.model is None:
            self.tok=self._T.from_pretrained(self.model_id,revision=self.revision); self.model=self._M.from_pretrained(self.model_id,revision=self.revision,device_map="auto",torch_dtype="auto")
    def generate(self,task,*,seed):
        self.load(); import torch; torch.manual_seed(seed); prompt=f"You are generating Python unit tests.\nCODE:\n{task.code}\nTASK:\n{task.prompt}\n"; inp=self.tok(prompt,return_tensors="pt").to(self.model.device)
        with torch.no_grad(): out=self.model.generate(**inp,max_new_tokens=self.max_new_tokens,do_sample=False)
        seq=out[0,inp["input_ids"].shape[1]:]; return CandidateTest(self.tok.decode(seq,skip_special_tokens=True),self.model_id,metadata={"seed":seed,"revision":self.revision})


def lexical_uncertainty(c):
    if c.token_nll is not None: return Evidence("lexical_uncertainty",1-math.exp(-max(0.,c.token_nll)),metadata={"source":"token_nll"})
    if c.raw_confidence is not None: return Evidence("lexical_uncertainty",1-c.raw_confidence,metadata={"source":"one_minus_raw_confidence"})
    return Evidence("lexical_uncertainty",None,metadata={"missing":True})

def static_risk(t):
    if t.complexity is None: return Evidence("static_software_risk",None,metadata={"missing":True})
    return Evidence("static_software_risk",min(1.,max(0.,(t.complexity-1)/24)),metadata={"complexity":t.complexity})

def disagreement_rate(signatures):
    if len(signatures)<2: return Evidence("behavioral_disagreement",None,metadata={"reason":"need_at_least_two"})
    majority=max(signatures.count(s) for s in set(signatures)); return Evidence("behavioral_disagreement",1-majority/len(signatures),metadata={"n":len(signatures),"unique":len(set(signatures))})

def oracle_disagreement(a,b):
    if a is None or b is None: return Evidence("oracle_disagreement",None,metadata={"missing":True})
    return Evidence("oracle_disagreement",float(a.strip()!=b.strip()))

def weighted_risk(evidence,weights=None):
    weights=weights or {}; vals=[]
    for e in evidence:
        if isinstance(e.value,(int,float)): vals.append((float(e.value),float(weights.get(e.name,1))))
    if not vals: return .5
    den=sum(w for _,w in vals); return sum(v*w for v,w in vals)/den if den else .5

@dataclass(frozen=True)
class VoIDecision: acquire:bool; expected_gain:float; expected_energy_joules:float; score:float
def value_of_information(with_signal,current,energy_joules,lambda_energy_per_joule,threshold=0.):
    gain=with_signal-current; score=gain-lambda_energy_per_joule*max(0.,energy_joules); return VoIDecision(score>threshold,gain,energy_joules,score)

class Action(str,Enum): ACCEPT="ACCEPT"; EXECUTE="EXECUTE"; VERIFY="VERIFY"; REPAIR="REPAIR"; REGENERATE="REGENERATE"; ESCALATE="ESCALATE"; ABSTAIN="ABSTAIN"
@dataclass(frozen=True)
class DecisionState: risk:float; complexity:float|None; raw_confidence:float|None; budget_joules_remaining:float|None=None
class GreenUTestPolicy:
    def __init__(self,risk_accept=.2,risk_verify=.45,risk_escalate=.7,abstain_above=.9):
        if not 0<=risk_accept<=risk_verify<=risk_escalate<=abstain_above<=1: raise ValueError("ordered thresholds required")
        self.a,self.v,self.e,self.z=risk_accept,risk_verify,risk_escalate,abstain_above
    def decide(self,s):
        if s.risk>=self.z:return Action.ABSTAIN
        if s.risk>=self.e:return Action.ESCALATE
        if s.risk>=self.v:return Action.VERIFY
        if s.risk<=self.a:return Action.ACCEPT
        return Action.EXECUTE
class SmallOnlyPolicy:
    def decide(self,s): return Action.EXECUTE
class StrongOnlyPolicy:
    def decide(self,s): return Action.ESCALATE
class RandomRoutingPolicy:
    def __init__(self,rate,seed): self.rate=rate; self.r=random.Random(seed)
    def decide(self,s): return Action.ESCALATE if self.r.random()<self.rate else Action.EXECUTE
class RawConfidencePolicy:
    def __init__(self,t): self.t=t
    def decide(self,s): return Action.ESCALATE if s.raw_confidence is None or s.raw_confidence<self.t else Action.EXECUTE
class StaticComplexityPolicy:
    def __init__(self,t): self.t=t
    def decide(self,s): return Action.ESCALATE if s.complexity is not None and s.complexity>=self.t else Action.EXECUTE

@dataclass(frozen=True)
class PowerSample: t:float; watts:float; phase:str="unassigned"
def integrate_joules(samples):
    if len(samples)<2:return 0.
    o=sorted(samples,key=lambda s:s.t)
    if any(not math.isfinite(x.t) or not math.isfinite(x.watts) or x.watts < 0 for x in o):
        raise ValueError("power samples require finite timestamps and non-negative finite watts")
    return sum(.5*(a.watts+b.watts)*(b.t-a.t) for a,b in zip(o,o[1:]))

def summarize_power(samples, idle_watts=0.0):
    if idle_watts < 0: raise ValueError("idle_watts must be non-negative")
    ordered=sorted(samples,key=lambda s:s.t)
    total=integrate_joules(ordered)
    phases={}
    for phase in sorted({s.phase for s in ordered}):
        phase_samples=[s for s in ordered if s.phase==phase]
        # Only contiguous same-phase intervals contribute to a phase subtotal.
        e=0.0
        for a,b in zip(ordered,ordered[1:]):
            if a.phase==phase and b.phase==phase:
                e += .5*(a.watts+b.watts)*(b.t-a.t)
        phases[phase]=e
    duration=max(0.0, ordered[-1].t-ordered[0].t) if len(ordered)>=2 else 0.0
    idle_adjusted=max(0.0,total-idle_watts*duration)
    return {"joules":total,"wh":total/3600.0,"idle_adjusted_joules":idle_adjusted,"idle_adjusted_wh":idle_adjusted/3600.0,"duration_s":duration,"by_phase_joules":phases}
class NullEnergyMeter:
    def __init__(self): self.phases=[]
    def mark(self,p): self.phases.append(p)
    def summary(self): return {"backend":"null","measured":False,"joules":0.,"wh":0.,"phases":self.phases}
class NVMLPowerSampler:
    def __init__(self,device_index=0,interval_s=.1):
        try: import pynvml
        except ImportError as exc: raise RuntimeError("Install GreenUTest with the energy extra") from exc
        self.nv=pynvml; self.interval_s=interval_s; self.samples=[]; self.stop_event=threading.Event(); self.phase="unassigned"; pynvml.nvmlInit(); self.handle=pynvml.nvmlDeviceGetHandleByIndex(device_index)
    def set_phase(self,p): self.phase=p
    def _loop(self):
        while not self.stop_event.is_set(): self.samples.append(PowerSample(time.perf_counter(),self.nv.nvmlDeviceGetPowerUsage(self.handle)/1000.,self.phase)); self.stop_event.wait(self.interval_s)
    def start(self): self.samples=[]; self.stop_event.clear(); self.thread=threading.Thread(target=self._loop,daemon=True); self.thread.start()
    def stop(self): self.stop_event.set(); self.thread.join(timeout=max(1.,self.interval_s*5)); return list(self.samples)

def synthetic_evaluate(task,candidate):
    p=hashlib.sha256(f"{task.task_id}|{candidate.text}|{candidate.model_id}".encode()).digest()[0]/255.; ex=p>.12; ov=p>.25 if ex else False; fd=p>.55 if ov else False
    return Outcome(True,ex,ov,p>.45,fd,bool(ex and not ov and p>.15),round(.2+.7*p,4) if ex else 0.,round(.3+.65*p,4) if ex else 0.,round(.1+.8*p,4) if ov else 0.,round(p,4),{"synthetic":True,"no_code_execution":True})

@dataclass(frozen=True)
class ProcessResult: returncode:int; stdout:str; stderr:str; timed_out:bool
def run_command(command,*,cwd,timeout_s=60.,env=None):
    try:
        cp=subprocess.run(command,cwd=cwd,env=env,text=True,capture_output=True,timeout=timeout_s,check=False); return ProcessResult(cp.returncode,cp.stdout,cp.stderr,False)
    except subprocess.TimeoutExpired as exc:return ProcessResult(-1,exc.stdout or "",exc.stderr or "",True)
