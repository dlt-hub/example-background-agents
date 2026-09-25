"""Example jaffle pipelines: one correct, four broken in different ways."""

from dlt.hub import run

from jaffle_shop.bad_config import load_jaffle_bad_config
from jaffle_shop.bad_incremental import load_jaffle_bad_incremental
from jaffle_shop.bad_pagination import load_jaffle_bad_pagination
from jaffle_shop.bad_selector import load_jaffle_bad_selector
from jaffle_shop.correct import load_jaffle_correct

job_inspector = run.agent(
    "dlthub-platform:job-inspector",
    section="__deployment__",
    trigger=[
        load_jaffle_correct.fail,
        load_jaffle_bad_pagination.fail,
        load_jaffle_bad_selector.fail,
        load_jaffle_bad_config.fail,
        load_jaffle_bad_incremental.fail,
    ],
    require={"profile": "access"},
)

__all__ = [
    # --- jaffle_shop/ — one correct pipeline and four broken ones -----------
    "load_jaffle_correct",  # tag:jaffle -> 935 / 10 / 6 rows
    "load_jaffle_bad_pagination",  # tag:jaffle -> GREEN, 100 of 935 rows
    "load_jaffle_bad_selector",  # tag:jaffle -> GREEN, 0 of 6 rows
    "load_jaffle_bad_config",  # tag:jaffle -> FAILS, 404 on /api/v2/
    "load_jaffle_bad_incremental",  # tag:jaffle -> FAILS, bad cursor_path
    "job_inspector",
]
