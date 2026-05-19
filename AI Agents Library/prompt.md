# AI Usage Data Validator — Implementation Prompt

You are a senior software engineer implementing a data validation and cleaning agent.

Your task is to implement the **AI Usage Data Validator** — the first agent in an AI cost and usage intelligence pipeline.

Before writing any code, inspect the existing project structure and explain which files you plan to create or modify.
Do not modify unrelated files.
Do not refactor existing code unless it is directly required for this implementation.
If a file already exists, state whether you plan to update it or preserve it before making any changes.

---

## Role

This agent validates, cleans, and scores AI usage and cost data files.
It is the entry point of the pipeline. Downstream agents receive only the clean output of this agent.
It operates strictly on the Single-Responsibility Principle: validation, cleaning, and scoring only.

---

## Boundaries

This agent must NOT perform any of the following:
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

## Supported Input Formats

- CSV (UTF-8, header row required)
- JSON (array of objects; each object represents one row; keys must match required field names exactly)

If the file is any other format, return `validation_status = "failed"` immediately without creating a clean file.
If a JSON file is not structured as an array of objects, return `validation_status = "failed"`.

---

## Required Fields

Every input file must contain **at least** these fields:

- `timestamp`
- `team`
- `provider`
- `model_or_tool`
- `usage_type`
- `input_tokens`
- `output_tokens`
- `cost_usd`
- `monthly_budget`
- `user_id`
- `request_id`

Additional fields beyond the required list are allowed and must be preserved in the clean output if the row is valid.

If any required field is entirely absent from the file:
- Do not create a clean file.
- Report the missing column names under `missing_required_columns`.
- Return `validation_status = "failed"`, `can_continue_to_next_agent = false`.

---

## Validation Rules

### File-Level (stop immediately, no clean file)

1. File format is not CSV or JSON → `failed`
2. File is unreadable, empty, or contains zero records → `failed`
3. JSON input is not an array of objects → `failed`
4. One or more required columns are missing → `failed`

### Row-Level Critical Errors (remove row, report in `invalid_rows_details`)

| Condition | `issue_type` |
|-----------|-------------|
| Any required field is null or empty | `missing_required_value` |
| `timestamp` cannot be parsed as a valid datetime | `invalid_timestamp` |
| `cost_usd < 0` | `negative_cost` |
| `input_tokens < 0` | `negative_input_tokens` |
| `output_tokens < 0` | `negative_output_tokens` |
| `monthly_budget` is missing, non-numeric, or `< 0` | `negative_monthly_budget` or `non_numeric_field` |
| Any of `input_tokens`, `output_tokens`, `cost_usd`, `monthly_budget` is non-numeric | `non_numeric_field` |
| `request_id` is missing or empty | `missing_request_id` |
| `request_id` is a duplicate (non-first occurrence) | `duplicate_request_id` |

### Row-Level High Warnings (keep row, report in `warnings`)

| Condition | `issue_type` | `severity` |
|-----------|-------------|------------|
| Same `team` has different `monthly_budget` values across rows | `inconsistent_monthly_budget` | `high_warning` |

Report once per affected team (not once per row).

### Row-Level Warnings (keep row, report in `warnings`)

| Condition | `issue_type` | `severity` |
|-----------|-------------|------------|
| `cost_usd = 0` | `zero_cost` | `warning` |
| Both `input_tokens = 0` and `output_tokens = 0` in the same row | `zero_tokens` | `warning` |

---

## Cleaning Rules

- Remove all rows with any critical error.
- Keep all rows with warnings or high warnings only.
- Preserve all additional (non-required) columns in valid rows.
- Always output the clean file as CSV, regardless of whether the input was CSV or JSON.
- Clean file name format: `cleaned_ai_usage_<YYYYMMDD_HHMMSS>.csv`
- Clean file output path: `data/cleaned/`

If no valid rows remain after cleaning:
- Do not create a clean file.
- Set `clean_file_path = ""`.
- Set `validation_status = "failed"`, `valid_rows = 0`, `can_continue_to_next_agent = false`.
- Explain in `next_step_reason`.

---

## Deduplication Rules

`request_id` uniquely identifies one AI usage or billing event.

- Keep the first occurrence of each `request_id`.
- Remove all subsequent occurrences.
- Report each removed duplicate in `invalid_rows_details` with:
  - `issue_type = "duplicate_request_id"`
  - `severity = "critical"`
  - `action = "removed_from_clean_file"`
- Count removed duplicates in `duplicate_rows_removed`.
- Do not mix `duplicate_request_id` entries with content-error entries.

---

## Timestamp Validation

Accept any datetime format that `pandas.to_datetime()` can parse reliably, including:
- ISO 8601 (`2024-01-15T14:30:00Z`)
- Standard datetime (`2024-01-15 14:30:00`)
- Unix epoch (integer or float)

Any value that cannot be parsed → `invalid_timestamp` critical error.

---

## Data Health Score

Start at 100. Apply the following deductions.
Scoring is **per-row / per-occurrence** — each offending row or occurrence is penalized individually.
The score cannot drop below 0.
Do not double-penalize the same issue: if a specific rule applies, use it; do not also apply the fallback.

| Condition | Deduction |
|-----------|-----------|
| `duplicate_request_id` removed | −3 per removed occurrence |
| Missing value in required field | −5 per row |
| Invalid timestamp | −4 per row |
| Non-numeric value in numeric field | −4 per row |
| `cost_usd < 0` | −5 per row |
| `input_tokens < 0` | −5 per row |
| `output_tokens < 0` | −5 per row |
| `monthly_budget < 0` | −5 per row |
| `monthly_budget` inconsistent for same `team` | −3 per affected team |
| `cost_usd = 0` warning | −1 per row |
| Both `input_tokens` and `output_tokens` = 0 | −1 per row |
| Any other critical error not listed above | −5 per row |

---

## Counting Rules

| Field | Definition |
|-------|-----------|
| `total_rows` | All data rows in the original file, excluding the header |
| `valid_rows` | Rows present in the clean file after all removals |
| `invalid_rows` | Rows removed due to content validation errors (not counting duplicates) |
| `duplicate_rows_removed` | Duplicate `request_id` occurrences removed (not counting the first occurrence) |
| `removed_rows` | `invalid_rows + duplicate_rows_removed` |
| `critical_errors_count` | Total entries in `invalid_rows_details` |
| `warnings_count` | Total `warning`-severity entries in `warnings` |
| `high_warnings_count` | Total `high_warning`-severity entries in `warnings` |

- A single row removed counts once in `invalid_rows` and once in `removed_rows`.
- A row with multiple issues is reported once per issue in `invalid_rows_details`, but counted once in `invalid_rows`.
- Warning-only or high-warning-only rows are never counted in `invalid_rows`.
- `row_number` refers to the data row number; the first data row (after header) is `row_number = 1`.

---

## Transition Conditions

Set `can_continue_to_next_agent = true` only when **all** of the following are true:
- `data_health_score > 85`
- No required columns are missing
- `valid_rows > 0`
- The clean file contains no rows with critical errors

Set `can_continue_to_next_agent = false` otherwise.

Critical errors found in the original file but removed from the clean file do **not** automatically block the transition, as long as all four conditions above are met.

`validation_status` must be `"failed"` whenever `can_continue_to_next_agent = false`.

### Validation Status Logic

| Status | Condition |
|--------|-----------|
| `"passed"` | No critical errors, no rows removed, no warnings of any kind |
| `"passed_with_warnings"` | Warnings, high warnings, or rows removed — but `can_continue_to_next_agent = true` |
| `"failed"` | `can_continue_to_next_agent = false` for any reason |

---

## JSON Output Schema

Return exactly this structure. No additional top-level fields.

```json
{
  "schema_version": "1.0",
  "agent_name": "AI Usage Data Validator",
  "validation_status": "passed | passed_with_warnings | failed",
  "data_health_score": 0,
  "source_file_format": "csv | json",
  "total_rows": 0,
  "valid_rows": 0,
  "invalid_rows": 0,
  "removed_rows": 0,
  "duplicate_rows_removed": 0,
  "missing_required_columns": [],
  "critical_errors_count": 0,
  "warnings_count": 0,
  "high_warnings_count": 0,
  "invalid_rows_details": [
    {
      "row_number": 0,
      "request_id": "",
      "issue_type": "",
      "field": "",
      "value": "",
      "severity": "critical",
      "action": "removed_from_clean_file"
    }
  ],
  "warnings": [
    {
      "issue_type": "",
      "field": "",
      "severity": "warning | high_warning",
      "message": "",
      "affected_rows": []
    }
  ],
  "clean_file_path": "",
  "can_continue_to_next_agent": false,
  "next_step_reason": ""
}
```

**Empty-state rules:**
- No invalid rows → `"invalid_rows_details": []`
- No warnings → `"warnings": []`
- No clean file created → `"clean_file_path": ""`

**`next_step_reason` examples:**
```
"Cleaned dataset passed all validation checks and is ready for the next agent."
"Validation failed: required columns are missing — team, cost_usd."
"Validation failed: no valid rows remained after cleaning."
"Cleaned dataset passed with warnings. 3 rows removed, score 88. Ready for next agent."
"Validation failed: data_health_score is 72, below required threshold of 85."
```

---

## Implementation Requirements

- Implement in Python 3.10+.
- Use `pandas` as the primary library for file parsing, validation, and CSV output.
- Structure the module with one function per responsibility:

| Function | Responsibility |
|----------|---------------|
| `load_file(path)` | Detect format, read CSV or JSON, return DataFrame + format string |
| `check_required_columns(df)` | Return list of missing required columns |
| `validate_rows(df)` | Apply all row-level rules; return clean_df, invalid_details list, warnings list |
| `deduplicate_request_ids(df)` | Identify duplicates; return deduped_df and removed list |
| `check_budget_consistency(df)` | Check `monthly_budget` consistency per `team`; return high_warning list |
| `calculate_health_score(invalid_details, warnings, high_warnings)` | Apply deduction table; return integer 0–100 |
| `write_clean_file(df, output_dir)` | Write timestamped CSV; return file path string |
| `build_json_report(...)` | Assemble and return final JSON report dict |
| `run(file_path)` | Entry point — orchestrates all of the above |

---

## Recommended File Structure

```
agents/
  ai_usage_data_validator.py

data/
  raw/
  cleaned/

tests/
  test_ai_usage_data_validator.py

sample_ai_usage_data.csv
README.md
```

---

## Sample Data File

Create `sample_ai_usage_data.csv` with at least one row of each type:

| Row Type | Purpose |
|----------|---------|
| Valid row | Baseline passing case |
| `cost_usd = 0` | Triggers `zero_cost` warning |
| `cost_usd < 0` | Triggers `negative_cost` critical error |
| Invalid `timestamp` | Triggers `invalid_timestamp` critical error |
| Duplicate `request_id` | Triggers `duplicate_request_id` critical error |
| `input_tokens = 0` and `output_tokens = 0` | Triggers `zero_tokens` warning |
| Inconsistent `monthly_budget` for same `team` | Triggers `inconsistent_monthly_budget` high warning |
| Missing value in required field | Triggers `missing_required_value` critical error |

---

## README Requirements

Create `README.md` with the following sections:

1. What the agent does (one paragraph)
2. Supported input formats
3. Required fields (table)
4. How to run the validator
5. Where the clean file is written
6. How to read the JSON report

---

## Required Tests

Write tests in `tests/test_ai_usage_data_validator.py` covering at minimum:

| Test Case | Expected Outcome |
|-----------|-----------------|
| Fully valid CSV file | `passed`, score 100, clean file written |
| Fully valid JSON file | `passed`, clean file is CSV |
| File with `cost_usd = 0` rows only | `passed_with_warnings`, no rows removed |
| File with `cost_usd < 0` rows | `passed_with_warnings` or `failed` depending on score; rows removed |
| File with duplicate `request_id` | Duplicate removed, reported in `invalid_rows_details` |
| File with invalid timestamp | Row removed, reported in `invalid_rows_details` |
| File with inconsistent `monthly_budget` per team | `high_warning` in `warnings`, no rows removed |
| File where all rows are invalid | `failed`, `valid_rows = 0`, no clean file |
| File with missing required column | `failed`, no clean file, column name in `missing_required_columns` |
| Unsupported file format | `failed`, no clean file |
| JSON not structured as array of objects | `failed` |
| Row with multiple issues | All issues reported separately in `invalid_rows_details`, row counted once in `invalid_rows` |
| Score drops below 85 | `can_continue_to_next_agent = false`, `validation_status = "failed"` |

---

## File Modification Policy

- Create only the files listed in the recommended file structure above.
- Do not modify any file that is not directly required for this implementation.
- Do not refactor existing code unless it directly conflicts with this implementation.
- If a file already exists, state your intent (update or preserve) before touching it.
