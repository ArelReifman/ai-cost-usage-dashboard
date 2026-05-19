# AI Cost & Usage Intelligence Dashboard

A Streamlit dashboard for monitoring and optimizing AI API costs across teams and providers.

## Quick Start

```bash
pip install -r requirements.txt
python3 -m streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

## Live AI Advisor - Gemini

Set your Gemini API key to enable live AI-powered cost optimization recommendations:

```bash
export GEMINI_API_KEY="your_key_here"
python3 -m streamlit run app.py
```

When `GEMINI_API_KEY` is set, the AI Advisor uses Gemini 2.5 Flash (with automatic fallback to Gemini 2.0 Flash) to analyze the filtered dataset and return three structured recommendation cards - each with severity, finding, business impact, estimated opportunity, and recommended action.

If no API key is set, or if the Gemini API is temporarily unavailable, the dashboard shows deterministic fallback recommendations derived from the current dataset.

> **Never commit API keys. Use environment variables only.**

## Features

| Section | Details |
|---|---|
| **KPI Cards** | Total Cost · Requests · Tokens · Avg $/Req · Efficiency Score · Estimated Savings |
| **Filters** | Date range · Team · Provider · Model · Usage Type |
| **Cost Analysis** | Daily cost trend with 7-day MA · Cost by team · Top 20 models by spend · Cost by usage type |
| **Efficiency & Risk** | Efficiency score per team · Waste risk (% of premium models on trivial tasks) |
| **Top Users** | 15 most expensive users with waste percentage |
| **Recommendations** | Rule-based optimization findings with severity badges and action steps |
| **AI Advisor** | Live Gemini-powered recommendations as structured cards, or deterministic fallback insights |

## Providers

OpenAI · Anthropic · Google · xAI · Meta · Mistral · DeepSeek · Qwen · Amazon

## Data Schema (AGENT.md v1.0)

`data/ai_usage_mock.csv` contains 1,000 mock usage records following the validator agent schema:

| Field | Type | Description |
|---|---|---|
| `request_id` | UUID | Unique request identifier |
| `timestamp` | datetime | Request time |
| `team` | string | Engineering / Marketing / Sales / Product / Finance / HR / Legal |
| `user_id` | string | User identifier |
| `provider` | string | OpenAI / Anthropic / Google / xAI / Meta / Mistral / DeepSeek / Qwen / Amazon |
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
│   └── ai_usage_mock.csv   # 1,000-row mock dataset (9 providers, 44 models)
└── AI Agents Library/
    └── AGENT.md            # Data validator agent spec
```
