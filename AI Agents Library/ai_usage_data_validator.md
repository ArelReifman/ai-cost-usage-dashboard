# AI Usage Data Validator
**Agent Package v1.0**
**Type:** Data Validation & Cleaning Agent
**Single-Responsibility:** Validate, clean, and score AI usage/cost data before it reaches downstream agents.

---

## Flags & Design Decisions

The following ambiguities were identified in the source spec and resolved before packaging:

| # | Issue | Decision |
|---|-------|----------|
| 1 | `invalid_rows` and `removed_rows` had identical definitions | Separated: `invalid_rows` = content-error removals only; `removed_rows` = `invalid_rows + duplicate_rows_removed` |
| 2 | Scoring rule granularity (per-row vs. per-issue-type) not specified | **Per-row**: each offending row is penalized individually |
| 3 | Valid `timestamp` formats not listed | Any format parseable by `pandas.to_datetime()` is valid; anything else is critical |
| 4 | JSON input structure not specified | Expected: array of objects, keys matching required field names |
| 5 | `invalid_rows_details` vs `warnings` boundary not explicit | Only removed rows → `invalid_rows_details`; warning-only rows → `warnings` array |

---

## 1. Final Agent Prompt

```
You are the AI Usage Data Validator — a data validation and cleaning agent.

Your only responsibility is to validate, clean, and score AI usage and cost data files before they are passed to downstream agents.

You must operate strictly according to the Single-Responsibility Principle:
you validate, clean, and score. Nothing else.

---

## Inputs You Accept

You receive one data file per invocation.
Supported formats: CSV, JSON (array of objects).
No other formats are accepted.

---

## Required Fields

Every input file must contain at least these required fields:
- timestamp
- team
- provider
- model_or_tool
- usage_type
- input_tokens
- output_tokens
- cost_usd
- monthly_budget
- user_id
- request_id

Additional fields are allowed and must be preserved in the clean output if the row is valid.

If any required field is missing entirely from the file, stop immediately.
Do not create a clean file. Return validation_status = "failed".

---

## File-Level Validation

1. If the file format is not CSV or JSON → validation_status = "failed", can_continue_to_next_agent = false.
2. If the file cannot be read, is empty, or contains no records → validation_status = "failed", can_continue_to_next_agent = false.
3. If one or more required columns are missing → validation_status = "failed", can_continue_to_next_agent = false.
   Report missing column names under missing_required_columns.

In all three cases above: do not create a clean file.

---

## Row-Level Validation

Apply the following rules to each row. A row that violates any critical rule must be:
- Removed from the clean file
- Reported in full in invalid_rows_details

### Critical Errors (remove row, report in invalid_rows_details)

- Any required field has a missing or null value
- timestamp cannot be parsed as a valid datetime
- cost_usd < 0
- input_tokens < 0
- output_tokens < 0
- monthly_budget is missing, non-numeric, or < 0
- Any of the following fields contains a non-numeric value: input_tokens, output_tokens, cost_usd, monthly_budget
- request_id is missing
- request_id is a duplicate (keep only the first occurrence; remove all subsequent occurrences)

### High Warnings (keep row, report in warnings array)

- For a given team, different rows have different values for monthly_budget
  Report once per affected team.

### Warnings (keep row, report in warnings array)

- cost_usd = 0
- Both input_tokens = 0 and output_tokens = 0 in the same row

---

## Duplicate Handling

request_id uniquely identifies one AI usage or billing event.
When a duplicate request_id is found:
- Retain the first occurrence.
- Remove all subsequent occurrences from the clean file.
- Report each removed duplicate in invalid_rows_details with issue_type = "duplicate_request_id" and severity = "critical".
- Do not mix this issue type with content errors.

---

## Clean File Output

- Always output a CSV file, regardless of whether the input was CSV or JSON.
- Include all rows that passed validation (critical-error rows removed, warning-only rows kept).
- Preserve any extra columns beyond the required fields, as long as the row itself is valid.
- Name the file: cleaned_ai_usage_<YYYYMMDD_HHMMSS>.csv
- Save to: data/cleaned/

If no valid rows remain after cleaning:
- Do not create a clean file.
- Set clean_file_path = "".
- Set validation_status = "failed", valid_rows = 0, can_continue_to_next_agent = false.
- Explain clearly in next_step_reason.

---

## Data Health Score

Start at 100. Apply the following deductions per occurrence (per-row, not per-issue-type).
The score cannot drop below 0.

| Condition | Deduction |
|-----------|-----------|
| duplicate request_id removed | -3 per removed duplicate |
| missing value in required field | -5 per row |
| invalid timestamp | -4 per row |
| non-numeric value in numeric field | -4 per row |
| cost_usd < 0 | -5 per row |
| input_tokens < 0 | -5 per row |
| output_tokens < 0 | -5 per row |
| monthly_budget < 0 | -5 per row |
| monthly_budget inconsistent for team | -3 per affected team (not per row) |
| cost_usd = 0 warning | -1 per row |
| both input_tokens and output_tokens = 0 | -1 per row |
| any other critical error not listed above | -5 per row |

No double-penalizing: if a specific rule applies, use it. Do not also apply the fallback -5.

---

## Transition Decision

Set can_continue_to_next_agent = true only when ALL of the following are true:
- data_health_score > 85
- No required columns are missing
- valid_rows > 0
- The clean file contains no rows with critical errors

Critical errors found in the original file but removed from the clean file do NOT
automatically block the transition, as long as all four conditions above are met.

Set can_continue_to_next_agent = false otherwise.

---

## Validation Status

- "passed": no critical errors, no rows removed, no warnings of any kind
- "passed_with_warnings": warnings, high warnings, or rows removed — but can_continue_to_next_agent = true
- "failed": can_continue_to_next_agent = false

---

## Output

Return a single JSON object exactly matching the schema defined in the agent contract.
Do not return anything else.
Do not perform cost analysis, anomaly detection, ROI analysis, optimization recommendations,
savings recommendations, executive summaries, vendor comparisons, or usage forecasts.
```

---

## 2. Agent Contract

| Field | Value |
|-------|-------|
| **Agent Name** | AI Usage Data Validator |
| **Version** | 1.0 |
| **Responsibility** | Validate, clean, and score AI usage/cost data files |
| **Trigger** | Called by an orchestrator or pipeline manager with a single file path |
| **Upstream** | Raw data source (user upload, scheduled ingestion, API export) |
| **Downstream** | Next pipeline agent (e.g., Cost Analysis Agent, Anomaly Detection Agent) |
| **Handoff Condition** | `can_continue_to_next_agent = true` AND clean file written to `data/cleaned/` |
| **Handoff Payload** | JSON report (see schema) + path to clean CSV file |
| **Invocation Type** | Synchronous — returns result before downstream agent starts |
| **Idempotent?** | Deterministic validation logic: yes. Fully idempotent output path: no, because the clean file name includes a timestamp. The validation results should be consistent for the same input, but `clean_file_path` may differ between runs. |
| **State** | Stateless — no memory between invocations |

### What This Agent Does
- Reads one data file (CSV or JSON)
- Checks file-level validity (format, readability, required columns)
- Validates each row against defined rules
- Removes critical rows, keeps warning-only rows
- Deduplicates `request_id` (keeps first occurrence)
- Writes a clean CSV file to `data/cleaned/`
- Computes a `data_health_score`
- Returns a structured JSON validation report

### What This Agent Does Not Do
See Section 7 (Forbidden Actions).

---

## 3. Input Contract

### Supported Formats
| Format | Notes |
|--------|-------|
| CSV | Header row required, UTF-8 encoding |
| JSON | Array of objects; each object = one row; keys must match required field names |

### Required Fields

| Field | Type | Rules |
|-------|------|-------|
| `timestamp` | datetime | Must be parseable (ISO 8601, `YYYY-MM-DD HH:MM:SS`, Unix epoch, or any format `pandas.to_datetime()` accepts) |
| `team` | string | Must be non-empty |
| `provider` | string | Must be non-empty |
| `model_or_tool` | string | Must be non-empty |
| `usage_type` | string | Must be non-empty |
| `input_tokens` | numeric | ≥ 0; non-numeric or negative = critical error |
| `output_tokens` | numeric | ≥ 0; non-numeric or negative = critical error |
| `cost_usd` | numeric | ≥ 0 (0 allowed with warning, negative = critical); non-numeric = critical error |
| `monthly_budget` | numeric | Must be numeric and ≥ 0. Must be consistent per `team`. Negative, missing, or non-numeric = critical error |
| `user_id` | string | Must be non-empty |
| `request_id` | string | Must be unique and non-empty |

### Optional Fields
Any additional columns beyond the required fields are preserved in the clean file as-is.

### Unsupported Formats
Excel (`.xlsx`, `.xls`) and all other formats are **not supported** in v1.0.
Return `validation_status = "failed"` if such a file is provided.

---

## 4. JSON Output Schema

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

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | string | Always `"1.0"` in this version |
| `agent_name` | string | Always `"AI Usage Data Validator"` |
| `validation_status` | enum | `"passed"` / `"passed_with_warnings"` / `"failed"` |
| `data_health_score` | integer | 0–100, starts at 100, deducted per rule |
| `source_file_format` | enum | `"csv"` or `"json"` |
| `total_rows` | integer | Total data rows in original file (excluding header) |
| `valid_rows` | integer | Rows in clean file after all removals |
| `invalid_rows` | integer | Rows removed due to content validation errors (not counting duplicates) |
| `removed_rows` | integer | Total rows removed = `invalid_rows + duplicate_rows_removed` |
| `duplicate_rows_removed` | integer | Number of duplicate `request_id` occurrences removed (not counting first occurrence) |
| `missing_required_columns` | array of strings | Column names missing from the file |
| `critical_errors_count` | integer | Total critical-error entries across all rows |
| `warnings_count` | integer | Total warning entries |
| `high_warnings_count` | integer | Total high-warning entries |
| `invalid_rows_details` | array | One entry per critical issue per row (a row can have multiple entries) |
| `warnings` | array | One entry per warning/high-warning issue type + affected rows |
| `clean_file_path` | string | Relative path to clean CSV; `""` if not created |
| `can_continue_to_next_agent` | boolean | Whether the next agent should process this file |
| `next_step_reason` | string | Brief explanation of the transition decision |

### `invalid_rows_details` — Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `row_number` | integer | Row number in original file; row 1 = first data row (after header) |
| `request_id` | string | Value of `request_id` in that row (or `""` if missing) |
| `issue_type` | string | Machine-readable issue code (see Issue Type Reference below) |
| `field` | string | The field that caused the error |
| `value` | any | The actual value found in that field |
| `severity` | enum | Always `"critical"` in `invalid_rows_details` |
| `action` | enum | Always `"removed_from_clean_file"` in this version |

### `warnings` — Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `issue_type` | string | Machine-readable issue code |
| `field` | string | The field involved |
| `severity` | enum | `"warning"` or `"high_warning"` |
| `message` | string | Human-readable description |
| `affected_rows` | array of integers | Row numbers where this warning was found |

### Issue Type Reference

| `issue_type` | Severity | Description |
|---|---|---|
| `missing_required_value` | critical | Required field is null or empty |
| `invalid_timestamp` | critical | Timestamp cannot be parsed |
| `negative_cost` | critical | `cost_usd < 0` |
| `negative_input_tokens` | critical | `input_tokens < 0` |
| `negative_output_tokens` | critical | `output_tokens < 0` |
| `negative_monthly_budget` | critical | `monthly_budget < 0` |
| `non_numeric_field` | critical | A numeric field contains a non-numeric value |
| `missing_request_id` | critical | `request_id` is missing or empty |
| `duplicate_request_id` | critical | `request_id` appears more than once; this is a non-first occurrence |
| `inconsistent_monthly_budget` | high_warning | Same `team` has different `monthly_budget` values across rows |
| `zero_cost` | warning | `cost_usd = 0` |
| `zero_tokens` | warning | Both `input_tokens` and `output_tokens` are 0 in the same row |

### Empty-State Rules
- If no invalid rows: `"invalid_rows_details": []`
- If no warnings: `"warnings": []`
- If no clean file created: `"clean_file_path": ""`

### `next_step_reason` Examples

```
"Cleaned dataset passed all validation checks and is ready for the next agent."

"Validation failed: required columns are missing — team, cost_usd."

"Validation failed: no valid rows remained after cleaning."

"Cleaned dataset passed with warnings. 3 rows removed, score 88. Ready for next agent."

"Validation failed: data_health_score is 72, below required threshold of 85."
```

---

## 5. Agent Workflow

```
START
  │
  ▼
[1] Receive file path
  │
  ▼
[2] Detect file format (CSV / JSON / unsupported)
  │
  ├─ Unsupported ──────────────────────────────────────────────────────┐
  ▼                                                                     │
[3] Read file — check readability, emptiness, zero records             │
  │                                                                     │
  ├─ Unreadable / empty / no records ──────────────────────────────────┤
  ▼                                                                     │
[4] Check required columns present                                     │
  │                                                                     │
  ├─ Missing required columns ─────────────────────────────────────────┤
  ▼                                                                     │
[5] Row-level validation loop (per row):                               │
    ├── Check missing required values                                   │
    ├── Validate timestamp parseability                                 │
    ├── Validate numeric fields (type check)                           │
    ├── Check cost_usd (< 0 = critical, = 0 = warning)                │
    ├── Check input_tokens / output_tokens (< 0 = critical, both 0 = warning) │
    ├── Check monthly_budget (< 0 or non-numeric = critical)          │
    └── Flag rows for removal or warning                               │
  │                                                                     │
  ▼                                                                     │
[6] Deduplicate request_id                                             │
    ├── Keep first occurrence                                           │
    └── Remove + report all subsequent occurrences                     │
  │                                                                     │
  ▼                                                                     │
[7] Check monthly_budget consistency per team                          │
    └── Flag high_warning if inconsistent (no row removal)            │
  │                                                                     │
  ▼                                                                     │
[8] Build clean dataset (valid rows only)                              │
  │                                                                     │
  ├─ No valid rows remain ─────────────────────────────────────────────┤
  ▼                                                                     │
[9] Write clean CSV to data/cleaned/                                   │
    └── Filename: cleaned_ai_usage_<YYYYMMDD_HHMMSS>.csv             │
  │                                                                     │
  ▼                                                                     │
[10] Calculate data_health_score (start 100, deduct per rule)         │
  │                                                                     │
  ▼                                                                     │
[11] Determine validation_status and can_continue_to_next_agent       │
  │                                                                     │
  ▼                                                                     ▼
[12] Build and return JSON report ◄──────── FAILED PATH: return JSON, no clean file

END
```

---

## 6. Allowed Actions

| # | Action | Description |
|---|--------|-------------|
| 1 | **Read input file** | Read CSV or JSON from the provided path |
| 2 | **Detect file format** | Identify CSV vs JSON vs unsupported |
| 3 | **Validate file-level structure** | Check readability, emptiness, required columns |
| 4 | **Validate row content** | Apply all row-level rules per the validation spec |
| 5 | **Deduplicate rows** | Identify and remove duplicate `request_id` occurrences |
| 6 | **Remove invalid rows** | Remove rows that violate critical rules from the clean file |
| 7 | **Preserve extra columns** | Keep any non-required columns in valid rows |
| 8 | **Write clean CSV** | Create `cleaned_ai_usage_<YYYYMMDD_HHMMSS>.csv` in `data/cleaned/` |
| 9 | **Calculate data_health_score** | Apply deduction rules to produce a score 0–100 |
| 10 | **Determine transition decision** | Set `can_continue_to_next_agent` based on defined thresholds |
| 11 | **Return JSON report** | Output structured validation report (schema v1.0) |

---

## 7. Forbidden Actions

| # | Forbidden Action | Reason |
|---|-----------------|--------|
| 1 | Cost analysis or cost breakdown | Out of scope — belongs to Cost Analysis Agent |
| 2 | Anomaly detection | Out of scope — belongs to Anomaly Detection Agent |
| 3 | ROI analysis | Out of scope — belongs to ROI Agent |
| 4 | Optimization recommendations | Out of scope — belongs to Optimization Agent |
| 5 | Savings recommendations | Out of scope — belongs to Optimization Agent |
| 6 | Executive summaries | Out of scope — belongs to Reporting Agent |
| 7 | Vendor/provider comparisons | Out of scope — belongs to Analysis Agent |
| 8 | Usage or cost forecasting | Out of scope — belongs to Forecasting Agent |
| 9 | Reading Excel files | Not supported in v1.0 |
| 10 | Modifying the original source file | Read-only access to source; only write to `data/cleaned/` |
| 11 | Storing state between invocations | Agent is stateless |
| 12 | Making pipeline routing decisions | The agent sets `can_continue_to_next_agent`; routing logic belongs to the orchestrator |

---

## 8. Success Criteria

The agent is considered successful when:

| Criterion | Condition |
|-----------|-----------|
| **File-level validation complete** | File format, readability, and required columns all checked |
| **Row-level validation complete** | All rows evaluated against all defined rules |
| **Clean file created** | At least one valid row exists and clean CSV is written to `data/cleaned/` |
| **JSON report returned** | Structured JSON matches schema v1.0 exactly |
| **Score computed** | `data_health_score` is a non-negative integer ≤ 100 |
| **Transition decision set** | `can_continue_to_next_agent` is set per defined conditions |
| **No scope violations** | Agent has not performed any forbidden action |

### Ideal Outcome (fully clean file)
```json
{
  "validation_status": "passed",
  "data_health_score": 100,
  "valid_rows": N,
  "invalid_rows": 0,
  "removed_rows": 0,
  "duplicate_rows_removed": 0,
  "can_continue_to_next_agent": true
}
```

---

## 9. Failure Criteria

The agent fails (returns `validation_status = "failed"`) in the following cases:

| Condition | Result |
|-----------|--------|
| Unsupported file format | `failed`, no clean file |
| File unreadable, empty, or zero records | `failed`, no clean file |
| One or more required columns missing | `failed`, no clean file |
| All rows removed after validation | `failed`, `valid_rows = 0`, no clean file |
| `data_health_score ≤ 85` | `can_continue_to_next_agent = false` (may still write clean file) |

### Soft Failure / Clean File Created but Downstream Blocked
The agent may still create a clean file, but `validation_status` must be `"failed"` whenever `can_continue_to_next_agent = false`.

This occurs when:
- `data_health_score ≤ 85` — data quality too low
- The clean file still contains rows with critical errors (should not happen by design, but flagged defensively)

---

## 10. Reuse Instructions

### How to Copy This Agent Into Another Claude Project

1. **Copy the agent prompt** from Section 1 into the new Claude project's system prompt (or project instructions).

2. **Set up the directory structure** in the new project:
   ```
   data/
     raw/        ← place input files here
     cleaned/    ← agent writes clean files here
   ```

3. **Pass the file path as input.** The agent expects a single file path pointing to a CSV or JSON file.

4. **Read the JSON output.** The agent always returns a structured JSON matching schema v1.0. Wire the downstream agent to read `clean_file_path` only when `can_continue_to_next_agent = true`.

5. **Do not change the required field list** unless you also update the validation rules and scoring rules accordingly. The required fields are tightly coupled to the rule set.

### Customization Points

| What to Customize | Where | Notes |
|---|---|---|
| Required field list | Section 3 + agent prompt | Add/remove fields; update validation rules accordingly |
| Supported input formats | Section 3 + agent prompt | Add Excel support by adding a parsing step |
| Transition threshold | Agent prompt (score > 85) | Change to reflect pipeline needs |
| Scoring weights | Agent prompt (deduction table) | Adjust per business requirements |
| Output directory | Agent prompt (`data/cleaned/`) | Change to match project folder structure |
| `schema_version` | JSON schema | Bump when making breaking schema changes |

### Integration Pattern

```
Orchestrator
    │
    ▼
[AI Usage Data Validator]  ← this agent
    │
    ├─ can_continue = true  ──► Next Agent (e.g., Cost Analysis Agent)
    │                            Input: clean_file_path
    │
    └─ can_continue = false ──► Error Handler / Human Review
                                 Input: JSON report + next_step_reason
```

### Versioning
- Bump `schema_version` in the JSON output when making breaking changes to the output schema.
- Keep the agent name constant (`"AI Usage Data Validator"`) to allow downstream agents to verify they received output from the correct agent.

---

## 11. Optional Implementation Structure

> No code is written here. This section describes the recommended module structure for when implementation is requested.

### Recommended Tech Stack
- **Language:** Python 3.10+
- **Primary library:** `pandas` (file parsing, row validation, CSV output)
- **Supporting libraries:** `json`, `datetime`, `pathlib`, `re`

### Project File Structure

```
agents/
  ai_usage_data_validator.py     ← main agent module

data/
  raw/                           ← input files placed here
  cleaned/                       ← clean CSV output written here

tests/
  test_ai_usage_data_validator.py

sample_ai_usage_data.csv         ← test fixture (see required rows below)
README.md
```

### Module Internal Structure (`ai_usage_data_validator.py`)

Suggested functions, each with a single responsibility:

| Function | Responsibility |
|---|---|
| `load_file(path)` | Detect format, read CSV or JSON, return DataFrame + format string |
| `check_required_columns(df)` | Return list of missing required columns |
| `validate_rows(df)` | Apply all row-level rules; return (clean_df, invalid_details, warnings) |
| `deduplicate_request_ids(df)` | Identify duplicates, return (deduped_df, removed_list) |
| `check_budget_consistency(df)` | Check `monthly_budget` consistency per `team`; return high_warning list |
| `calculate_health_score(invalid_details, warnings, high_warnings)` | Apply deduction rules; return integer score |
| `write_clean_file(df, output_dir)` | Write CSV with timestamped filename; return file path |
| `build_json_report(...)` | Assemble and return final JSON report dict |
| `run(file_path)` | Orchestrates all of the above; entry point |

### `sample_ai_usage_data.csv` — Required Test Rows

The sample file must contain at least one row of each type:

| Row Type | Purpose |
|---|---|
| Valid row | Baseline passing case |
| `cost_usd = 0` | Triggers `zero_cost` warning |
| `cost_usd < 0` | Triggers `negative_cost` critical error |
| Invalid `timestamp` | Triggers `invalid_timestamp` critical error |
| Duplicate `request_id` | Triggers `duplicate_request_id` critical error |
| `input_tokens = 0` and `output_tokens = 0` | Triggers `zero_tokens` warning |
| Inconsistent `monthly_budget` for same `team` | Triggers `inconsistent_monthly_budget` high warning |
| Missing value in required field | Triggers `missing_required_value` critical error |

### `README.md` — Required Sections

1. What the agent does (one paragraph)
2. Supported input formats
3. Required fields (table)
4. How to run the validator (command)
5. Where the clean file is written
6. How to read the JSON report

### Testing Strategy (no code)

Each function listed above should have at least one unit test.
Integration tests should cover:
- Full valid file → `passed`, score 100
- File with all warning types → `passed_with_warnings`, no rows removed
- File with mixed critical + warnings → `passed_with_warnings`, rows removed, score computed
- File with all rows invalid → `failed`, no clean file
- Missing required column → `failed`, no clean file
- Unsupported file format → `failed`
- JSON input → clean CSV output confirmed

---

*Agent Package v1.0 — AI Agents Library*
*Created: 2026-05-18*
