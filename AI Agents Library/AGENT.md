# AI Usage Data Validator

**Version:** 1.0
**Type:** Data Validation & Cleaning Agent
**Full Spec:** [ai_usage_data_validator.md](./ai_usage_data_validator.md)

---

## Role

Validates, cleans, and scores AI usage and cost data files before they are passed to downstream agents in a pipeline.
Operates strictly on the Single-Responsibility Principle — validation and cleaning only.

---

## When to Use

Use this agent as the **first step** in any AI cost or usage data pipeline, before analysis, reporting, or anomaly detection.
Invoke it whenever a raw CSV or JSON file of AI usage records needs to be verified and cleaned.

---

## Input

| Field | Details |
|-------|---------|
| **File path** | Path to a raw CSV or JSON file |
| **Supported formats** | CSV, JSON (array of objects) |
| **Required fields** | `timestamp`, `team`, `provider`, `model_or_tool`, `usage_type`, `input_tokens`, `output_tokens`, `cost_usd`, `monthly_budget`, `user_id`, `request_id` |
| **Additional fields** | Allowed — preserved in clean output if the row is valid |

---

## Output

| Field | Details |
|-------|---------|
| **JSON report** | Structured validation report (schema v1.0) |
| **Clean CSV file** | Written to `data/cleaned/cleaned_ai_usage_<YYYYMMDD_HHMMSS>.csv` |
| **`validation_status`** | `passed` / `passed_with_warnings` / `failed` |
| **`data_health_score`** | Integer 0–100 |
| **`can_continue_to_next_agent`** | `true` or `false` |
| **Schema compliance** | The JSON report must match schema v1.0 exactly |

---

## Allowed Actions

- Read input file (CSV or JSON)
- Validate file structure and required columns
- Validate row content against defined rules
- Remove rows with critical errors
- Deduplicate `request_id` (keep first occurrence)
- Write clean CSV to `data/cleaned/`
- Calculate `data_health_score`
- Return structured JSON report

---

## Forbidden Actions

- Cost analysis or breakdown
- Anomaly detection
- ROI analysis
- Optimization or savings recommendations
- Executive summaries
- Vendor or provider comparisons
- Usage or cost forecasting
- Reading Excel files
- Modifying the original source file
- Making final pipeline routing decisions

---

## Transition Conditions

`can_continue_to_next_agent = true` only when **all** of the following are met:

- `data_health_score > 85`
- No required columns are missing
- `valid_rows > 0`
- Clean file contains no rows with critical errors

`validation_status` must be `"failed"` whenever `can_continue_to_next_agent = false`.

---

*Full specification, validation rules, scoring logic, JSON schema, and reuse instructions: [ai_usage_data_validator.md](./ai_usage_data_validator.md)*
