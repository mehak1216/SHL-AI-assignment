# SHL Conversational Assessment Recommender

FastAPI service for the SHL AI Intern take-home assignment.

## Assignment coverage

This repository covers the core product requirements from `SHL_AI_Intern_Assignment.pdf`.

| PDF requirement | Status | Notes |
| --- | --- | --- |
| Use the SHL `Individual Test Solutions` catalog only | Covered | `data/shl_catalog.json` is checked in and contains 254 SHL catalog items. |
| Expose `GET /health` | Covered | Returns `{"status":"ok"}` with HTTP 200. |
| Expose stateless `POST /chat` | Covered | Request takes the full `messages` history; the server stores no conversation state. |
| Clarify vague requests | Covered | The agent asks one concise follow-up when context is missing. |
| Recommend 1 to 10 assessments with name and SHL URL | Covered | Responses only emit catalog-grounded recommendations. |
| Refine when the user changes constraints | Covered | New user constraints are applied across the whole message history. |
| Compare assessments | Covered | The agent supports catalog-grounded comparison replies without returning a shortlist. |
| Stay in scope and refuse prompt injection / off-topic asks | Covered | The agent refuses legal, salary, and prompt-injection requests. |
| Respect the evaluator turn budget | Covered | The agent stops over-clarifying near the 8-turn cap and switches to best-effort recommendations. |
| Approach document | Covered | See `APPROACH.md`. |
| Public deployed API URL | Not included in repo | This is a submission-time deployment step, not a source-code artifact. |

The assignment-required endpoints are `GET /health` and `POST /chat`.
`GET /` is included only as a convenience demo surface and is not required by the evaluator.

## What it does

- exposes `GET /health` and `POST /chat`
- keeps the API stateless by reading the full conversation history on every call
- asks clarifying questions for vague requests
- returns grounded SHL recommendations with catalog URLs only
- handles refinements and assessment comparisons
- refuses off-topic and prompt-injection requests
- includes a small browser dashboard for manual review

## Run locally

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

## Streamlit deployment

If you want a Streamlit Cloud demo instead of deploying the FastAPI API service, use:

- main file path: `streamlit_app.py`

This Streamlit app reuses the same recommendation logic, but it is a demo wrapper rather than the assignment's required FastAPI `/health` and `/chat` deployment target.

## API contract

Request schema:

```json
{
  "messages": [
    {"role": "user", "content": "Hiring a Java developer who works with stakeholders"},
    {"role": "assistant", "content": "What seniority level is this role?"},
    {"role": "user", "content": "Mid-level, around 4 years. Add personality tests too."}
  ]
}
```

Response schema:

```json
{
  "reply": "Based on the role you described, I'd shortlist 5 SHL assessments...",
  "recommendations": [
    {
      "name": "Java 8 (New)",
      "url": "https://www.shl.com/solutions/products/product-catalog/view/java-8-new/",
      "test_type": "K"
    }
  ],
  "end_of_conversation": false
}
```

Notes:

- `recommendations` is empty while the agent is clarifying, comparing, or refusing.
- `recommendations` contains 1 to 10 items when the agent commits to a shortlist.
- `end_of_conversation` flips to `true` only once the agent believes the recommendation task is complete.

## Catalog data

The app loads:

1. `data/shl_catalog.json` if present
2. otherwise `data/shl_catalog.sample.json`

This repository already includes a populated `data/shl_catalog.json` with 254 SHL catalog entries, so the agent is not limited to the small fallback sample during normal use.

Use `scripts/bootstrap_catalog.py` on a machine with internet access to rebuild the live `Individual Test Solutions` catalog.

Recommended command:

```bash
python scripts/bootstrap_catalog.py --max-start 240 --delay-seconds 0.5
```

The bootstrap script supports:

- browser-like headers to reduce SHL blocking
- resumable checkpointing in `data/shl_catalog.checkpoint.json`
- configurable page depth
- configurable delay between requests

## Dashboard

Opening `http://127.0.0.1:8000/` shows an interactive demo interface that:

- lets an interviewer type prompts directly instead of using Postman
- preserves the full stateless conversation history in the browser
- renders the latest structured shortlist with clickable SHL URLs
- includes one-click demo scenarios for vague queries, refinement, and comparison

## Testing

Run the automated checks with:

```bash
python -m pytest tests
```

The tests cover:

- `/health` readiness behavior
- `/chat` response schema
- clarification on vague prompts
- grounded recommendations
- comparison behavior
- off-topic refusal
- prompt-injection refusal
- refinement constraints like excluding personality tests
- best-effort behavior near the evaluator turn cap

## Evaluation

Run the offline evaluation harness with:

```bash
python scripts/evaluate_agent.py
```

It evaluates labeled conversation cases in `data/evaluation_cases.json` and reports:

- `Recall@10` for shortlist cases as a retrieval-quality metric
- `Precision@10` as a recommendation relevance proxy
- groundedness pass rate by checking that all returned URLs exist in the SHL catalog
- schema pass rate for response-shape correctness
- behavior pass rate across clarification, refinement, comparison, refusal, and turn-cap scenarios

You can point the script at another labeled set with:

```bash
python scripts/evaluate_agent.py --cases data/evaluation_cases.json
```

## Submission checklist

- Deploy the FastAPI service and keep `/health` and `/chat` reachable.
- Submit the deployed base URL.
- Submit `APPROACH.md` as the 2-page design note.
- Regenerate the catalog before final submission if you want the freshest SHL scrape.
