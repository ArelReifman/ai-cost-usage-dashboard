# Preparation Questions — AI Cost & Usage Intelligence Dashboard

---

## 1. Which metrics did you choose, and why?

The dashboard surfaces six KPIs, each chosen to answer a specific business question:

| Metric | Business question it answers |
|---|---|
| **Total Cost** | How much are we spending on AI this period? |
| **Total Requests** | How heavily is AI being used across the org? |
| **Total Tokens** | Where is the computational load concentrated? |
| **Avg Cost / Request** | Are we getting reasonable unit economics? |
| **Efficiency Score** | Are teams using the right model for each task? |
| **Estimated Savings** | How much could we recover immediately? |

Beyond the headline KPIs, I added two operational metrics that matter most for cost control:

- **Waste Risk** — the percentage of requests where a premium-tier model (e.g. GPT-5.5 Pro, Claude Opus) was used for a trivial task like embedding or search. This is the most actionable signal for quick savings.
- **Model Efficiency Score per Team** — a team-level score (0–100%) derived from waste rate, making it easy to identify which teams need routing guidance rather than budget cuts.

The goal was to give a finance leader, engineering manager, and CTO different entry points into the same dataset — headline cost visibility for finance, efficiency gaps for engineering, and strategic risk for leadership.

---

## 2. Which AI feature did you build, and what problem does it solve?

**Problem:** Dashboards show what happened, but not what to do about it. A cost analyst looking at the data still needs to manually synthesize patterns across teams, models, and usage types to produce actionable recommendations — a process that takes time and expertise.

**Solution:** A live AI Advisor powered by the Gemini API. When the user clicks "Generate live AI recommendations," the advisor:

1. Builds a compact aggregated summary from the currently filtered dataset (team costs, top 10 models by spend, provider share, waste flags, legacy model usage, top expensive users) — no raw CSV rows are sent.
2. Sends it to Gemini 2.5 Flash with a strict JSON schema prompt, asking for exactly three prioritized recommendations.
3. Parses the JSON response and renders each recommendation as a structured card showing: severity, finding, business impact, estimated opportunity, and recommended action.

**Resilience built in:**
- Automatic model fallback: if Gemini 2.5 Flash is overloaded or unavailable, the advisor retries with Gemini 2.0 Flash.
- If both models fail, or if no API key is configured, the dashboard shows three deterministic rule-based recommendations derived from the same dataset — so the advisor is always useful, never broken.
- No API key is ever hardcoded or logged.

The feature bridges the gap between "here is your data" and "here is what you should do this week."

---

## 3. What would you do differently with another week of work?

**Data & accuracy**
- Replace the mock CSV with a proper data pipeline pulling from real API billing exports (OpenAI usage API, Anthropic usage API, Google Cloud billing).
- Add a date-partitioned data store so the dashboard can handle months of history without loading everything into memory.

**Product**
- Add user-level drill-down: click a team to see individual users, click a user to see their model and usage-type breakdown.
- Add budget tracking: show each team's current spend as a percentage of their monthly budget with a burn-rate projection.
- Add anomaly detection: flag days or users where spend spiked more than 2σ above their baseline.

**AI Advisor**
- Cache Gemini responses for a given filter state (TTL ~1 hour) to avoid redundant API calls and reduce latency.
- Let the user ask follow-up questions in a chat interface against the same dataset context.
- Add a "compare periods" mode so the advisor can identify whether efficiency is improving or degrading week-over-week.

**Engineering**
- Move to a proper backend (FastAPI) with a database, so multiple users can access the dashboard concurrently without each loading the full dataset.
- Add authentication so teams can only see their own data.

---

## 4. How would you obtain real data and scale this in a production environment?

**Data ingestion**

Most major AI providers expose usage and billing APIs:
- OpenAI: `/v1/usage` endpoint, or export from the billing dashboard
- Anthropic: usage API (available to enterprise customers)
- Google Vertex AI / Gemini: Cloud Billing export to BigQuery
- Other providers (xAI, Mistral, DeepSeek): webhook callbacks or gateway-level logging

For providers without native usage APIs, an **AI gateway** (LiteLLM Proxy, Portkey, or a custom reverse proxy) sits in front of all model calls, logs every request with team, user, model, token counts, and cost, and writes to a central store — regardless of which underlying provider is used.

**Storage & processing**
- Raw events → append-only log (Kafka or a managed equivalent) for real-time ingestion
- Aggregated daily/weekly summaries → PostgreSQL or BigQuery for the dashboard to query
- A lightweight ETL job (Airflow or a scheduled Cloud Function) runs nightly to enrich and roll up the raw logs

**Dashboard scaling**
- Replace Streamlit's in-process data loading with pre-aggregated queries against the database — the dashboard never touches raw rows
- Deploy Streamlit (or migrate to a React frontend backed by FastAPI) behind an internal load balancer with SSO authentication
- Add row-level security so each team only sees their own spend data

**Governance**
- Enforce budget alerts via the gateway: block or warn when a team exceeds a configurable threshold mid-month
- Publish a model selection policy (which model tier is approved for which task class) and measure compliance through the efficiency score metric already in the dashboard
