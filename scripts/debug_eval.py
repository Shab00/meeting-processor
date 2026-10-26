import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")

from app.routes.analyse import run_and_parse
from evals.loader import load_samples
from evals.matcher import jaccard, tokens

def containment(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))

async def main():
    samples = {s["id"]: s for s in load_samples(Path("evals/data/samples.jsonl"))}
    for sid in ["sprint_planning", "incident_postmortem", "product_roadmap",
                "hiring_debrief", "vendor_selection"]:
        s = samples[sid]
        print("=" * 80)
        print(sid)
        a = await run_and_parse(s["transcript"])
        for cat in ["decisions", "risks", "action_items"]:
            exp = s["expected"][cat]
            pred = getattr(a, cat)
            print(f"\n--- {cat} ---")
            print("EXPECTED:")
            for e in exp:
                desc = e.get("description") or f'{e.get("owner")} | {e.get("task")}'
                print("  -", desc)
            print("PREDICTED:")
            for p in pred:
                desc = getattr(p, "description", None) or f"{p.owner} | {p.task}"
                print("  -", desc)
        for cat in ["decisions", "risks"]:
            exp, pred = s["expected"][cat], getattr(a, cat)
            if exp and pred:
                print(f"\nScores[{cat}] expected[0] vs each predicted:")
                for p in pred:
                    j = jaccard(exp[0]['description'], p.description)
                    c = containment(exp[0]['description'], p.description)
                    print(f"  J={j:.2f} C={c:.2f}  {p.description[:70]}")

if __name__ == "__main__":
    asyncio.run(main())
