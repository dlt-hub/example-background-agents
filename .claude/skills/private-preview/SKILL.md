---
name: private-preview
description: "Onboard a design partner to the dltHub background agents private preview. MUST use when the user asks 'how do I get started', 'set me up', 'what is this repo', 'what am I supposed to do', 'what are the steps', 'how do I deploy this', or opens this workspace for the first time. Covers prerequisites, workspace setup, model credentials, deploying, running the job-inspector agent on a failing pipeline, and pointers to write a custom agent. Do NOT use for writing an agent's prompt or output schema — read the docs listed below for that."
---

# Background agents private preview

Background agents are dltHub jobs that run an AI agent loop. They wake on events
(for example, a job failing) and write a structured result next to the run they
acted on. This workspace ships five example pipelines against the live
[Jaffle Shop API](https://jaffle-shop.dlthub.com/docs): one correct, four broken
in different ways. Use them as the substrate for the verified `job-inspector`
agent and for agents the partner writes themselves.

Private preview: expect rough edges. Log findings against the docs and the
tools — surface them to dltHub team.

## Docs

Fetch these before writing agent code; answer from them, not memory.

- https://dlt-issue-4448-docs.services4758.workers.dev/docs/devel/hub/agents.md — `run.agent()`, triggers, deploying, run results, guardrails
- https://dlt-issue-4448-docs.services4758.workers.dev/docs/devel/hub/agents/agent-definitions.md — writing a definition
- https://dlt-issue-4448-docs.services4758.workers.dev/docs/devel/hub/agents/job-inspector.md — the verified agent, read before declaring it

## Getting them set up

Work through these in order. All commands run with `uv run` and `--non-interactive`.

**Log in before touching the platform.** No `workspace`, `deploy`, `variable`
or `job` command until `dlthub login` in step 3. Run one earlier and it starts
a device flow by itself.

**You never handle the API key.** The commands that touch it in step 3 go to
the partner to run themselves. Do not ask them to paste it, do not put it in a
command you run, and do not write it to a file.

**1. Prerequisites.** `uv` on PATH and Python 3.12–3.14. If `uv` is missing,
point them at https://docs.astral.sh/uv/. A coding agent is already open —
that is you.

**2. Set up the workspace.** Follow this prompt end-to-end. Ask the partner
questions only where the prompt tells you to.

```text
Set up this directory for dltHub background agents. Use `uv run` and pass
`--non-interactive` to `dlthub` commands.

1. If there is no `.dlt/.workspace` file, run `uvx dlthub-init@latest`.
2. Add these dependencies to pyproject.toml and run `uv sync`:
   "dlt[hub]==1.30.1a0", "dlthub[mcp]", "dlthub-client>=0.28.5",
   "pydantic-ai-slim[anthropic,openai,google,mcp,spec]>=2.35.0", "aiohttp>=3.14.3"
3. Run `uv run dlthub ai toolkit install dlthub-platform --overwrite`, then
   `uv run dlthub ai status`, and fix any warnings.
4. Declare the `job-inspector` agent in `__deployment__.py` with an explicit
   trigger on the failed jobs: `job.fail:*`. Ask me which
   jobs to watch, or which pipeline to build first if there are none.

I'll configure the model key and endpoint myself. Never ask for them, put them
in a command, or write them to a file.
```

**3. Model and key — partner does this themselves.** Hand over both blocks
below and ask them to fill in the placeholders in their own editor and
terminal. Do not fill in any value for them, do not run these commands, and do
not ask what the values are — the key never enters this session, and the model
and endpoint are theirs to pick.

Ask them to add the model and endpoint to `.dlt/config.toml`. Every agent job
in the workspace uses them:

```toml
[agent]
model = "<provider:model>"        # e.g. "azure:<deployment>", "anthropic:claude-sonnet-4-5", "openai:gpt-5"
api_url = "<endpoint URL>"        # omit for providers with a fixed endpoint
api_version = "<api version>"     # Azure endpoints only, e.g. "2024-12-01-preview"
```

Then ask them to run these three lines in their own terminal, with their key
in place of `<PASTE_KEY_HERE>`:

```bash
export AGENT__API_KEY=<PASTE_KEY_HERE>
uv run dlthub login
uv run dlthub variable set AGENT__API_KEY --value "$AGENT__API_KEY" --secret --workspace
```

The `export` covers local runs; `variable set` stores the key as a workspace
secret because the platform runner cannot read their shell. If the workspace
is not connected yet, they run `uv run dlthub workspace connect` between
`login` and `variable set`.

**4. Deploy.**

```bash
uv run dlthub deploy
```

## What is in the workspace

`jaffle_shop/` runs against the live Jaffle Shop API. Fire them all with
`uv run dlthub job trigger tag:jaffle`.

| pipeline | outcome | the bug |
|---|---|---|
| `load_jaffle_correct` | 935 / 10 / 6 rows | the reference |
| `load_jaffle_bad_config` | **fails** | `base_url` on `/api/v2/`, 404 on the first request |
| `load_jaffle_bad_incremental` | **fails** | `cursor_path` on a field the API does not have |
| `load_jaffle_bad_pagination` | **green**, 100 of 935 rows | paginator reads `next` from the body; this API uses the `Link` header |
| `load_jaffle_bad_selector` | **green**, 0 of 6 rows | `data_selector` points at `data.results`; the API returns a bare array |

Two fail outright. The other two lose data without failing, so no job-status
trigger sees them at all — that is the class of problem worth writing a custom
agent for.

## Try the inspector

`job-inspector` wakes only when a job it watches fails. Trigger one of the
failing pipelines:

```bash
uv run dlthub run load_jaffle_bad_config
```

Read the diagnosis from either the failed run's page in the Web UI (it links
to the inspector run) or the **Agents** tab at
[app.dlthub.com](https://app.dlthub.com).

To read the inspector's transcript from the CLI:

```bash
uv run dlthub job logs job_inspector
```

Judge the diagnosis with the partner: is it right, and useful to someone who
has to act on it? Where does it fall short? Those are the findings worth
sending back.

## Customize or extend

Override the inspector's defaults in `__deployment__.py` — model, turn limit,
extra instructions — see the "Customize the job inspector" section of the docs
above.

To write a custom agent (for example, one that catches the silent-underload
pipelines the inspector cannot see), either:

- Write an `AGENT.md` with YAML frontmatter (tools, access, output schema) and
  a Markdown body as the system prompt, then declare it in `__deployment__.py`
  by its folder, or
- Write a Python function with `@run.agent`, where the docstring is the system
  prompt, parameters are inputs, and the return type is the output schema.

The `agents.md` doc listed above has both patterns end to end.
