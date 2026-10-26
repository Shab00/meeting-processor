# Extraction eval harness

Offline evaluation of the meeting-processor agent against hand-labelled
ground truth.

```bash
python scripts/run_evals.py            # all samples
python scripts/run_evals.py --limit 1  # smoke test
```

Reports are written to `evals/artifacts/report.json` and `report.md`. The
script exits 1 if any sample failed to run (crash or timeout), 0 otherwise —
low scores do not fail the run.

## What it measures

**Structural extraction quality**, not summary quality. For each transcript
the harness calls `run_and_parse` directly (no HTTP, no database) and compares
the extracted items to the expected ones:

| Category       | Compared fields             | Ignored                      |
|----------------|-----------------------------|------------------------------|
| `action_items` | `owner`, `task`             | `due_date`*, `source_quote`  |
| `decisions`    | `description`               | `made_by`, `source_quote`    |
| `risks`        | `description`               | `severity`, `source_quote`   |

\* `due_date` is carried through into the report for inspection but is not
part of the match criterion.

Per category it reports precision, recall, F1, TP/FP/FN and a
**hallucination rate** = predicted items with no ground-truth match / total
predicted (i.e. `FP / (TP + FP)`). Aggregates are micro-averaged (sum
TP/FP/FN across samples, then compute metrics); macro F1 (mean of per-sample
F1) is also included in the JSON and Markdown reports.

## Matching strategy

Text is normalised (lowercase, punctuation removed, whitespace collapsed),
tokenised, and a small stopword list is dropped. Two strings match when the
Jaccard similarity of their token sets is **≥ 0.6**. Action items
additionally require an **exact owner match** after normalisation.

This is deliberately simple and transparent. It will under-credit valid
paraphrases ("handle the Stripe contract" vs "finalise contract with
Stripe"), so treat scores as a lower bound and read the predicted items in
`report.json` when a number looks surprising.

## Why greedy matching

Each expected item matches **at most one** predicted item and vice versa.
Expected items are walked in order and claim the first unmatched prediction
that passes the match function. This prevents one good prediction from
satisfying several expected items (inflating recall), and prevents duplicate
predictions from all counting as hits (inflating precision) — duplicates show
up as false positives. Greedy is not an optimal assignment, but with the
small item counts per meeting the difference is negligible and the behaviour
is easy to reason about.

## Adding samples

Append one JSON object per line to `evals/data/samples.jsonl`. No code
change is required.

```json
{"id": "unique_id", "transcript": "...", "expected": {
  "action_items": [{"owner": "Name", "task": "...", "due_date": "Friday or null"}],
  "decisions":    [{"description": "..."}],
  "risks":        [{"description": "..."}]
}}
```

(Shown wrapped for readability — each sample must be a single line.) The
loader raises a `ValueError` with the line number if a line is malformed.

## Known limitations

- **5 samples is not statistically meaningful.** A single item flipping
  moves a category's numbers substantially. Aim for 15–20 samples before
  quoting numbers as authoritative.
- The agent is non-deterministic; expect run-to-run variance.
- **Summary text is not scored.** Measuring summary quality properly would
  need a separate LLM-as-judge evaluation, which is explicitly out of scope
  for this harness.
