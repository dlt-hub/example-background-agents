import dlt
from dlt.hub import run
from dlt.hub.run import trigger
from dlt.sources.rest_api import rest_api_source

from jaffle_shop import BASE_URL, DATASET, PAGE_SIZE, TAG


def broken_source():
    return rest_api_source(
        {
            "client": {
                "base_url": BASE_URL,
                # BUG: this API has no `next` key in the body — it uses a Link header.
                # Should be: "paginator": "header_link"
                "paginator": {"type": "json_link", "next_url_path": "next"},
            },
            "resource_defaults": {
                "write_disposition": "replace",
                "endpoint": {"params": {"page_size": PAGE_SIZE}},
            },
            "resources": [
                {
                    "name": "customers_bad_pagination",
                    "endpoint": {"path": "customers"},
                },
                {
                    # BUG (variant): hard-capped page count. Fine today at 6 stores,
                    # silently truncating the day there are more than 2 pages of them.
                    "name": "stores_bad_pagination",
                    "endpoint": {
                        "path": "stores",
                        "paginator": {
                            "type": "page_number",
                            "base_page": 1,
                            "page_param": "page",
                            "total_path": None,
                            "maximum_page": 2,
                        },
                    },
                },
            ],
        }
    )


@run.pipeline(
    "jaffle_bad_pagination",
    section="jaffle_shop",
    trigger=trigger.tag(TAG),
    expose={
        "display_name": "Jaffle — BROKEN pagination (silent under-load)",
        "tags": ["jaffle", "broken", "silent"],
    },
)
def load_jaffle_bad_pagination() -> None:
    pipeline = dlt.pipeline(
        pipeline_name="jaffle_bad_pagination",
        destination="playground",
        dataset_name=DATASET,
    )
    info = pipeline.run(broken_source())
    print(info)
    print(
        "NOTE: this run is green but incomplete — expected 935 customers, "
        "loaded 100. Compare with the `customers` table from jaffle_correct."
    )


if __name__ == "__main__":
    load_jaffle_bad_pagination()
