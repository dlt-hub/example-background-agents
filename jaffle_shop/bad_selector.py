import dlt
from dlt.hub import run
from dlt.hub.run import trigger
from dlt.sources.rest_api import rest_api_source

from jaffle_shop import BASE_URL, DATASET, PAGE_SIZE, TAG


def bad_selector_source():
    return rest_api_source(
        {
            "client": {"base_url": BASE_URL, "paginator": "header_link"},
            "resource_defaults": {
                "write_disposition": "replace",
                "endpoint": {"params": {"page_size": PAGE_SIZE}},
            },
            "resources": [
                {
                    "name": "stores_bad_selector",
                    "endpoint": {
                        "path": "stores",
                        # BUG: response is a bare array — there is no `data.results`
                        # envelope. Omit data_selector entirely to read the root.
                        "data_selector": "data.results",
                    },
                },
            ],
        }
    )


@run.pipeline(
    "jaffle_bad_selector",
    section="jaffle_shop",
    trigger=trigger.tag(TAG),
    expose={
        "display_name": "Jaffle — BROKEN data selector (empty table)",
        "tags": ["jaffle", "broken", "silent"],
    },
)
def load_jaffle_bad_selector() -> None:
    pipeline = dlt.pipeline(
        pipeline_name="jaffle_bad_selector",
        destination="playground",
        dataset_name=DATASET,
    )
    info = pipeline.run(bad_selector_source())
    print(info)
    print("NOTE: green run, 0 rows loaded — expected 6 stores.")


if __name__ == "__main__":
    load_jaffle_bad_selector()
