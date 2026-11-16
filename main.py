"""CLI entry point.

    python main.py research --idea-file examples/plantcare.txt
    python main.py research --idea "text of the startup idea"

Exit codes: 0 = ok, 2 = partial (some category empty), 1 = failed / bad input.
"""
import argparse
import logging
import sys
from pathlib import Path

from google import genai

from agents.research import run_research
from config import ConfigError, load_settings
from state import Run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Startup Team")
    sub = parser.add_subparsers(dest="command", required=True)
    research = sub.add_parser("research", help="Run the Research agent")
    group = research.add_mutually_exclusive_group(required=True)
    group.add_argument("--idea", help="The startup idea as text")
    group.add_argument("--idea-file", help="Path to a UTF-8 text file with the startup idea")
    research.add_argument("--run-id", help="Name of the run folder (default: timestamp)")
    return parser


def read_idea(args: argparse.Namespace) -> str:
    if args.idea:
        idea = args.idea
    else:
        idea = Path(args.idea_file).read_text(encoding="utf-8")
    idea = idea.strip()
    if not idea:
        raise ValueError("The startup idea is empty.")
    return idea


def print_summary(state, run: Run) -> None:
    print(f"\nRun {state.run_id}: {state.status.upper()}")
    if state.error:
        print(f"Error: {state.error}")
    if state.research:
        r = state.research
        print(f"  competitors={len(r.competitors)}  audiences={len(r.audiences)}  "
              f"pain_points={len(r.pain_points)}  market_signals={len(r.market_signals)}")
        print(f"  sources found={len(state.sources)}  dropped={len(state.dropped)}")
    print(f"State: {run.state_path}")
    print(f"Trace: {run.trace_path}")


def main(argv=None) -> int:
    # Hebrew text must not crash the Windows console
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s",
                        datefmt="%H:%M:%S")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("google_genai").setLevel(logging.WARNING)

    args = build_parser().parse_args(argv)
    try:
        settings = load_settings()
        idea = read_idea(args)
    except (ConfigError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        run, state = Run.create(idea, args.run_id)
    except FileExistsError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    client = genai.Client(api_key=settings.api_key)
    state = run_research(run, state, client, settings)
    print_summary(state, run)
    return {"ok": 0, "partial": 2}.get(state.status, 1)


if __name__ == "__main__":
    sys.exit(main())
