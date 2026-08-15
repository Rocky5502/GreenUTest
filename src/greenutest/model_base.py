from __future__ import annotations

import random
from abc import ABC, abstractmethod

from .schemas import CandidateTest, Task

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


