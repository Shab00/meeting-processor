import asyncio

from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

from evals.scorer import aggregate, score_sample  # noqa: E402


async def run_evals(
    samples: list[dict],
    limit: int | None = None,
    per_sample_timeout_s: float = 120.0,
) -> dict:
    # Lazy import: app.config reads the environment at import time, so this
    # must happen after load_dotenv above.
    from app.routes.analyse import run_and_parse

    if limit is not None:
        samples = samples[:limit]

    results: list[dict] = []
    failed: list[dict] = []
    for sample in samples:
        try:
            analysis = await asyncio.wait_for(
                run_and_parse(sample["transcript"]), timeout=per_sample_timeout_s
            )
        except (asyncio.TimeoutError, TimeoutError):
            failed.append({"sample_id": sample["id"], "error": "failed: timeout"})
            continue
        except Exception as e:  # noqa: BLE001 - record and keep going
            failed.append(
                {"sample_id": sample["id"], "error": f"failed: {type(e).__name__}: {e}"}
            )
            continue
        results.append(score_sample(sample, analysis))

    return {"results": results, "failed": failed, "aggregate": aggregate(results)}
