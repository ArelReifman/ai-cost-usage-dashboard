# AI Cost & Usage Intelligence Dashboard

A Streamlit dashboard for monitoring and optimizing AI API costs across teams and providers.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

## Optional — Live AI Advisor

Set your Anthropic API key to enable Claude-powered cost optimization insights:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
streamlit run app.py
```

## Features

| Section | Details |
|---|---|
| **KPI Cards** | Total Cost · Requests · Tokens · Avg $/Req · Efficiency Score · Estimated Savings |
| **Filters** | Date range · Team · Provider · Model · Usage Type |
| **Cost Analysis** | Daily cost trend with 7-day MA · Cost by team · Cost by model · Cost by usage type |
| **Efficiency & Risk** | Efficiency score per team · Waste risk (% of premium models on trivial tasks) |
| **Top Users** | 15 most expensive users with waste percentage |
| **Recommendations** | 5 rule-based optimization rules with severity and action steps |
| **AI Advisor** | Live Claude API or illustrative mock insights |

## Data Schema (AGENT.md v1.0)

The mock CSV at `data/ai_usage_mock.csv` follows the validator agent schema:

| Field | Type | Description |
|---|---|---|
| `request_id` | UUID | Unique request identifier |
| `timestamp` | datetime | Request time |
| `team` | string | Engineering / Marketing / Sales / Product / Finance / HR / Legal |
| `user_id` | string | User identifier |
| `provider` | string | OpenAI / Anthropic / Google / Azure |
| `model_or_tool` | string | Model name |
| `usage_type` | string | completion / embedding / chat / summarization / code-gen / analysis / search |
| `input_tokens` | int | Input token count |
| `output_tokens` | int | Output token count |
| `cost_usd` | float | Request cost in USD |
| `monthly_budget` | int | Team monthly budget in USD |

## Regenerate Mock Data

```bash
python3 generate_data.py
```

The app auto-generates data on first run if `data/ai_usage_mock.csv` is missing.

## Project Structure

```
.
├── app.py                  # Streamlit dashboard
├── generate_data.py        # Mock data generator
├── requirements.txt
├── README.md
├── data/
│   └── ai_usage_mock.csv   # 500-row mock dataset
└── AI Agents Library/
    └── AGENT.md            # Data validator agent spec
```
