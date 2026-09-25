# example-background-agents

A dltHub workspace with five example pipelines against the live
[Jaffle Shop API](https://jaffle-shop.dlthub.com/docs): one correct, four
broken in different ways. Deploy them to dltHub Platform and use them as the
substrate for building background agents that diagnose failing or silently
under-loading jobs.

## Setup

```bash
uv sync
cp -n .dlt/config.toml.template .dlt/config.toml
uv run dlthub local run load_jaffle_correct   # smoke test
uv run dlthub login
uv run dlthub workspace connect --create example-background-agents
uv run dlthub deploy
```

`.dlt/config.toml` is gitignored — `dlthub workspace connect` writes your
`workspace_id`, `organization_id` and workspace name into it. Copy it from the
template and it stays out of your commits.

## The pipelines

`jaffle_shop/` runs against the live
[Jaffle Shop API](https://jaffle-shop.dlthub.com/docs). Fire them all with
`uv run dlthub job trigger tag:jaffle`.

| pipeline | outcome | the bug |
|---|---|---|
| `correct` | 935 / 10 / 6 rows | the reference |
| `bad_config` | **fails** | `base_url` on `/api/v2/`, 404 on the first request |
| `bad_incremental` | **fails** | `cursor_path` on a field the API does not have |
| `bad_pagination` | **green**, 100 of 935 rows | paginator reads `next` from the body; this API uses the `Link` header |
| `bad_selector` | **green**, 0 of 6 rows | `data_selector` points at `data.results`; the API returns a bare array |

Two fail outright. The other two lose data without failing. They finish green,
so no job-status trigger sees them at all — that's the interesting class of
problem for a background agent to catch.

### `correct` — the reference

Jaffle Shop, done right. The baseline every broken example is compared
against. Loads customers (935), products (10) and stores (6). Orders and items
are left out on purpose: at 62k and 91k rows they make a demo run slow without
teaching anything extra.

### `bad_config` — fixed api config

Fixed after the job-inspector diagnosis. The original broken version pointed
at `/api/v2/` and configured placeholder bearer auth. The API serves `/api/v1/`
and is unauthenticated, so this source now uses the shared correct base URL
and no auth.

### `bad_incremental` — wrong incremental cursor

Fails once extraction starts. The orders endpoint accepts `start_date` /
`end_date`, and each order carries an `ordered_at` timestamp. This job
configures the incremental cursor on `updated_at` — a field that does not
exist on this API.

Expected failure:

```
IncrementalCursorPathMissing: Cursor element with JSON path `updated_at`
was not found in extracted data item.
```

The tell is that it fails *during* extraction rather than on the first
request, so unlike the 404 case it can leave a partial load behind. Fix by
pointing `cursor_path` at the real field, `ordered_at`.

### `bad_pagination` — silent under-load

The run goes green and loads 100 of 935 customers. The mistake: the
`json_link` paginator looks for a `next` key **in the response body**, but
this API advertises the next page in the `Link` response **header**. The body
is a bare array, so `next` is never found, the paginator concludes there is
no next page, and extraction stops after page one.

```
correct (`header_link`) -> 935 rows
this    (`json_link`)   -> 100 rows   (10.7% of the data)
```

This is the dangerous class of bug: nothing fails. No exception, no warning,
a green run, and a table that is quietly missing 89% of its rows. Compare
`customers_bad_pagination` against `customers` in the `jaffle_shop` dataset.

Two variants of the same mistake ship in this pipeline — the second one caps
at a fixed page count, which breaks the day the dataset outgrows the cap.

### `bad_selector` — green run, empty table

`data_selector` is a JSONPath into the response body. This API returns a bare
array, so the records are at the root. Pointing the selector at `data.results`
— the shape a *different* API would use — matches nothing, so the resource
yields zero records.

```
correct (root / omitted)  -> 6 stores
this    (`data.results`)  -> 0 rows
```

Same failure class as the pagination bug: the run is green, no exception is
raised, and the only symptom is a table that is emptier than it should be. A
row-count check is what catches this, not the job status.
