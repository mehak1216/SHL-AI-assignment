# Approach Document

## Overview

This submission implements a stateless conversational recommender for SHL assessments using FastAPI. The service exposes the required `GET /health` and `POST /chat` endpoints and adds a lightweight dashboard at `GET /` to make the system easier to review manually.

The agent is designed around a simple but robust policy:

- clarify when the user request is too vague
- retrieve and rank only from the SHL catalog
- refine recommendations using the full conversation history
- compare named SHL assessments using catalog-backed metadata
- refuse off-topic and prompt-injection requests

## Catalog And Retrieval

The code loads assessment records from a local catalog file. If `data/shl_catalog.json` exists, it is used as the primary catalog. Otherwise the app falls back to `data/shl_catalog.sample.json` for local development.

The intended production path is:

1. scrape the SHL Individual Test Solutions catalog
2. normalize each assessment into a structured local JSON record
3. serve recommendations only from that local record set

Each record contains:

- name
- URL
- test type
- description
- job levels
- languages
- duration
- remote testing flag
- adaptive flag
- tags

Retrieval is deterministic and catalog-grounded. The ranker scores assessments based on:

- role and domain keywords
- soft-skill cues such as stakeholder interaction or leadership
- requested assessment types such as technical, cognitive, or personality
- seniority hints
- language hints

When multiple assessment types are requested, the recommender diversifies the shortlist so the final results are not dominated by a single type.

## Prompting And Dialogue Policy

The service is stateless, so the full message history is sent on every `POST /chat` request. The agent reconstructs its working state from the request payload rather than storing server-side session state.

The conversation policy is:

- If the request is vague, ask one concise clarifying question.
- If enough context is available, produce a shortlist of 1 to 10 items.
- If the user refines constraints, re-rank using the updated full history.
- If the user asks to compare two assessments, answer from catalog fields rather than model memory.
- If the user asks something off-topic or attempts prompt injection, refuse and stay within scope.

To respect the evaluator turn budget, the agent stops asking repeated clarification questions near the end of the conversation and instead makes a best-effort grounded recommendation from the available context.

## Evaluation

The code includes both agent-level/API-level tests and an offline labeled evaluation harness in `scripts/evaluate_agent.py`.

Behavioral coverage includes:

- health endpoint contract
- chat endpoint schema compliance
- vague-query clarification
- grounded shortlist generation
- comparison without recommendations
- off-topic refusal
- exclusion refinements such as "no personality tests"
- best-effort behavior near the turn cap

The offline evaluator reads `data/evaluation_cases.json` and reports:

- `Recall@10` on shortlist cases to measure retrieval quality
- `Precision@10` as a recommendation relevance proxy
- groundedness pass rate by verifying every returned URL exists in the local SHL catalog
- schema pass rate
- behavior pass rate across clarify, shortlist, compare, and refuse scenarios

This gives the project a lightweight but concrete way to measure recommendation quality and regression risk even without access to the full private evaluation harness.

## What Did Not Work Well

The biggest limitation in this local environment was direct network access to the SHL website, so the repository currently includes a starter sample catalog and a bootstrap script for generating the full catalog on a machine with internet access.

The current ranking approach is intentionally deterministic and explainable, but it is less expressive than a richer semantic retrieval pipeline. If I had more time, I would add:

- stronger job-description parsing
- synonym expansion from real trace data
- evaluation against the official public conversation traces
- retrieval tuning against a broader Recall@10 benchmark
