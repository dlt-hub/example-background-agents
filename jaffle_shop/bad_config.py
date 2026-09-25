import dlt
from dlt.hub import run
from dlt.hub.run import trigger
from dlt.sources.rest_api import rest_api_source

from jaffle_shop import BASE_URL, DATASET, PAGE_SIZE, TAG


def misconfigured_source():
    return rest_api_source(
        {
            "client": {
                "base_url": BASE_URL,
                "paginator": "header_link",
            },
            "resource_defaults": {
                "write_disposition": "replace",
                "endpoint": {"params": {"page_size": PAGE_SIZE}},
            },
            "resources": [
                {"name": "products_bad_config", "endpoint": {"path": "products"}},
            ],
        }
    )


@run.pipeline(
    "jaffle_bad_config",
    section="jaffle_shop",
    trigger=trigger.tag(TAG),
    expose={
        "display_name": "Jaffle — fixed api config",
        "tags": ["jaffle", "fixed"],
    },
)
def load_jaffle_bad_config() -> None:
    pipeline = dlt.pipeline(
        pipeline_name="jaffle_bad_config",
        destination="playground",
        dataset_name=DATASET,
    )
    info = pipeline.run(misconfigured_source())
    print(info)


if __name__ == "__main__":
    load_jaffle_bad_config()
