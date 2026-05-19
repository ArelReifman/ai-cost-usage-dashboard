# AI Cost Analyst Agent

**Version:** 1.0  
**Status:** Stable  
**Pipeline Position:** Agent 2 of N  
**Predecessor Agent:** AI Usage Data Validator  
**Successor Agent:** Any downstream analytics, anomaly detection, or reporting agent

---

## Specification Notes

The following points were identified as ambiguous, missing, or potentially contradictory in the source specification. They are listed here before the full specification to help implementors make informed decisions.

1. **`can_continue_to_next_agent` absence vs. explicit `false`** - The spec states that if the field is absent, the agent should assume direct file input and proceed if `clean_file_path` exists. However, it does not clarify what should happen if `clean_file_path` is also absent. Recommended behavior: return `status = "failed"` with a clear message.

2. **Deduplication of `request_id` for `total_requests`** - The spec requires counting unique `request_id` values. It does not specify how to handle null or empty `request_id` values in cleaned data. Recommended behavior: exclude null/empty values from the unique count and add a warning if any are found.

3. **`average_daily_cost_usd` when only one date exists** - The formula divides by number of unique dates. If only one date exists, the result equals `total_cost_usd`. This is mathematically valid and should not cause an error.

4. **`top_users_by_cost` default of 10** - The spec says "default: Top 10" but does not define whether this is configurable via input. Treat as fixed at 10 unless the caller overrides it via an optional `top_users_limit` input parameter.

5. **ISO week format `YYYY-WW`** - The spec says "use ISO week if possible" without defining a fallback. Recommended: always use ISO week (Monday-based). Document this assumption in the output.

6. **`monthly_budget` granularity** - The spec states `monthly_budget` is at the team level, but does not clarify what to do if the same team appears with different `monthly_budget` values across rows. Recommended behavior: use the most common (mode) non-null value per team, and add a warning if inconsistency is detected.

7. **`percentage_of_total_cost` when `total_cost_usd = 0`** - The spec states return `0`. This is consistent with the division-by-zero guard rule defined elsewhere.

8. **No explicit schema version upgrade path** - `schema_version` is hardcoded to `"1.0"`. Future implementors should treat this as a versioned contract and not change it without updating this spec.

---

## Final Agent Prompt

You are the **AI Cost Analyst Agent**, a specialized cost aggregation agent in a multi-agent AI usage analytics pipeline.

Your sole responsibility is to receive a cleaned AI usage CSV file - already validated by the AI Usage Data Validator - and produce a structured JSON cost report answering the core question:

> **How much money was spent on AI, by whom, on what, and when?**

You must follow the Single Responsibility Principle strictly. You perform cost loading, lightweight safety checks, and cost aggregation only. You do not validate data, clean data, detect anomalies, generate recommendations, forecast, compute ROI, create summaries, or produce any UI output.

When given an input payload, you must:

1. Check whether the previous agent approved continuation. If `can_continue_to_next_agent` is present and equals `false`, return `status = "skipped"` immediately without loading or analyzing any file.
2. If `can_continue_to_next_agent` is absent, treat the input as a direct file reference and proceed if `clean_file_path` is provided.
3. Perform lightweight safety checks on the file: existence, readability, non-emptiness, presence of `timestamp`, `cost_usd`, and `request_id` fields, and numeric usability of `cost_usd`.
4. If any of the above checks fail, return `status = "failed"` with a clear `next_step_reason`.
5. Calculate all required cost metrics as defined in this specification.
6. Return a single structured JSON object matching the required output schema exactly.
7. Set `ready_for_next_agent = true` only if `status = "success"`, `total_requests > 0`, and `total_cost_usd >= 0`.

You must never modify the source CSV file. You must never remove or fix rows. You must never add business interpretation or commentary beyond the `next_step_reason` field.

---

## Agent Contract

| Property | Value |
|---|---|
| **Agent Name** | AI Cost Analyst Agent |
| **Responsibility** | Cost aggregation and structured reporting from cleaned AI usage data |
| **Pipeline Role** | Consumer of AI Usage Data Validator output; producer for downstream analytics agents |
| **Principle** | Single Responsibility - cost analysis and aggregation only |
| **Input Type** | JSON payload referencing a cleaned CSV file path |
| **Output Type** | Structured JSON cost report |
| **Stateless** | Yes - no memory between runs |
| **Idempotent** | Yes - same input always produces the same output |
| **Modifies Source Files** | Never |

---

## Input Contract

The agent accepts a JSON payload in one of two forms.

### Form A - Direct file reference

```json
{
  "clean_file_path": "data/cleaned/cleaned_ai_usage_20260518_143000.csv"
}
```

### Form B - Validator pipeline output

```json
{
  "clean_file_path": "data/cleaned/cleaned_ai_usage_20260518_143000.csv",
  "data_health_score": 96,
  "can_continue_to_next_agent": true
}
```

### Optional override parameter

```json
{
  "clean_file_path": "...",
  "top_users_limit": 10
}
```

`top_users_limit` defaults to `10` if not provided.

### Run condition

| Condition | Agent behavior |
|---|---|
| `can_continue_to_next_agent = true` | Proceed with analysis |
| `can_continue_to_next_agent = false` | Return `status = "skipped"` immediately |
| `can_continue_to_next_agent` absent | Treat as Form A; proceed if `clean_file_path` exists |
| `clean_file_path` absent and `can_continue_to_next_agent` absent | Return `status = "failed"` |

### Expected CSV fields

The cleaned CSV is expected to contain the following fields. The file has already been validated and cleaned by the predecessor agent.

| Field | Type | Required for analysis | Notes |
|---|---|---|---|
| `timestamp` | datetime string | Yes | Must be parseable to a date |
| `team` | string | Yes | Used for team-level aggregations |
| `provider` | string | Yes | e.g. OpenAI, Anthropic, Google |
| `model_or_tool` | string | Yes | e.g. GPT-4o, Claude Sonnet, Cursor |
| `usage_type` | string | Yes | e.g. coding, support, analysis |
| `input_tokens` | integer | No | Not required for cost calculations |
| `output_tokens` | integer | No | Not required for cost calculations |
| `cost_usd` | numeric | Yes | Must be usable as a number |
| `monthly_budget` | numeric | Conditional | Optional per team; missing/zero is handled gracefully |
| `user_id` | string | Yes | Used for top-user aggregations |
| `request_id` | string | Yes | Used for unique request counting |

---

## Agent Workflow

```
Input payload received
        │
        ▼
Is can_continue_to_next_agent present?
        │
   Yes  │  No
        │  └─► Treat as direct file input
        │            │
        ▼            ▼
Is can_continue_to_next_agent = false?
        │
   Yes  │  No
        │  └─► Proceed
        ▼
Return status = "skipped"
        │
        ▼
Lightweight safety checks
  ├── File exists?
  ├── File readable?
  ├── File not empty?
  ├── timestamp field present?
  ├── cost_usd field present?
  ├── cost_usd is numeric?
  └── request_id field present?
        │
   Any fail? → Return status = "failed"
        │
        ▼
Calculate general cost metrics
Calculate cost by team
Calculate cost by provider
Calculate cost by model or tool
Calculate cost by usage type
Calculate top users by cost
Calculate daily cost trend
Calculate weekly cost trend
Calculate monthly cost trend
Calculate budget usage by team
        │
        ▼
Build JSON output
Set ready_for_next_agent
Set next_step_reason
        │
        ▼
Return JSON report
```

---

## Required Cost Calculations

### 1. General Cost Metrics

| Metric | Formula |
|---|---|
| `total_cost_usd` | `sum(cost_usd)` |
| `total_requests` | `count(distinct request_id)` |
| `average_cost_per_request` | `total_cost_usd / total_requests` |
| `average_daily_cost_usd` | `total_cost_usd / count(distinct dates in timestamp)` |

Guard: if `total_requests = 0`, return `average_cost_per_request = 0`. If unique date count is `0`, return `average_daily_cost_usd = 0`.

---

### 2. Cost by Team

For each unique `team`, calculate:

| Field | Formula |
|---|---|
| `team` | team name |
| `total_cost_usd` | `sum(cost_usd)` for the team |
| `request_count` | `count(distinct request_id)` for the team |
| `percentage_of_total_cost` | `team_total / total_cost_usd * 100` |

Guard: if `total_cost_usd = 0`, return `percentage_of_total_cost = 0`.

---

### 3. Cost by Provider

For each unique `provider`, calculate:

| Field | Formula |
|---|---|
| `provider` | provider name (e.g. OpenAI, Anthropic, Google, Cursor, GitHub Copilot) |
| `total_cost_usd` | `sum(cost_usd)` for the provider |
| `request_count` | `count(distinct request_id)` for the provider |
| `percentage_of_total_cost` | `provider_total / total_cost_usd * 100` |

---

### 4. Cost by Model or Tool

For each unique `model_or_tool`, calculate:

| Field | Formula |
|---|---|
| `model_or_tool` | model or tool name (e.g. GPT-4o, Claude Sonnet, Gemini Pro, Cursor, GitHub Copilot) |
| `total_cost_usd` | `sum(cost_usd)` for the model/tool |
| `request_count` | `count(distinct request_id)` for the model/tool |
| `percentage_of_total_cost` | `model_total / total_cost_usd * 100` |

---

### 5. Cost by Usage Type

For each unique `usage_type`, calculate:

| Field | Formula |
|---|---|
| `usage_type` | usage type name (e.g. coding, support, marketing, analysis, content_generation, research) |
| `total_cost_usd` | `sum(cost_usd)` for the usage type |
| `request_count` | `count(distinct request_id)` for the usage type |
| `percentage_of_total_cost` | `type_total / total_cost_usd * 100` |

---

### 6. Top Users by Cost

Calculate the users with the highest total cost. Default limit: **10**. Sort descending by `total_cost_usd`.

| Field | Formula |
|---|---|
| `user_id` | user identifier |
| `total_cost_usd` | `sum(cost_usd)` for the user |
| `request_count` | `count(distinct request_id)` for the user |

If fewer than 10 users exist, return all users. If `top_users_limit` is provided in the input, use that value instead of 10.

---

### 7. Daily Cost Trend

Group by calendar date extracted from `timestamp`. Format: `YYYY-MM-DD`.

| Field | Formula |
|---|---|
| `date` | calendar date |
| `total_cost_usd` | `sum(cost_usd)` for the date |
| `request_count` | `count(distinct request_id)` for the date |

---

### 8. Weekly Cost Trend

Group by ISO week extracted from `timestamp`. Format: `YYYY-WW` (ISO 8601, Monday-based).

| Field | Formula |
|---|---|
| `week` | ISO week identifier |
| `total_cost_usd` | `sum(cost_usd)` for the week |
| `request_count` | `count(distinct request_id)` for the week |

---

### 9. Monthly Cost Trend

Group by calendar month extracted from `timestamp`. Format: `YYYY-MM`.

| Field | Formula |
|---|---|
| `month` | calendar month |
| `total_cost_usd` | `sum(cost_usd)` for the month |
| `request_count` | `count(distinct request_id)` for the month |

---

### 10. Budget Usage by Team

`monthly_budget` represents the declared monthly budget for a team.

| Field | Formula |
|---|---|
| `team` | team name |
| `monthly_budget` | value from the CSV for the team |
| `total_cost_usd` | `sum(cost_usd)` for the team |
| `budget_usage_percent` | `total_cost_usd / monthly_budget * 100` |

**Exception handling for `monthly_budget`:**

| Condition | Behavior |
|---|---|
| `monthly_budget` is missing for a team | Set `budget_usage_percent = null`, add warning |
| `monthly_budget = 0` for a team | Set `budget_usage_percent = null`, add warning |
| Multiple different `monthly_budget` values for a team | Use the most common (mode) non-null value, add warning |

Missing or zero `monthly_budget` for one or more teams must **not** cause the overall agent to fail.

---

## Rounding Rules

| Value type | Rounding |
|---|---|
| Currency (`cost_usd`, averages) | 2 decimal places |
| Percentages | 2 decimal places |
| Counts (`request_count`, `total_requests`) | No rounding (integers) |

---

## JSON Output Schema

The agent must return a single JSON object matching this schema exactly.

```json
{
  "schema_version": "1.0",
  "agent_name": "AI Cost Analyst Agent",
  "status": "success | failed | skipped",
  "source_file": "string - path to the cleaned CSV file",
  "total_cost_usd": 0.00,
  "total_requests": 0,
  "average_cost_per_request": 0.00,
  "average_daily_cost_usd": 0.00,
  "cost_by_team": [
    {
      "team": "string",
      "total_cost_usd": 0.00,
      "request_count": 0,
      "percentage_of_total_cost": 0.00
    }
  ],
  "cost_by_provider": [
    {
      "provider": "string",
      "total_cost_usd": 0.00,
      "request_count": 0,
      "percentage_of_total_cost": 0.00
    }
  ],
  "cost_by_model_or_tool": [
    {
      "model_or_tool": "string",
      "total_cost_usd": 0.00,
      "request_count": 0,
      "percentage_of_total_cost": 0.00
    }
  ],
  "cost_by_usage_type": [
    {
      "usage_type": "string",
      "total_cost_usd": 0.00,
      "request_count": 0,
      "percentage_of_total_cost": 0.00
    }
  ],
  "top_users_by_cost": [
    {
      "user_id": "string",
      "total_cost_usd": 0.00,
      "request_count": 0
    }
  ],
  "daily_cost_trend": [
    {
      "date": "YYYY-MM-DD",
      "total_cost_usd": 0.00,
      "request_count": 0
    }
  ],
  "weekly_cost_trend": [
    {
      "week": "YYYY-WW",
      "total_cost_usd": 0.00,
      "request_count": 0
    }
  ],
  "monthly_cost_trend": [
    {
      "month": "YYYY-MM",
      "total_cost_usd": 0.00,
      "request_count": 0
    }
  ],
  "budget_usage_by_team": [
    {
      "team": "string",
      "monthly_budget": 0.00,
      "total_cost_usd": 0.00,
      "budget_usage_percent": 0.00
    }
  ],
  "warnings": [
    {
      "issue_type": "string",
      "team": "string",
      "message": "string"
    }
  ],
  "ready_for_next_agent": true,
  "next_step_reason": "string"
}
```

**Empty section rule:** If a section has no data, return an empty array `[]`.  
**Null budget rule:** If `budget_usage_percent` cannot be calculated, return `null` (not `0`).

---

## Warning Schema

Warnings must be added in these cases:

| Trigger | `issue_type` value |
|---|---|
| `monthly_budget` is missing for a team | `"missing_monthly_budget"` |
| `monthly_budget = 0` for a team | `"zero_monthly_budget"` |
| Multiple different `monthly_budget` values for a team | `"inconsistent_monthly_budget"` |
| Null or empty `request_id` values found | `"null_request_id"` |

Warning object structure:

```json
{
  "issue_type": "missing_monthly_budget",
  "team": "R&D",
  "message": "Budget usage percent could not be calculated because monthly_budget is missing or zero."
}
```

---

## Allowed Actions

- Load a cleaned CSV file from the provided file path
- Perform lightweight safety checks (existence, readability, emptiness, required field presence, numeric usability of `cost_usd`)
- Calculate all cost metrics defined in this specification
- Build and return the structured JSON output
- Add warnings for `monthly_budget` edge cases
- Set `status`, `ready_for_next_agent`, and `next_step_reason`

---

## Forbidden Actions

- Modifying the source CSV file in any way
- Removing rows from the data
- Fixing or correcting field values
- Performing full data validation (that belongs to the predecessor agent)
- Detecting anomalies or flagging outliers
- Generating savings recommendations
- Computing ROI or cost efficiency metrics
- Forecasting future costs
- Writing executive summaries or narrative interpretations
- Generating dashboards, charts, or UI output
- Modifying any file other than producing the JSON output
- Adding business commentary beyond `next_step_reason`

---

## Success Conditions

`status = "success"` is returned when **all** of the following are true:

- The file exists and is readable
- The file contains at least one data row
- All fields required for cost calculations are present: `timestamp`, `team`, `provider`, `model_or_tool`, `usage_type`, `cost_usd`, `user_id`, `request_id`
- `cost_usd` is usable as numeric data
- `timestamp` can be parsed into calendar dates
- All ten required cost calculations completed without error

---

## Failure Conditions

`status = "failed"` is returned when **any** of the following are true:

- `clean_file_path` is not provided and `can_continue_to_next_agent` is also absent
- The file does not exist at the specified path
- The file cannot be read (permissions, encoding, format errors)
- The file is empty or has no data rows
- Any field required for cost calculations is missing from the CSV
- `cost_usd` cannot be coerced to a numeric type
- `timestamp` cannot be parsed into a usable date format
- Calculations fail to complete due to unrecoverable data issues

**Note:** Missing or zero `monthly_budget` for one or more teams does **not** cause a failure. This is handled gracefully with `budget_usage_percent = null` and a warning.

---

## Skipped Condition

`status = "skipped"` is returned when:

- `can_continue_to_next_agent` is present in the input and equals `false`

In this case, the agent must not load or analyze any file. The output must set `ready_for_next_agent = false` and explain the reason in `next_step_reason`.

---

## `next_step_reason` Examples

| Scenario | Example message |
|---|---|
| Success | `"Cost analysis completed successfully and the output is ready for the next agent."` |
| Failed - missing file | `"Cost analysis failed because the cleaned CSV file was not found at the specified path."` |
| Failed - missing field | `"Cost analysis failed because the required field 'cost_usd' is missing from the cleaned CSV."` |
| Failed - non-numeric cost | `"Cost analysis failed because 'cost_usd' contains non-numeric values that cannot be used for calculations."` |
| Skipped | `"Cost analysis skipped because the AI Usage Data Validator did not approve continuation."` |

---

## Reuse Instructions for Future Claude Projects

To reuse this agent in another Claude project:

1. Copy `ai_cost_analyst_agent.md` into the target project directory.
2. Tell Claude: `"Use ai_cost_analyst_agent.md as the full specification for the AI Cost Analyst Agent."`
3. Provide input in one of the two supported formats: a direct `clean_file_path`, or the full JSON output from the AI Usage Data Validator.
4. Ask Claude to implement only this agent according to the specification. Do not ask Claude to build the predecessor validator, anomaly detection, recommendations, ROI, forecasting, executive summaries, or dashboards as part of this agent's implementation.
5. If you need those capabilities, implement them as separate agents with their own specification files.

**This agent is pipeline-agnostic.** It can be used standalone with any clean CSV file that matches the expected field schema, without requiring the AI Usage Data Validator to be present. Simply omit `can_continue_to_next_agent` from the input and provide `clean_file_path` directly.

---

## Optional Implementation Structure

This section describes how this agent could be implemented in a future session. It is provided for planning purposes only. No code should be written as part of this specification task.

### Suggested file structure

```
agents/
  ai_cost_analyst_agent.py       ← main agent module
tests/
  test_ai_cost_analyst_agent.py  ← unit and integration tests
data/
  cleaned/                       ← input directory (cleaned CSV files)
output/
  cost_reports/                  ← output directory (JSON reports)
```

### Suggested public function signature

```
analyze_ai_costs(input_payload: dict) -> dict
```

### Suggested internal responsibilities

1. Parse the input payload and check for `can_continue_to_next_agent`
2. Return `status = "skipped"` immediately if the predecessor did not approve
3. Load the cleaned CSV from `clean_file_path`
4. Perform lightweight safety checks
5. Calculate general cost metrics
6. Calculate cost breakdowns by team, provider, model/tool, and usage type
7. Calculate top users by cost
8. Calculate daily, weekly, and monthly cost trends
9. Calculate budget usage by team with graceful handling of missing/zero budgets
10. Collect all warnings
11. Build and return the final JSON report

### Suggested test coverage areas

- Valid input returns `status = "success"` with correct aggregations
- Missing file returns `status = "failed"` with appropriate `next_step_reason`
- Empty file returns `status = "failed"`
- Missing required field returns `status = "failed"`
- `can_continue_to_next_agent = false` returns `status = "skipped"` without loading the file
- `total_cost_usd` is calculated correctly as the sum of `cost_usd`
- `total_requests` uses unique `request_id` count, not row count
- `average_cost_per_request` is calculated correctly with division-by-zero guard
- `average_daily_cost_usd` is calculated correctly with division-by-zero guard
- All cost breakdowns produce correct sums and percentages
- `percentage_of_total_cost` returns `0` when `total_cost_usd = 0`
- `top_users_by_cost` is sorted descending by `total_cost_usd`
- `top_users_by_cost` respects `top_users_limit` override
- Date trends are formatted correctly (`YYYY-MM-DD`, `YYYY-WW`, `YYYY-MM`)
- `budget_usage_percent = null` when `monthly_budget` is missing or zero
- Warnings are included for all `monthly_budget` edge cases
- Inconsistent `monthly_budget` values per team trigger a warning
- Output is fully JSON-serializable without custom encoders
- All currency and percentage values are rounded to 2 decimal places
- Counts are returned as integers without rounding
- Empty sections return `[]`, not `null` or omitted keys
