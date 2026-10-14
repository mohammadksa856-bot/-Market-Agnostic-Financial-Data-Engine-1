from __future__ import annotations
import time
from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class Job:
    name: str
    interval_seconds: int
    action: callable
    next_run: float = 0

class Scheduler:
    def __init__(self, jobs: list[Job]): self.jobs=jobs
    def tick(self, now: float | None=None):
        now=time.time() if now is None else now; results=[]
        for j in self.jobs:
            if now>=j.next_run:
                try: results.append((j.name,j.action(),None))
                except Exception as e: results.append((j.name,None,e))
                j.next_run=now+j.interval_seconds
        return results
    def serve(self, poll_seconds=30):
        while True: self.tick(); time.sleep(poll_seconds)
