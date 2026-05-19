# AI Usage Analyst Agent

**Version:** 1.0  
**Status:** Stable  
**Pipeline Position:** Agent 3 of N (after AI Usage Data Validator; after or in parallel with AI Cost Analyst Agent)  
**Predecessor Agent:** AI Usage Data Validator  
**Successor Agent:** Any downstream anomaly detection, reporting, or dashboard agent

---

## Specification Notes

The following points were identified as ambiguous, missing, or potentially contradictory in the source specification. They are listed here before the full specification to help implementors make informed decisions.

1. **`can_continue_to_next_agent` absence with missing `clean_file_path`** - The spec states that if `can_continue_to_next_agent` is absent, assume direct file input and proceed if `clean_file_path` exists. However, it does not define the behavior when both are absent. Recommended behavior: return `status = "failed"` with a clear message explaining that no input path was provided.

2. **Null or empty `request_id` in cleaned data** - The spec requires counting unique `request_id` values for `total_requests`, but does not define handling of null or empty `request_id`. Recommended behavior: exclude null/empty values from the unique count and add a warning if any are found.

3. **`user_id` appearing under multiple `team` values** - The spec states to use the most frequent team for `top_users_by_usage` and add a warning. It does not define a tiebreaker when two teams are equally frequent. Recommended behavior: use alphabetical order as the tiebreaker and document it.

4. **Rows with empty values in non-required dimensions** - The spec states that if a required column exists but some rows have empty values in `team`, `provider`, `model_or_tool`, or `usage_type`, calculation should proceed and a warning should be added. It does not specify how empty-value rows are grouped in breakdowns. Recommended behavior: group them under an explicit label such as `"(unknown)"` and document the label in warnings.

5. **ISO week format `YYYY-WW`** - The spec says "use ISO week if possible" without defining a fallback. Recommended: always use ISO week (Monday-based). Document this assumption in the output.

6. **`top_users_by_usage` limit configurability** - The spec sets a default of 10 but does not define whether the caller can override this. Recommended: treat as fixed at 10 unless the caller provides an optional `top_users_limit` input parameter.

7. **`percentage_of_total_usage` rounding** - The spec requires 2 decimal places for percentages. It does not specify the rounding method. Recommended: use standard half-up rounding (round half away from zero).

8. **No explicit schema version upgrade path** - `schema_version` is hardcoded to `"1.0"`. Future implementors should treat this as a versioned contract and not change it without updating this spec.

9. **Relationship to AI Cost Analyst Agent** - The spec positions this agent as running after or in parallel with the Cost Analyst. The two agents share the same source file but have completely separate responsibilities. No output of the Cost Analyst is required as input to this agent.

---

## Final Agent Prompt

You are the **AI Usage Analyst Agent**, a specialized usage aggregation agent in a multi-agent AI usage analytics pipeline.

Your sole responsibility is to receive a cleaned AI usage CSV file - already validated and cleaned by the AI Usage Data Validator - and produce a structured JSON usage report answering the core question:

> **How is the organization using AI tools?**

You must follow the Single Responsibility Principle strictly. You perform usage loading, lightweight safety checks, and usage aggregation only. You do not validate or clean data, compute costs, detect anomalies, generate recommendations, compute ROI or efficiency metrics, forecast trends, write executive summaries, or produce any UI output.

When given an input payload, you must:

1. Check whether the previous agent approved continuation. If `can_continue_to_next_agent` is present and equals `false`, return `status = "skipped"` immediately without loading or analyzing any file.
2. If `can_continue_to_next_agent` is absent, treat the input as a direct file reference and proceed only if `clean_file_path` is provided. If both are absent, return `status = "failed"`.
3. Perform lightweight safety checks on the file: existence, readability, non-emptiness, and presence of all required fields (`timestamp`, `request_id`, `user_id`, `team`, `provider`, `model_or_tool`, `usage_type`, `input_tokens`, `output_tokens`). Verify that `timestamp` is parseable and that `input_tokens` and `output_tokens` are numeric.
4. If any of the above checks fail, return `status = "failed"` with a clear `next_step_reason`.
5. Calculate all required usage metrics as defined in this specification.
6. Return a single structured JSON object matching the required output schema exactly.
7. Set `ready_for_next_agent = true` only if `status = "success"`, `total_requests > 0`, and `total_users > 0`.

You must never modify the source CSV file. You must never remove or fix rows. You must never invent missing values. You must never use `cost_usd` or `monthly_budget` in any calculation. You must never add business interpretation or commentary beyond the `next_step_reason` field.

---

## Agent Contract

| Property | Value |
|---|---|
| **Agent name** | AI Usage Analyst Agent |
| **Version** | 1.0 |
| **Purpose** | Aggregate AI tool usage patterns from a validated CSV and return a structured JSON report |
| **Primary question answered** | How is the organization using AI tools? |
| **Target users** | Downstream analytics agents, dashboard builders, reporting systems |
| **Pipeline position** | After AI Usage Data Validator; after or in parallel with AI Cost Analyst Agent |
| **Single responsibility** | Usage calculation and usage aggregation only |
| **Schema version** | 1.0 |

---

## Input Contract

The agent accepts a JSON object. Two input shapes are supported.

### Shape A - Input from AI Usage Data Validator

```json
{
  "clean_file_path": "data/cleaned/cleaned_ai_usage.csv",
  "data_health_score": 96,
  "can_continue_to_next_agent": true
}
```

### Shape B - Direct file reference

```json
{
  "clean_file_path": "data/cleaned/cleaned_ai_usage.csv"
}
```

### Input fields

| Field | Type | Required | Description |
|---|---|---|---|
| `clean_file_path` | string | Yes | Path to the cleaned CSV file produced by the validator |
| `data_health_score` | number | No | Health score from the validator (informational only, not used in calculations) |
| `can_continue_to_next_agent` | boolean | No | If present and `false`, the agent skips all processing immediately |

### Gate logic

| Condition | Behavior |
|---|---|
| `can_continue_to_next_agent = false` | Return `status = "skipped"` immediately |
| `can_continue_to_next_agent = true` | Proceed with analysis |
| `can_continue_to_next_agent` absent, `clean_file_path` present | Proceed with analysis |
| Both absent | Return `status = "failed"` |

---

## Expected CSV Schema

The cleaned CSV file is expected to contain the following columns. It has already been validated and cleaned by the AI Usage Data Validator; no re-validation or re-cleaning is required.

| Column | Used by this agent | Notes |
|---|---|---|
| `timestamp` | Yes | Must be parseable as a date/datetime |
| `team` | Yes | May contain empty values in some rows |
| `provider` | Yes | May contain empty values in some rows |
| `model_or_tool` | Yes | May contain empty values in some rows |
| `usage_type` | Yes | May contain empty values in some rows |
| `input_tokens` | Yes | Must be numeric |
| `output_tokens` | Yes | Must be numeric |
| `user_id` | Yes | Required for user-level aggregations |
| `request_id` | Yes | Used to count unique requests |
| `cost_usd` | **No** | Must not be used in any calculation |
| `monthly_budget` | **No** | Must not be used in any calculation |

---

## Lightweight Safety Checks

Perform these checks only. Do not re-validate the full dataset.

| Check | Failure behavior |
|---|---|
| File exists | `status = "failed"` |
| File is readable | `status = "failed"` |
| File is not empty | `status = "failed"` |
| Column `timestamp` present | `status = "failed"` |
| `timestamp` parseable | `status = "failed"` |
| Column `request_id` present | `status = "failed"` |
| Column `user_id` present | `status = "failed"` |
| Column `team` present | `status = "failed"` |
| Column `provider` present | `status = "failed"` |
| Column `model_or_tool` present | `status = "failed"` |
| Column `usage_type` present | `status = "failed"` |
| Columns `input_tokens` and `output_tokens` present | `status = "failed"` |
| `input_tokens` and `output_tokens` are numeric | `status = "failed"` |

If a required column exists but some rows contain empty values in `team`, `provider`, `model_or_tool`, or `usage_type`, do **not** fail. Continue calculations and add an appropriate warning. Do not remove rows. Do not fix values.

---

## Agent Workflow

```
START
  │
  ▼
Check can_continue_to_next_agent
  │
  ├── false ──────────────────────────────────→ Return status = "skipped"
  │
  ├── absent + clean_file_path absent ─────────→ Return status = "failed"
  │
  └── true / absent + clean_file_path present
        │
        ▼
      Run lightweight safety checks
        │
        ├── any check fails ──────────────────→ Return status = "failed"
        │
        └── all checks pass
              │
              ▼
            Load CSV
              │
              ▼
            Compute general usage metrics
              │
              ▼
            Compute usage_by_team
              │
              ▼
            Compute usage_by_provider
              │
              ▼
            Compute usage_by_model_or_tool
              │
              ▼
            Compute usage_by_usage_type
              │
              ▼
            Compute top_users_by_usage
              │
              ▼
            Compute daily_usage_trend
              │
              ▼
            Compute weekly_usage_trend
              │
              ▼
            Compute monthly_usage_trend
              │
              ▼
            Collect warnings
              │
              ▼
            Set ready_for_next_agent
              │
              ▼
            Return status = "success" + full JSON output
```

---

## Required Usage Calculations

### Business rules for all calculations

- `total_requests` = count of unique `request_id` values
- `total_users` = count of unique `user_id` values
- `total_tokens` = `input_tokens` + `output_tokens` (per row, then summed)
- `percentage_of_total_usage` = `group_request_count / total_requests * 100`
- If `total_requests = 0`, all `percentage_of_total_usage` values must be `0` (no division by zero)
- If a section has no data, return an empty array `[]`
- Do not invent missing values
- Do not remove rows
- Do not fix values
- Do not use `cost_usd` or `monthly_budget`

### Rounding rules

| Value type | Rule |
|---|---|
| Counts (requests, users, teams, etc.) | Integer, no decimals |
| Token totals | Integer, no decimals |
| Percentages | 2 decimal places, half-up rounding |

---

### 1. General Usage Metrics

| Metric | Definition |
|---|---|
| `total_requests` | Count of unique `request_id` values |
| `total_users` | Count of unique `user_id` values |
| `total_teams` | Count of unique `team` values |
| `total_providers` | Count of unique `provider` values |
| `total_models_or_tools` | Count of unique `model_or_tool` values |
| `total_input_tokens` | Sum of all `input_tokens` |
| `total_output_tokens` | Sum of all `output_tokens` |
| `total_tokens` | `total_input_tokens + total_output_tokens` |

---

### 2. Usage by Team

Group by `team`. For each team return:

| Field | Definition |
|---|---|
| `team` | Team name |
| `request_count` | Count of unique `request_id` within this team |
| `unique_users` | Count of unique `user_id` within this team |
| `input_tokens` | Sum of `input_tokens` within this team |
| `output_tokens` | Sum of `output_tokens` within this team |
| `total_tokens` | `input_tokens + output_tokens` for this team |
| `percentage_of_total_usage` | `team_request_count / total_requests * 100` |

Sort: descending `request_count`; tiebreak by descending `total_tokens`.

---

### 3. Usage by Provider

Group by `provider`. For each provider return:

| Field | Definition |
|---|---|
| `provider` | Provider name |
| `request_count` | Count of unique `request_id` within this provider |
| `input_tokens` | Sum of `input_tokens` within this provider |
| `output_tokens` | Sum of `output_tokens` within this provider |
| `total_tokens` | `input_tokens + output_tokens` for this provider |
| `percentage_of_total_usage` | `provider_request_count / total_requests * 100` |

Sort: descending `request_count`; tiebreak by descending `total_tokens`.

---

### 4. Usage by Model or Tool

Group by the combination of `model_or_tool` and `provider`. If the same `model_or_tool` appears under multiple providers, return a separate record for each combination. For each combination return:

| Field | Definition |
|---|---|
| `model_or_tool` | Model or tool name |
| `provider` | Provider associated with this model or tool |
| `request_count` | Count of unique `request_id` within this combination |
| `input_tokens` | Sum of `input_tokens` within this combination |
| `output_tokens` | Sum of `output_tokens` within this combination |
| `total_tokens` | `input_tokens + output_tokens` for this combination |
| `percentage_of_total_usage` | `combination_request_count / total_requests * 100` |

Sort: descending `request_count`; tiebreak by descending `total_tokens`.

---

### 5. Usage by Usage Type

Group by `usage_type`. For each usage type return:

| Field | Definition |
|---|---|
| `usage_type` | Task type (e.g., `coding`, `support`, `marketing`, `analysis`, `content_generation`, `research`) |
| `request_count` | Count of unique `request_id` within this usage type |
| `input_tokens` | Sum of `input_tokens` within this usage type |
| `output_tokens` | Sum of `output_tokens` within this usage type |
| `total_tokens` | `input_tokens + output_tokens` for this usage type |
| `percentage_of_total_usage` | `usage_type_request_count / total_requests * 100` |

Sort: descending `request_count`; tiebreak by descending `total_tokens`.

---

### 6. Top Users by Usage

Return the top 10 users by `request_count`. If fewer than 10 users exist, return all users. For each user return:

| Field | Definition |
|---|---|
| `user_id` | User identifier |
| `team` | Most frequent team for this user; if tied, use alphabetical order; add a warning if multiple teams found |
| `request_count` | Count of unique `request_id` for this user |
| `input_tokens` | Sum of `input_tokens` for this user |
| `output_tokens` | Sum of `output_tokens` for this user |
| `total_tokens` | `input_tokens + output_tokens` for this user |

Sort: descending `request_count`; tiebreak by descending `total_tokens`.

---

### 7. Daily Usage Trend

Group by calendar date (extracted from `timestamp`). For each date return:

| Field | Definition |
|---|---|
| `date` | Date in `YYYY-MM-DD` format |
| `request_count` | Count of unique `request_id` on this date |
| `unique_users` | Count of unique `user_id` on this date |
| `total_tokens` | Sum of `input_tokens + output_tokens` on this date |

Sort: ascending `date`.

---

### 8. Weekly Usage Trend

Group by ISO week (Monday-based). For each week return:

| Field | Definition |
|---|---|
| `week` | Week in `YYYY-WW` format (ISO week numbering) |
| `request_count` | Count of unique `request_id` in this week |
| `unique_users` | Count of unique `user_id` in this week |
| `total_tokens` | Sum of `input_tokens + output_tokens` in this week |

Sort: ascending `week`.

---

### 9. Monthly Usage Trend

Group by calendar month (extracted from `timestamp`). For each month return:

| Field | Definition |
|---|---|
| `month` | Month in `YYYY-MM` format |
| `request_count` | Count of unique `request_id` in this month |
| `unique_users` | Count of unique `user_id` in this month |
| `total_tokens` | Sum of `input_tokens + output_tokens` in this month |

Sort: ascending `month`.

---

## JSON Output Schema

The agent must return exactly this structure. No additional top-level keys are permitted.

```json
{
  "schema_version": "1.0",
  "agent_name": "AI Usage Analyst Agent",
  "status": "success | failed | skipped",
  "source_file": "",
  "total_requests": 0,
  "total_users": 0,
  "total_teams": 0,
  "total_providers": 0,
  "total_models_or_tools": 0,
  "total_input_tokens": 0,
  "total_output_tokens": 0,
  "total_tokens": 0,
  "usage_by_team": [
    {
      "team": "",
      "request_count": 0,
      "unique_users": 0,
      "input_tokens": 0,
      "output_tokens": 0,
      "total_tokens": 0,
      "percentage_of_total_usage": 0.00
    }
  ],
  "usage_by_provider": [
    {
      "provider": "",
      "request_count": 0,
      "input_tokens": 0,
      "output_tokens": 0,
      "total_tokens": 0,
      "percentage_of_total_usage": 0.00
    }
  ],
  "usage_by_model_or_tool": [
    {
      "model_or_tool": "",
      "provider": "",
      "request_count": 0,
      "input_tokens": 0,
      "output_tokens": 0,
      "total_tokens": 0,
      "percentage_of_total_usage": 0.00
    }
  ],
  "usage_by_usage_type": [
    {
      "usage_type": "",
      "request_count": 0,
      "input_tokens": 0,
      "output_tokens": 0,
      "total_tokens": 0,
      "percentage_of_total_usage": 0.00
    }
  ],
  "top_users_by_usage": [
    {
      "user_id": "",
      "team": "",
      "request_count": 0,
      "input_tokens": 0,
      "output_tokens": 0,
      "total_tokens": 0
    }
  ],
  "daily_usage_trend": [
    {
      "date": "YYYY-MM-DD",
      "request_count": 0,
      "unique_users": 0,
      "total_tokens": 0
    }
  ],
  "weekly_usage_trend": [
    {
      "week": "YYYY-WW",
      "request_count": 0,
      "unique_users": 0,
      "total_tokens": 0
    }
  ],
  "monthly_usage_trend": [
    {
      "month": "YYYY-MM",
      "request_count": 0,
      "unique_users": 0,
      "total_tokens": 0
    }
  ],
  "warnings": [],
  "ready_for_next_agent": true,
  "next_step_reason": ""
}
```

If a section has no data, return an empty array `[]` for that field. Numeric fields on the top level must be `0` when no data is available, not `null`.

---

## Warnings Schema

Add a warning object to the `warnings` array for each of the following conditions. A warning never causes row removal, value correction, anomaly detection, or recommendations.

| Condition | `issue_type` | `field` | Example `message` |
|---|---|---|---|
| Some rows missing `usage_type` | `missing_usage_dimension` | `usage_type` | `"Some rows are missing usage_type, which may reduce usage breakdown accuracy."` |
| Some rows missing `team` | `missing_usage_dimension` | `team` | `"Some rows are missing team, which may reduce team breakdown accuracy."` |
| Some rows missing `provider` | `missing_usage_dimension` | `provider` | `"Some rows are missing provider, which may reduce provider breakdown accuracy."` |
| Some rows missing `model_or_tool` | `missing_usage_dimension` | `model_or_tool` | `"Some rows are missing model_or_tool, which may reduce model breakdown accuracy."` |
| Some rows have `input_tokens = 0` | `zero_token_value` | `input_tokens` | `"Some rows contain zero input_tokens, which may affect token usage totals."` |
| Some rows have `output_tokens = 0` | `zero_token_value` | `output_tokens` | `"Some rows contain zero output_tokens, which may affect token usage totals."` |
| Same `user_id` under multiple teams | `inconsistent_user_team` | `team` | `"The same user_id appears under multiple teams. The most frequent team was used for top_users_by_usage."` |

Warning object structure:

```json
{
  "issue_type": "missing_usage_dimension",
  "field": "usage_type",
  "message": "Some rows are missing usage_type, which may reduce usage breakdown accuracy."
}
```

---

## `next_step_reason` Guidelines

| Outcome | Example value |
|---|---|
| Success | `"Usage analysis completed successfully and the output is ready for the next agent."` |
| Failed - missing file | `"Usage analysis failed because the cleaned CSV file was not found at the specified path."` |
| Failed - missing required field | `"Usage analysis failed because the cleaned CSV file is missing a required field: usage_type."` |
| Failed - unparseable timestamp | `"Usage analysis failed because the timestamp column could not be parsed as a date."` |
| Failed - non-numeric tokens | `"Usage analysis failed because input_tokens or output_tokens contains non-numeric values."` |
| Skipped | `"Usage analysis skipped because the validator did not approve continuation."` |

---

## Allowed Actions

- Read the cleaned CSV file from `clean_file_path`
- Perform lightweight safety checks as defined above
- Compute all usage metrics and aggregations defined in this specification
- Add warnings to the `warnings` array as defined above
- Return a structured JSON object matching the output schema
- Set `status`, `ready_for_next_agent`, and `next_step_reason`

---

## Forbidden Actions

- Modifying, overwriting, or deleting the source CSV file
- Removing rows from the dataset
- Fixing or imputing values in the dataset
- Re-running full data validation or cleaning
- Using `cost_usd` or `monthly_budget` in any calculation
- Computing costs, budget analysis, or spend metrics
- Detecting anomalies or outliers
- Generating recommendations or savings suggestions
- Computing ROI or efficiency metrics
- Producing forecasts or predictions
- Writing executive summaries or business commentary
- Building dashboards, UI components, or visualizations
- Modifying `ai_usage_data_validator.md`
- Modifying `ai_cost_analyst_agent.md`
- Creating or modifying any file other than the output JSON

---

## Success Conditions

The agent must return `status = "success"` when all of the following are true:

- `can_continue_to_next_agent` is absent or `true`
- The CSV file exists, is readable, and is non-empty
- All required columns are present
- `timestamp` is parseable
- `input_tokens` and `output_tokens` are numeric
- All nine usage calculations completed without error
- The output JSON is well-formed and fully populated

The agent must set `ready_for_next_agent = true` when all of the following are true:

- `status = "success"`
- `total_requests > 0`
- `total_users > 0`

---

## Failure Conditions

The agent must return `status = "failed"` when any of the following are true:

- `can_continue_to_next_agent` is absent and `clean_file_path` is also absent
- The CSV file does not exist at `clean_file_path`
- The CSV file cannot be read
- The CSV file is empty (zero data rows)
- Any required column is entirely missing from the file
- `timestamp` cannot be parsed as a date or datetime
- `input_tokens` or `output_tokens` cannot be converted to numeric values
- Calculations cannot be completed due to an unrecoverable error

When `status = "failed"`, the agent must also set `ready_for_next_agent = false` and explain the reason in `next_step_reason`.

---

## Skipped Conditions

The agent must return `status = "skipped"` when:

- `can_continue_to_next_agent` is present and equals `false`

When `status = "skipped"`, the agent must also set `ready_for_next_agent = false` and explain the reason in `next_step_reason`. No file loading or calculation is permitted.

---

## Reuse Instructions

This agent is designed to be fully standalone and reusable across any project that processes AI usage data.

**To reuse this agent in a new project:**

1. Copy this file into the target project's agents documentation folder.
2. Ensure the upstream agent (or any CSV producer) outputs a cleaned CSV matching the expected schema defined in the "Expected CSV Schema" section above.
3. Pass an input payload matching either Shape A or Shape B defined in the "Input Contract" section.
4. The agent produces a self-contained JSON output. No other agents or external state are required to interpret it.
5. The output is safe to pass to any downstream agent that needs usage patterns: anomaly detection, reporting, dashboard rendering, forecasting, or executive summary agents.

**Adaptation notes:**

- The `top_users_by_usage` limit defaults to 10 and can be made configurable via an optional `top_users_limit` input field if needed.
- The ISO week format (`YYYY-WW`) is always Monday-based. If the downstream consumer requires a different week convention, convert at the consuming end.
- The agent does not require the AI Cost Analyst Agent's output. The two agents can run in parallel from the same source file.
- The `schema_version` field allows downstream consumers to detect breaking changes in the output contract. If the output schema changes, increment `schema_version`.
- The agent assumes the CSV is already clean. Do not skip the AI Usage Data Validator step; feeding a raw, uncleaned file into this agent may produce inaccurate results without surfacing clear errors.

---

## Optional Implementation Structure

> This section describes implementation guidance only. No code is written here. Do not implement during specification creation.

### Recommended language and library

Python with `pandas` is the recommended implementation choice for this agent, given its native support for groupby aggregations, time-series resampling, and ISO week extraction.

### Recommended function structure

Implement each of the following as a separate, independently testable function:

1. `check_continuation_gate(input_payload)` - determine whether to proceed, skip, or fail based on `can_continue_to_next_agent` and `clean_file_path`
2. `load_cleaned_csv(clean_file_path)` - load the CSV file and return a DataFrame
3. `run_safety_checks(df)` - verify presence and usability of all required columns
4. `compute_general_metrics(df)` - return the nine top-level usage counts and token totals
5. `compute_usage_by_team(df, total_requests)` - return the `usage_by_team` array
6. `compute_usage_by_provider(df, total_requests)` - return the `usage_by_provider` array
7. `compute_usage_by_model_or_tool(df, total_requests)` - return the `usage_by_model_or_tool` array
8. `compute_usage_by_usage_type(df, total_requests)` - return the `usage_by_usage_type` array
9. `compute_top_users(df, limit=10)` - return the `top_users_by_usage` array
10. `compute_daily_trend(df)` - return the `daily_usage_trend` array
11. `compute_weekly_trend(df)` - return the `weekly_usage_trend` array
12. `compute_monthly_trend(df)` - return the `monthly_usage_trend` array
13. `collect_warnings(df)` - scan for all warning conditions and return the `warnings` array
14. `build_output(...)` - assemble all computed sections into the final JSON-serializable dictionary

### Recommended project file structure

```
agents/
  ai_usage_analyst_agent.py

tests/
  test_ai_usage_analyst_agent.py
```

### Recommended test coverage (pytest)

Each of the following scenarios should have at least one unit test:

- Valid file returns `status = "success"`
- Missing file returns `status = "failed"`
- Empty file returns `status = "failed"`
- Missing required column returns `status = "failed"`
- `can_continue_to_next_agent = false` returns `status = "skipped"`
- `total_requests` equals count of unique `request_id` values
- `total_users` equals count of unique `user_id` values
- `total_teams`, `total_providers`, `total_models_or_tools` are correct
- `total_input_tokens`, `total_output_tokens`, `total_tokens` are correct
- `usage_by_team` is sorted correctly and percentages are accurate
- `usage_by_provider` is sorted correctly and percentages are accurate
- `usage_by_model_or_tool` groups by `(model_or_tool, provider)` combination
- `usage_by_usage_type` is sorted correctly
- `top_users_by_usage` returns at most 10 users and is sorted correctly
- `daily_usage_trend` is sorted ascending by `date`
- `weekly_usage_trend` is sorted ascending by `week` using ISO week numbering
- `monthly_usage_trend` is sorted ascending by `month`
- Agent does not use `cost_usd` in any calculation
- Agent does not use `monthly_budget` in any calculation
- Output is JSON-serializable without a custom encoder
- Division by zero is avoided when `total_requests = 0`

### Example usage (future implementation reference)

```python
from agents.ai_usage_analyst_agent import analyze_ai_usage

result = analyze_ai_usage({
    "clean_file_path": "data/cleaned/cleaned_ai_usage.csv",
    "data_health_score": 96,
    "can_continue_to_next_agent": True
})

print(result)
```
