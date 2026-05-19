"""
Generates 1,000-row enterprise-realistic AI usage CSV (AGENT.md schema).

Each row represents either:
  - A "pipeline job": large batch/automated AI workflow (nightly code analysis,
    document processing pipelines, bulk summarization). Token counts reflect
    real enterprise batch workloads — 500K–8M input tokens per job.
  - A "regular call": individual API request from an interactive user session.

Total cost is scaled to $12,000 to represent enterprise pricing including
API gateway overhead and observability tooling (typically 2–4x raw API cost).
"""
import os
import random
import uuid

import numpy as np
import pandas as pd

np.random.seed(42)
random.seed(42)

END   = pd.Timestamp("2026-05-18")
START = END - pd.Timedelta(days=90)

# ── Teams: (monthly_budget_usd, user_pool_size, target_row_count) ─────────────
# Budgets are intentionally tight relative to 90-day spend to trigger
# "near budget" alerts in the dashboard for demo impact.
TEAMS = {
    "Engineering": ( 5_500, 25, 210),   # ~94% budget utilisation over 90 days
    "Product":     ( 4_000, 15, 155),   # ~94% utilisation
    "Marketing":   ( 3_500, 12, 125),   # high cost/low value — premium models, wasteful
    "Support":     (   800, 22, 175),   # high volume, very efficient cheap models
    "Sales":       ( 1_800, 15, 130),   # moderate, mixed models
    "Finance":     ( 1_300,  8,  85),   # ~88% utilisation — near budget
    "Legal":       ( 2_000,  8,  80),   # within budget
    "HR":          (   600,  7,  40),   # lowest usage
}
# sum of target_row_count == 1000

# ── Providers & models ────────────────────────────────────────────────────────
PROVIDERS = ["OpenAI", "Anthropic", "Google", "xAI", "Meta", "Mistral", "DeepSeek", "Qwen", "Amazon"]

ALL_MODELS = {
    "OpenAI":    [
        # current
        "GPT-5.5", "GPT-5.5 Pro", "GPT-5.4", "GPT-5.4 Pro",
        "GPT-5.3-Codex", "GPT-5.3 Instant", "GPT-5 mini", "GPT-5 nano",
        # legacy / historical
        "GPT-5.2", "GPT-5.2 Pro", "GPT-5.1", "GPT-4o", "GPT-4o mini",
        "GPT-4.1", "GPT-4.1 mini", "o3", "o3-pro", "o4-mini",
    ],
    "Anthropic": ["Claude Opus 4.7", "Claude Opus 4.6", "Claude Sonnet 4.6", "Claude Haiku"],
    "Google":    ["Gemini 3 Pro", "Gemini 3 Deep Think"],
    "xAI":       ["Grok 4.3"],
    "Meta":      ["Llama 4 Scout", "Llama 4 Maverick", "Llama 4 Behemoth"],
    "Mistral":   ["Mistral Large 3", "Mistral 3 14B", "Mistral 3 8B", "Mistral 3 3B"],
    "DeepSeek":  ["DeepSeek V4 Pro", "DeepSeek V4 Flash", "DeepSeek R1"],
    "Qwen":      ["Qwen3-Max", "Qwen3.5-Omni", "Qwen3.6", "Qwen3-VL", "Qwen-Coder"],
    "Amazon":    ["Nova 2", "Nova Pro", "Nova Premier", "Nova Act"],
}

# Premium models reserved for pipeline jobs
PIPELINE_MODELS = {
    "OpenAI":    ["GPT-5.5 Pro", "GPT-5.5", "GPT-5.4 Pro"],
    "Anthropic": ["Claude Opus 4.7", "Claude Opus 4.6", "Claude Sonnet 4.6"],
    "Google":    ["Gemini 3 Deep Think", "Gemini 3 Pro"],
    "xAI":       ["Grok 4.3"],
    "Meta":      ["Llama 4 Behemoth"],
    "Mistral":   ["Mistral Large 3"],
    "DeepSeek":  ["DeepSeek V4 Pro"],
    "Qwen":      ["Qwen3-Max"],
    "Amazon":    ["Nova Premier"],
}

# (input $/1M tokens, output $/1M tokens)
COSTS = {
    # OpenAI — current
    "GPT-5.5":              (15.00,  60.00),
    "GPT-5.5 Pro":          (30.00, 120.00),
    "GPT-5.4":              ( 8.00,  32.00),
    "GPT-5.4 Pro":          (18.00,  72.00),
    "GPT-5.3-Codex":        ( 6.00,  24.00),
    "GPT-5.3 Instant":      ( 2.00,   8.00),
    "GPT-5 mini":           ( 0.40,   1.60),
    "GPT-5 nano":           ( 0.08,   0.32),
    # OpenAI — legacy
    "GPT-5.2":              ( 6.00,  24.00),
    "GPT-5.2 Pro":          (12.00,  48.00),
    "GPT-5.1":              ( 4.00,  16.00),
    "GPT-4o":               ( 5.00,  15.00),
    "GPT-4o mini":          ( 0.15,   0.60),
    "GPT-4.1":              ( 3.00,  12.00),
    "GPT-4.1 mini":         ( 0.40,   1.60),
    "o3":                   (10.00,  40.00),
    "o3-pro":               (20.00,  80.00),
    "o4-mini":              ( 1.10,   4.40),
    # Anthropic
    "Claude Opus 4.7":      (15.00,  75.00),
    "Claude Opus 4.6":      (12.00,  60.00),
    "Claude Sonnet 4.6":    ( 3.00,  15.00),
    "Claude Haiku":         ( 0.80,   4.00),
    # Google
    "Gemini 3 Pro":         ( 2.50,  10.00),
    "Gemini 3 Deep Think":  ( 8.00,  32.00),
    # xAI
    "Grok 4.3":             ( 5.00,  20.00),
    # Meta
    "Llama 4 Scout":        ( 0.20,   0.80),
    "Llama 4 Maverick":     ( 0.50,   2.00),
    "Llama 4 Behemoth":     ( 2.00,   8.00),
    # Mistral
    "Mistral Large 3":      ( 3.00,   9.00),
    "Mistral 3 14B":        ( 0.50,   1.50),
    "Mistral 3 8B":         ( 0.20,   0.60),
    "Mistral 3 3B":         ( 0.06,   0.18),
    # DeepSeek
    "DeepSeek V4 Pro":      ( 1.00,   3.00),
    "DeepSeek V4 Flash":    ( 0.15,   0.60),
    "DeepSeek R1":          ( 0.55,   2.20),
    # Qwen
    "Qwen3-Max":            ( 1.20,   4.80),
    "Qwen3.5-Omni":         ( 0.80,   3.20),
    "Qwen3.6":              ( 0.50,   2.00),
    "Qwen3-VL":             ( 0.70,   2.80),
    "Qwen-Coder":           ( 0.40,   1.60),
    # Amazon
    "Nova 2":               ( 0.80,   3.20),
    "Nova Pro":             ( 1.80,   7.20),
    "Nova Premier":         ( 5.00,  20.00),
    "Nova Act":             ( 0.30,   1.20),
}

USAGE_TYPES = ["completion", "embedding", "chat", "summarization", "code-gen", "analysis", "search"]

# ── Pipeline job fraction per team ────────────────────────────────────────────
# Pipeline rows use large token counts (500K–8M) representing batch workloads.
PIPELINE_PCT = {
    "Engineering": 0.55,  # nightly CI analysis, full-repo code review, PR summarization
    "Product":     0.45,  # user research batch analysis, usage analytics pipelines
    "Marketing":   0.18,  # content generation pipelines
    "Support":     0.00,  # all individual ticket interactions — no batch jobs
    "Sales":       0.10,  # CRM enrichment pipelines
    "Finance":     0.30,  # financial report analysis, regulatory doc review
    "Legal":       0.38,  # contract batch review, compliance scanning
    "HR":          0.12,  # resume screening pipelines
}

PIPELINE_USAGE   = ["analysis", "summarization", "code-gen", "completion"]
PIPELINE_USAGE_W = [0.35, 0.30, 0.25, 0.10]

# ── Provider preferences by team ──────────────────────────────────────────────
# Weights order: OpenAI, Anthropic, Google, xAI, Meta, Mistral, DeepSeek, Qwen, Amazon
PROVIDER_WEIGHTS = {
    "Engineering": [0.25, 0.30, 0.10, 0.05, 0.10, 0.08, 0.06, 0.03, 0.03],  # open-source mix
    "Product":     [0.28, 0.38, 0.12, 0.04, 0.06, 0.04, 0.03, 0.02, 0.03],  # Anthropic-heavy
    "Marketing":   [0.55, 0.18, 0.08, 0.04, 0.05, 0.03, 0.03, 0.02, 0.02],  # OpenAI-dominant
    "Support":     [0.25, 0.32, 0.08, 0.02, 0.05, 0.06, 0.04, 0.02, 0.16],  # cheap Nova + Haiku
    "Sales":       [0.48, 0.20, 0.08, 0.05, 0.05, 0.03, 0.03, 0.02, 0.06],
    "Finance":     [0.35, 0.28, 0.10, 0.03, 0.04, 0.05, 0.08, 0.04, 0.03],
    "Legal":       [0.45, 0.35, 0.08, 0.02, 0.03, 0.02, 0.02, 0.01, 0.02],  # conservative
    "HR":          [0.50, 0.18, 0.08, 0.02, 0.05, 0.03, 0.03, 0.02, 0.09],
}

USAGE_WEIGHTS = {
    "Engineering": [0.15, 0.04, 0.14, 0.07, 0.38, 0.17, 0.05],  # code-gen heavy
    "Product":     [0.20, 0.05, 0.18, 0.15, 0.12, 0.25, 0.05],
    "Marketing":   [0.28, 0.08, 0.30, 0.20, 0.03, 0.07, 0.04],  # chat + completion
    "Support":     [0.12, 0.04, 0.60, 0.06, 0.01, 0.06, 0.11],  # chat dominant
    "Sales":       [0.22, 0.05, 0.35, 0.15, 0.02, 0.16, 0.05],
    "Finance":     [0.20, 0.04, 0.14, 0.22, 0.02, 0.35, 0.03],
    "Legal":       [0.14, 0.02, 0.10, 0.38, 0.02, 0.30, 0.04],  # summarization heavy
    "HR":          [0.25, 0.06, 0.30, 0.20, 0.03, 0.12, 0.04],
}

# Marketing/Sales/HR pull expensive models even for trivial tasks (waste pattern)
EXPENSIVE_BIAS = {"Marketing": 0.52, "Sales": 0.32, "HR": 0.28}
# Support/Engineering/Product prefer cheap models for regular calls
CHEAP_BIAS     = {"Support": 0.82, "Engineering": 0.32, "Product": 0.28, "Finance": 0.25}


# ── Model selection ───────────────────────────────────────────────────────────
def _pick_model(team: str, provider: str, is_pipeline: bool) -> str:
    if is_pipeline:
        options = PIPELINE_MODELS.get(provider, ALL_MODELS[provider])
        return random.choice(options)

    options = ALL_MODELS[provider]
    if team in EXPENSIVE_BIAS and random.random() < EXPENSIVE_BIAS[team]:
        pricey = [m for m in options if COSTS[m][0] >= 5.0]
        if pricey:
            return random.choice(pricey)
    if team in CHEAP_BIAS and random.random() < CHEAP_BIAS[team]:
        cheap = [m for m in options if COSTS[m][0] < 1.0]
        if cheap:
            return random.choice(cheap)
    return random.choice(options)


# ── Token count generation ────────────────────────────────────────────────────
def _token_counts(usage: str, is_pipeline: bool, team: str) -> tuple[int, int]:
    if is_pipeline:
        # Enterprise batch workload: hundreds of thousands to millions of tokens.
        # Engineering/Product pipelines (full codebase, large dataset) trend larger.
        inp = max(50_000, int(np.random.lognormal(14.0, 0.9)))   # mean ≈ 1.4M
        out = max(5_000,  int(np.random.lognormal(11.8, 0.7)))   # mean ≈ 130K
        if team in ("Engineering", "Product"):
            inp = int(inp * random.uniform(1.3, 3.0))
            out = int(out * random.uniform(1.1, 2.0))
        return min(inp, 10_000_000), min(out, 2_000_000)

    # Regular interactive API calls — realistic per-request sizes
    if usage == "embedding":
        return max(100, int(np.random.lognormal(6.5, 0.7))), 0

    if usage == "search":
        return (max(200,  int(np.random.lognormal(6.8, 0.6))),
                max(50,   int(np.random.lognormal(5.0, 0.5))))

    if usage == "code-gen":
        inp = max(500,  int(np.random.lognormal(9.5, 0.8)))   # mean ≈ 13K
        out = max(200,  int(np.random.lognormal(9.0, 0.8)))   # mean ≈ 8K
        return min(inp, 80_000), min(out, 40_000)

    if usage == "summarization":
        inp = max(1_000, int(np.random.lognormal(10.5, 0.7)))  # mean ≈ 36K
        out = max(200,   int(np.random.lognormal(7.5, 0.6)))
        return min(inp, 100_000), min(out, 10_000)

    if usage == "analysis":
        inp = max(500,  int(np.random.lognormal(10.0, 0.8)))  # mean ≈ 22K
        out = max(200,  int(np.random.lognormal(8.5, 0.7)))
        return min(inp, 80_000), min(out, 20_000)

    # chat / completion — shrink for Support (short ticket interactions)
    inp = max(200, int(np.random.lognormal(8.5, 0.9)))   # mean ≈ 5K
    out = max(100, int(np.random.lognormal(7.5, 0.9)))   # mean ≈ 1.8K
    if team == "Support":
        inp = max(200, int(inp * 0.35))
        out = max(100, int(out * 0.35))
    return min(inp, 40_000), min(out, 15_000)


# ── Main generator ────────────────────────────────────────────────────────────
def generate(target_total: float = 12_000.0) -> pd.DataFrame:
    # Build per-team user pools
    users_by_team: dict[str, list] = {}
    for team, (budget, size, _) in TEAMS.items():
        users_by_team[team] = [
            (f"{team[:3].lower()}_{i+1:03d}", team, budget)
            for i in range(size)
        ]

    # Build ordered list of team assignments based on target row counts
    assignments: list[str] = []
    for team, (_, _, target) in TEAMS.items():
        assignments.extend([team] * target)
    random.shuffle(assignments)

    rows = []
    for team in assignments:
        uid, _, budget = random.choice(users_by_team[team])
        is_pipeline = random.random() < PIPELINE_PCT[team]

        # Pipeline rows bias toward premium providers
        if is_pipeline:
            pw = [w * 1.5 if i < 2 else w for i, w in enumerate(PROVIDER_WEIGHTS[team])]
            total_w = sum(pw)
            pw = [w / total_w for w in pw]
        else:
            pw = PROVIDER_WEIGHTS[team]

        provider = random.choices(PROVIDERS, weights=pw)[0]
        model    = _pick_model(team, provider, is_pipeline)

        usage = (
            random.choices(PIPELINE_USAGE, weights=PIPELINE_USAGE_W)[0]
            if is_pipeline
            else random.choices(USAGE_TYPES, weights=USAGE_WEIGHTS[team])[0]
        )

        inp, out = _token_counts(usage, is_pipeline, team)
        ci, co   = COSTS[model]
        cost     = round((inp * ci + out * co) / 1_000_000, 6)

        # beta(2,1) skews towards recent dates; business hours bias
        offset = int(np.random.beta(2, 1) * 90)
        ts = START + pd.Timedelta(
            days=offset,
            hours=random.randint(7, 21),
            minutes=random.randint(0, 59),
        )

        rows.append({
            "request_id":     str(uuid.uuid4()),
            "timestamp":      ts.strftime("%Y-%m-%d %H:%M:%S"),
            "team":           team,
            "user_id":        uid,
            "provider":       provider,
            "model_or_tool":  model,
            "usage_type":     usage,
            "input_tokens":   inp,
            "output_tokens":  out,
            "cost_usd":       cost,
            "monthly_budget": budget,
        })

    df = pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)

    # Scale to enterprise target.
    # Pipeline jobs naturally represent batch workloads but raw API cost still
    # undershoots what enterprises pay when including gateway, observability,
    # and support overhead (typically 2–5x raw token cost). Scaling preserves
    # all relative cost ratios between teams, models, and usage types.
    raw_total = df["cost_usd"].sum()
    factor    = target_total / raw_total if raw_total > 0 else 1.0
    df["cost_usd"] = (df["cost_usd"] * factor).round(4)

    os.makedirs("data", exist_ok=True)
    df.to_csv("data/ai_usage_mock.csv", index=False)

    final_total = df["cost_usd"].sum()
    print(f"✅  Generated {len(df)} rows → data/ai_usage_mock.csv")
    print(f"    Raw API cost:     ${raw_total:>10,.2f}")
    print(f"    Scaling factor:   {factor:>10.2f}x  (enterprise overhead incl.)")
    print(f"    Final total cost: ${final_total:>10,.2f}")
    print()
    print("Cost by team:")
    print(df.groupby("team")["cost_usd"].sum().sort_values(ascending=False).to_string())
    print()
    print("Cost by model:")
    print(df.groupby("model_or_tool")["cost_usd"].sum().sort_values(ascending=False).to_string())
    print()
    print("Rows by team:")
    print(df["team"].value_counts().sort_index().to_string())
    return df


if __name__ == "__main__":
    generate()
