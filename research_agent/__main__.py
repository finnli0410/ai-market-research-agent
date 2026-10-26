"""python -m research_agent "French accounting SaaS" [--demo] [--out report.md]"""
import argparse
import sys

from . import agent, llm
from .render import to_markdown


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="research_agent", description="Cited market research report in Markdown")
    p.add_argument("subject")
    p.add_argument("--demo", action="store_true", help="use the cached sample run (no API key needed)")
    p.add_argument("--out", help="write the report to this file")
    a = p.parse_args(argv)
    if not a.demo and not llm.configured():
        print("RESEARCH_LLM_API_KEY not set: running in demo mode with the cached sample.", file=sys.stderr)
    md = to_markdown(agent.run(a.subject, demo=a.demo))
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(md)
    else:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
