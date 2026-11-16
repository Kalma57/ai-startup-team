"""Shared state on disk (rules 2 and 3): runs/<run_id>/state.json + trace.jsonl."""
import json
import logging
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from schemas import RunState

log = logging.getLogger("state")

RUNS_DIR = Path("runs")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Run:
    """One run's folder: loads/saves state.json and appends to trace.jsonl."""

    def __init__(self, run_id: str, runs_dir: Path = RUNS_DIR):
        self.run_id = run_id
        self.dir = runs_dir / run_id
        self.state_path = self.dir / "state.json"
        self.trace_path = self.dir / "trace.jsonl"

    @classmethod
    def create(cls, idea: str, run_id: str | None = None, runs_dir: Path = RUNS_DIR):
        run_id = run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
        run = cls(run_id, runs_dir)
        if run.dir.exists():
            raise FileExistsError(f"Run folder already exists: {run.dir}")
        run.dir.mkdir(parents=True)
        state = RunState(run_id=run_id, created_at=now_iso(), idea=idea)
        run.save(state)
        return run, state

    def save(self, state: RunState) -> None:
        """Write atomically so another agent never reads a half-written file."""
        tmp = self.state_path.with_suffix(".json.tmp")
        tmp.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        os.replace(tmp, self.state_path)

    def load(self) -> RunState:
        return RunState.model_validate_json(self.state_path.read_text(encoding="utf-8"))

    def trace(self, agent: str, step: str, seconds: float, note: str = "") -> None:
        entry = {"at": now_iso(), "agent": agent, "step": step,
                 "seconds": round(seconds, 2), "note": note}
        with self.trace_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        log.info("[%s] %s (%.1fs) %s", agent, step, seconds, note)

    @contextmanager
    def step(self, agent: str, step: str):
        """Time a step and trace it. Yields a dict; put a 'note' in it to record details."""
        info: dict = {"note": ""}
        start = time.monotonic()
        try:
            yield info
        except Exception as exc:
            self.trace(agent, step, time.monotonic() - start, f"FAILED: {exc}")
            raise
        self.trace(agent, step, time.monotonic() - start, info["note"])
