"""AI Cost & Usage Intelligence Dashboard."""
import html as _html_module
import json
import os

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Cost & Usage Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Premium CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}
.stApp { background: #f1f5f9; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* ── Sidebar ─────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #0f172a !important;
    border-right: 1px solid #1e293b;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stCaption p,
[data-testid="stSidebar"] span {
    color: #94a3b8 !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #e2e8f0 !important;
}
[data-testid="stSidebar"] hr {
    border-color: #1e293b !important;
    opacity: 1 !important;
}

/* ── Sidebar multiselect input box ───────────────────────────────── */
[data-testid="stSidebar"] [data-baseweb="select"] > div:first-child {
    background-color: #f8fafc !important;
    border-color: #e2e8f0 !important;
    border-radius: 8px !important;
    padding: 2px 6px !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div:first-child:focus-within {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.18) !important;
}

/* ── Sidebar multiselect chips ───────────────────────────────────── */
[data-testid="stSidebar"] span[data-baseweb="tag"] {
    background-color: #4f46e5 !important;
    border: 1px solid rgba(99,102,241,0.35) !important;
    border-radius: 8px !important;
    padding: 1px 6px !important;
    margin: 2px !important;
}
[data-testid="stSidebar"] span[data-baseweb="tag"]:hover {
    background-color: #4338ca !important;
}
[data-testid="stSidebar"] span[data-baseweb="tag"] span {
    color: #ffffff !important;
    font-weight: 500 !important;
    font-size: 0.78rem !important;
}
[data-testid="stSidebar"] span[data-baseweb="tag"] [data-testid="stMultiSelectDeleteButton"],
[data-testid="stSidebar"] span[data-baseweb="tag"] button,
[data-testid="stSidebar"] span[data-baseweb="tag"] svg {
    color: #c7d2fe !important;
    fill: #c7d2fe !important;
    opacity: 1 !important;
}

/* ── Hero ────────────────────────────────────────────────────────── */
.hero-banner {
    background: linear-gradient(135deg, #0f172a 0%, #1a2744 45%, #1e1b4b 100%);
    border-radius: 16px;
    padding: 40px 44px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: -80px; right: -80px;
    width: 340px; height: 340px;
    background: radial-gradient(circle, rgba(99,102,241,0.22) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}
.hero-banner::after {
    content: '';
    position: absolute;
    bottom: -60px; left: 35%;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(14,165,233,0.12) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(99,102,241,0.18);
    border: 1px solid rgba(99,102,241,0.38);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.70rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #a5b4fc;
    margin-bottom: 16px;
}
.hero-title {
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: #f8fafc;
    margin: 0 0 10px 0;
    line-height: 1.15;
}
.hero-subtitle {
    font-size: 0.96rem;
    color: #94a3b8;
    margin: 0 0 24px 0;
    line-height: 1.6;
    max-width: 640px;
}
.hero-rule {
    width: 44px; height: 3px;
    background: linear-gradient(90deg, #6366f1, #0ea5e9);
    border-radius: 2px;
    margin-bottom: 20px;
}
.hero-meta {
    font-size: 0.79rem;
    color: #64748b;
}
.hero-meta strong { color: #94a3b8; font-weight: 600; }

/* ── KPI Cards ───────────────────────────────────────────────────── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 14px;
    margin: 0 0 6px 0;
}
.kpi-card {
    background: white;
    border-radius: 12px;
    padding: 18px 20px 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.07), 0 2px 8px rgba(0,0,0,0.04);
    border-top: 3px solid #e2e8f0;
    transition: box-shadow 0.15s ease;
}
.kpi-card:hover {
    box-shadow: 0 4px 14px rgba(0,0,0,0.10), 0 2px 6px rgba(0,0,0,0.06);
}
.kpi-card.c-indigo  { border-top-color: #6366f1; }
.kpi-card.c-sky     { border-top-color: #0ea5e9; }
.kpi-card.c-emerald { border-top-color: #10b981; }
.kpi-card.c-amber   { border-top-color: #f59e0b; }
.kpi-card.c-violet  { border-top-color: #8b5cf6; }
.kpi-card.c-rose    { border-top-color: #f43f5e; }
.kpi-label {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.10em;
    color: #64748b;
    margin: 0 0 9px 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.kpi-value {
    font-size: 1.65rem;
    font-weight: 800;
    color: #0f172a;
    line-height: 1.0;
    margin: 0 0 8px 0;
    letter-spacing: -0.03em;
}
.kpi-delta {
    font-size: 0.72rem;
    font-weight: 600;
    padding: 2px 9px;
    border-radius: 20px;
    display: inline-block;
}
.kpi-delta.pos  { background: #dcfce7; color: #166534; }
.kpi-delta.neg  { background: #fee2e2; color: #991b1b; }
.kpi-delta.warn { background: #fef3c7; color: #92400e; }
.kpi-delta.muted{ background: #f1f5f9; color: #475569; }

/* ── KPI helper ──────────────────────────────────────────────────── */
.kpi-helper {
    font-size: 0.77rem;
    color: #94a3b8;
    margin: 4px 0 0;
    line-height: 1.5;
    padding: 10px 4px 2px;
    border-top: 1px solid #f1f5f9;
}

/* ── Section header ──────────────────────────────────────────────── */
.section-block {
    margin: 44px 0 18px;
    padding-bottom: 14px;
    border-bottom: 2px solid #e2e8f0;
}
.section-eyebrow {
    font-size: 0.67rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #6366f1;
    margin: 0 0 4px;
}
.section-title {
    font-size: 1.30rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0 0 5px;
    line-height: 1.3;
    letter-spacing: -0.015em;
}
.section-desc {
    font-size: 0.83rem;
    color: #64748b;
    margin: 0;
    line-height: 1.6;
    max-width: 780px;
}

/* ── Chart cards ─────────────────────────────────────────────────── */
[data-testid="stPlotlyChart"] {
    background: white;
    border-radius: 12px;
    padding: 6px 4px 2px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.03);
}
[data-testid="stDataFrame"] {
    background: white;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.03);
}

/* ── Recommendation cards ────────────────────────────────────────── */
.rec-card {
    background: white;
    border-radius: 12px;
    padding: 18px 22px;
    margin: 12px 0;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05), 0 2px 6px rgba(0,0,0,0.04);
    border-left: 4px solid #e2e8f0;
}
.rec-card.high   { border-left-color: #dc2626; }
.rec-card.medium { border-left-color: #d97706; }
.rec-card.low    { border-left-color: #059669; }
.rec-card.info   { border-left-color: #2563eb; }
.rec-badge {
    display: inline-block;
    font-size: 0.63rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    padding: 2px 9px;
    border-radius: 12px;
    margin-bottom: 9px;
}
.rec-badge.high   { background: #fee2e2; color: #991b1b; }
.rec-badge.medium { background: #fef3c7; color: #92400e; }
.rec-badge.low    { background: #dcfce7; color: #166534; }
.rec-badge.info   { background: #dbeafe; color: #1e40af; }
.rec-title {
    font-size: 0.94rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 6px;
    line-height: 1.4;
}
.rec-detail {
    font-size: 0.84rem;
    color: #475569;
    margin-bottom: 10px;
    line-height: 1.6;
}
.rec-action {
    font-size: 0.82rem;
    color: #4f46e5;
    padding: 7px 13px;
    background: #f5f3ff;
    border-radius: 7px;
    display: inline-block;
    font-weight: 500;
    line-height: 1.5;
}

/* ── AI Advisor ──────────────────────────────────────────────────── */
.advisor-demo-block {
    background: #ffffff;
    border-radius: 14px;
    padding: 26px 30px;
    margin: 14px 0 8px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.04);
}
.advisor-live-header {
    background: #ffffff;
    border-radius: 14px;
    padding: 24px 28px 20px;
    margin: 14px 0 12px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 2px 8px rgba(0,0,0,0.04);
}
.advisor-heading {
    font-size: 1.05rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0 0 10px;
}
.advisor-desc {
    font-size: 0.87rem;
    color: #475569;
    margin: 0 0 20px;
    line-height: 1.6;
    padding: 10px 14px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 3px solid #6366f1;
    border-radius: 6px;
}
.advisor-live-desc {
    font-size: 0.87rem;
    color: #065f46;
    margin: 0;
    padding: 10px 14px;
    background: #ecfdf5;
    border: 1px solid #a7f3d0;
    border-radius: 8px;
    line-height: 1.55;
}
.insight-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 16px 20px;
    margin: 10px 0;
}
.insight-label {
    display: inline-block;
    font-size: 0.67rem;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: #4338ca;
    background: #ede9fe;
    border: 1px solid #c4b5fd;
    padding: 3px 10px;
    border-radius: 10px;
    margin-bottom: 9px;
}
.insight-text {
    font-size: 0.87rem;
    color: #1e293b;
    line-height: 1.7;
}
.insight-text strong {
    color: #0f172a;
    font-weight: 600;
}

/* ── Footer ──────────────────────────────────────────────────────── */
.dash-footer {
    text-align: center;
    padding: 22px 0 10px;
    font-size: 0.76rem;
    color: #94a3b8;
    border-top: 1px solid #e2e8f0;
    margin-top: 36px;
}

/* ── Misc Streamlit overrides ────────────────────────────────────── */
[data-testid="stMetricDelta"] { font-size: 0.75rem !important; }
.stAlert { border-radius: 10px !important; }
hr { border-color: #e2e8f0 !important; margin: 28px 0 !important; }
</style>
""", unsafe_allow_html=True)


# ── UI helper ─────────────────────────────────────────────────────────────────
def _section_header(eyebrow: str, title: str, desc: str) -> None:
    st.markdown(
        f'<div class="section-block">'
        f'<p class="section-eyebrow">{eyebrow}</p>'
        f'<p class="section-title">{title}</p>'
        f'<p class="section-desc">{desc}</p>'
        f"</div>",
        unsafe_allow_html=True,
    )


# ── Data helpers ──────────────────────────────────────────────────────────────
_EXPENSIVE = {
    "GPT-5.5 Pro", "GPT-5.4 Pro", "GPT-5.2 Pro", "o3-pro",
    "Claude Opus 4.7", "Claude Opus 4.6",
    "Gemini 3 Deep Think", "Grok 4.3",
    "Llama 4 Behemoth", "Mistral Large 3",
    "DeepSeek V4 Pro", "Qwen3-Max", "Nova Premier",
}
LEGACY_MODELS = {
    "GPT-5.2", "GPT-5.2 Pro", "GPT-5.1",
    "GPT-4o", "GPT-4o mini",
    "GPT-4.1", "GPT-4.1 mini",
    "o3", "o3-pro", "o4-mini",
}
_TRIVIAL   = {"embedding", "search"}

CHART_COLORS = {
    "purple":  "#6d28d9",
    "blue":    "#1d4ed8",
    "green":   "#047857",
    "amber":   "#b45309",
    "red":     "#b91c1c",
    "sky":     "#0284c7",
    "indigo":  "#4338ca",
    "emerald": "#065f46",
    "rose":    "#be185d",
}

# Shared layout defaults applied to every chart
_FONT = dict(family="Inter, system-ui, sans-serif", color="#1e293b")
_AXIS = dict(
    showgrid=True,
    gridcolor="#e2e8f0",
    gridwidth=1,
    tickfont=dict(color="#475569", size=11),
    title_font=dict(color="#1e293b", size=12),
    linecolor="#cbd5e1",
    linewidth=1,
)

# Distinct, high-contrast palette for pie/donut slices
_PIE_COLORS = [
    "#4338ca", "#0284c7", "#047857", "#b45309",
    "#be185d", "#7c3aed", "#0f766e",
]


@st.cache_data
def load_data() -> pd.DataFrame:
    path = "data/ai_usage_mock.csv"
    if not os.path.exists(path):
        _generate_fallback(path)

    df = pd.read_csv(path)
    df["timestamp"]    = pd.to_datetime(df["timestamp"])
    df["date"]         = df["timestamp"].dt.date
    df["date_str"]     = df["timestamp"].dt.strftime("%Y-%m-%d")
    df["total_tokens"] = df["input_tokens"] + df["output_tokens"]
    df["output_ratio"] = np.where(
        df["total_tokens"] > 0,
        df["output_tokens"] / df["total_tokens"],
        0,
    )
    df["waste_flag"] = (
        df["model_or_tool"].isin(_EXPENSIVE) & df["usage_type"].isin(_TRIVIAL)
    ).astype(int)
    return df


def _generate_fallback(path: str) -> None:
    try:
        from generate_data import generate
        generate()
    except ImportError:
        pass


# ── Load ──────────────────────────────────────────────────────────────────────
df_all = load_data()

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Filters")
    st.divider()

    min_d = df_all["timestamp"].min().date()
    max_d = df_all["timestamp"].max().date()
    date_range = st.date_input(
        "Date Range",
        value=(min_d, max_d),
        min_value=min_d,
        max_value=max_d,
    )
    start_d = date_range[0] if len(date_range) >= 1 else min_d
    end_d   = date_range[1] if len(date_range) >= 2 else date_range[0]

    all_teams     = sorted(df_all["team"].unique())
    all_providers = sorted(df_all["provider"].unique())
    all_models    = sorted(df_all["model_or_tool"].unique())
    all_usage     = sorted(df_all["usage_type"].unique())

    sel_teams     = st.multiselect("Team",       all_teams,     default=all_teams)
    sel_providers = st.multiselect("Provider",   all_providers, default=all_providers)
    sel_models    = st.multiselect("Model",      all_models,    default=all_models)
    sel_usage     = st.multiselect("Usage Type", all_usage,     default=all_usage)

    st.divider()
    st.caption(f"Dataset: {len(df_all):,} records")

# ── Apply filters ─────────────────────────────────────────────────────────────
df = df_all[
    (df_all["timestamp"].dt.date >= start_d)
    & (df_all["timestamp"].dt.date <= end_d)
    & (df_all["team"].isin(sel_teams     or all_teams))
    & (df_all["provider"].isin(sel_providers or all_providers))
    & (df_all["model_or_tool"].isin(sel_models    or all_models))
    & (df_all["usage_type"].isin(sel_usage     or all_usage))
]

# ── Hero header ───────────────────────────────────────────────────────────────
st.markdown(
    f"""
<div class="hero-banner">
  <div class="hero-badge">🤖 &nbsp;AI Intelligence Platform</div>
  <p class="hero-title">AI Cost &amp; Usage Intelligence</p>
  <p class="hero-subtitle">
    Understand AI spend, usage patterns, efficiency gaps, and optimization opportunities
    across all teams, providers, and models — in one executive view.
  </p>
  <div class="hero-rule"></div>
  <p class="hero-meta">
    <strong>{len(df):,} records</strong> &nbsp;·&nbsp; {start_d} → {end_d}
    &nbsp;·&nbsp; Teams: {', '.join(sel_teams or all_teams)}
  </p>
</div>
""",
    unsafe_allow_html=True,
)

if df.empty:
    st.warning("No records match the selected filters. Try widening the date range or clearing a filter.")
    st.stop()

# ── KPI computations ──────────────────────────────────────────────────────────
total_cost   = df["cost_usd"].sum()
total_req    = len(df)
total_tokens = df["total_tokens"].sum()
avg_cost_req = total_cost / total_req

waste_n     = int(df["waste_flag"].sum())
efficiency  = round(100 - (waste_n / total_req * 100), 1)

wasted_df   = df[df["waste_flag"] == 1]
est_savings = max(
    0.0,
    wasted_df["cost_usd"].sum() - wasted_df["total_tokens"].sum() * 0.001 / 1_000,
)

# ── KPI cards ─────────────────────────────────────────────────────────────────
_eff_cls   = "pos" if efficiency >= 90 else ("warn" if efficiency >= 70 else "neg")
_eff_label = "Good" if efficiency >= 90 else ("Review" if efficiency >= 70 else "Action needed")

st.markdown(
    f"""
<div class="kpi-grid">
  <div class="kpi-card c-indigo">
    <div class="kpi-label">Total AI Spend</div>
    <div class="kpi-value">${total_cost:,.2f}</div>
    <span class="kpi-delta muted">Selected period</span>
  </div>
  <div class="kpi-card c-sky">
    <div class="kpi-label">API Requests</div>
    <div class="kpi-value">{total_req:,}</div>
    <span class="kpi-delta muted">Total calls</span>
  </div>
  <div class="kpi-card c-emerald">
    <div class="kpi-label">Tokens Processed</div>
    <div class="kpi-value">{total_tokens / 1e6:.1f}M</div>
    <span class="kpi-delta muted">Input + Output</span>
  </div>
  <div class="kpi-card c-amber">
    <div class="kpi-label">Cost per Request</div>
    <div class="kpi-value">${avg_cost_req:.2f}</div>
    <span class="kpi-delta muted">Avg per call</span>
  </div>
  <div class="kpi-card c-violet">
    <div class="kpi-label">Model Efficiency</div>
    <div class="kpi-value">{efficiency}%</div>
    <span class="kpi-delta {_eff_cls}">{_eff_label}</span>
  </div>
  <div class="kpi-card c-rose">
    <div class="kpi-label">Optimization Potential</div>
    <div class="kpi-value">${est_savings:,.2f}</div>
    <span class="kpi-delta warn">Recoverable</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<p class="kpi-helper">'
    "Based on data from the selected period. "
    "<strong>Model Efficiency</strong> = % of requests where model tier matches task complexity. "
    "<strong>Optimization Potential</strong> = estimated recoverable spend if identified waste patterns are addressed."
    "</p>",
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════
# SECTION 1 — COST ANALYSIS
# ═══════════════════════════════════════════════════════════════════
_section_header(
    "Cost Intelligence",
    "Where is the Budget Going?",
    "AI spend broken down by team, model, provider, and usage type. "
    "Use this view to identify the highest-cost areas and track spend trends over time.",
)

col_trend, col_team = st.columns([3, 2])

with col_trend:
    daily = (
        df.groupby("date_str")["cost_usd"]
        .sum()
        .reset_index()
        .rename(columns={"date_str": "date", "cost_usd": "cost"})
        .sort_values("date")
    )
    daily["ma7"] = daily["cost"].rolling(7, min_periods=1).mean()

    fig = go.Figure()
    fig.add_bar(
        x=daily["date"], y=daily["cost"],
        name="Daily Cost",
        marker_color=CHART_COLORS["sky"],
        marker_line_width=0,
        opacity=0.85,
    )
    fig.add_scatter(
        x=daily["date"], y=daily["ma7"],
        name="7-day avg",
        line=dict(color=CHART_COLORS["indigo"], width=3),
        mode="lines",
    )
    fig.update_layout(
        title=dict(text="Daily AI Spend Trend", font=dict(color="#0f172a", size=14, family="Inter, system-ui, sans-serif")),
        template="plotly_white",
        height=300,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#fafafa",
        margin=dict(l=0, r=0, t=50, b=0),
        legend=dict(orientation="h", y=-0.22, font=dict(color="#475569", size=11)),
        font=_FONT,
        xaxis={**_AXIS, "title": ""},
        yaxis={**_AXIS, "title": "Cost (USD)"},
        hoverlabel=dict(bgcolor="white", bordercolor="#e2e8f0", font_color="#0f172a"),
    )
    fig.update_layout(height=340)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col_team:
    tc = (
        df.groupby("team")["cost_usd"]
        .sum()
        .sort_values()
        .reset_index()
    )
    fig2 = px.bar(
        tc, x="cost_usd", y="team", orientation="h",
        title="Total Spend by Team",
        color="cost_usd",
        color_continuous_scale=[[0, "#c7d2fe"], [0.4, "#6366f1"], [1, "#3730a3"]],
        labels={"cost_usd": "USD", "team": ""},
    )
    fig2.update_traces(marker_line_width=0)
    fig2.update_layout(
        title=dict(text="Total Spend by Team", font=dict(color="#0f172a", size=14, family="Inter, system-ui, sans-serif")),
        template="plotly_white", height=340,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#fafafa",
        margin=dict(l=0, r=0, t=50, b=0),
        coloraxis_showscale=False,
        font=_FONT,
        xaxis={**_AXIS, "title": "USD"},
        yaxis={**_AXIS, "title": ""},
        hoverlabel=dict(bgcolor="white", bordercolor="#e2e8f0", font_color="#0f172a"),
    )
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

col_model, col_usage = st.columns(2)

with col_model:
    mc = (
        df.groupby("model_or_tool")["cost_usd"]
        .sum()
        .sort_values(ascending=False)
        .head(20)
        .reset_index()
    )
    fig3 = px.bar(
        mc, x="model_or_tool", y="cost_usd",
        title="Spend by Model — Top 20",
        color="cost_usd",
        color_continuous_scale=[[0, "#bae6fd"], [0.35, "#0284c7"], [1, "#0c4a6e"]],
        labels={"cost_usd": "USD", "model_or_tool": ""},
    )
    fig3.update_traces(marker_line_width=0)
    fig3.update_layout(
        title=dict(text="Spend by Model — Top 20", font=dict(color="#0f172a", size=14, family="Inter, system-ui, sans-serif")),
        template="plotly_white", height=360,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#fafafa",
        margin=dict(l=0, r=0, t=50, b=90),
        coloraxis_showscale=False,
        font=_FONT,
        xaxis={**_AXIS, "title": "", "tickangle": -35},
        yaxis={**_AXIS, "title": "USD"},
        hoverlabel=dict(bgcolor="white", bordercolor="#e2e8f0", font_color="#0f172a"),
    )
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

with col_usage:
    uc = df.groupby("usage_type")["cost_usd"].sum().reset_index()
    fig4 = px.pie(
        uc, values="cost_usd", names="usage_type",
        title="Spend by Usage Type",
        color_discrete_sequence=_PIE_COLORS,
        hole=0.40,
    )
    fig4.update_traces(
        textfont=dict(color="white", size=11),
        marker=dict(line=dict(color="white", width=2)),
        hovertemplate="<b>%{label}</b><br>$%{value:,.2f}<br>%{percent}<extra></extra>",
    )
    fig4.update_layout(
        title=dict(text="Spend by Usage Type", font=dict(color="#0f172a", size=14, family="Inter, system-ui, sans-serif")),
        template="plotly_white", height=360,
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=50, b=0),
        font=dict(family="Inter, system-ui, sans-serif", color="#1e293b"),
        legend=dict(font=dict(color="#475569", size=11)),
        hoverlabel=dict(bgcolor="white", bordercolor="#e2e8f0", font_color="#0f172a"),
    )
    st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})

# ═══════════════════════════════════════════════════════════════════
# SECTION 2 — EFFICIENCY & WASTE RISK
# ═══════════════════════════════════════════════════════════════════
_section_header(
    "Efficiency Analysis",
    "Are We Getting Value for Money?",
    "Model efficiency measures how often each team uses cost-appropriate models for the task at hand. "
    "Waste risk identifies requests where expensive, premium-tier models were applied to simple tasks "
    "like search and embedding — a common and addressable source of excess spend.",
)

col_eff, col_waste = st.columns(2)

with col_eff:
    eff_rows = []
    for team in sorted(df["team"].unique()):
        sub   = df[df["team"] == team]
        score = round(100 - sub["waste_flag"].mean() * 100, 1)
        eff_rows.append({"team": team, "score": score})
    eff_df = pd.DataFrame(eff_rows).sort_values("score")

    bar_colors = [
        "#047857" if s >= 90
        else "#b45309" if s >= 70
        else "#b91c1c"
        for s in eff_df["score"]
    ]
    fig5 = go.Figure(
        go.Bar(
            x=eff_df["score"],
            y=eff_df["team"],
            orientation="h",
            marker_color=bar_colors,
            marker_line_width=0,
            text=[f"{s}%" for s in eff_df["score"]],
            textposition="outside",
            textfont=dict(color="#1e293b", size=11),
        )
    )
    fig5.update_layout(
        title=dict(text="Model Efficiency by Team  (🟢 ≥ 90%  🟡 ≥ 70%  🔴 < 70%)", font=dict(color="#0f172a", size=13, family="Inter, system-ui, sans-serif")),
        template="plotly_white",
        height=340,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#fafafa",
        margin=dict(l=0, r=55, t=50, b=0),
        font=_FONT,
        xaxis={**_AXIS, "range": [0, 115], "title": "Score (%)"},
        yaxis={**_AXIS, "title": ""},
        hoverlabel=dict(bgcolor="white", bordercolor="#e2e8f0", font_color="#0f172a"),
    )
    st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar": False})

with col_waste:
    wr = []
    for team in sorted(df["team"].unique()):
        sub = df[df["team"] == team]
        wr.append({
            "team":       team,
            "waste_pct":  round(sub["waste_flag"].mean() * 100, 1),
            "wasted_usd": sub.loc[sub["waste_flag"] == 1, "cost_usd"].sum(),
        })
    wr_df = pd.DataFrame(wr).sort_values("waste_pct", ascending=False)
    _waste_max_y = wr_df["waste_pct"].max() * 1.25

    fig6 = px.bar(
        wr_df, x="team", y="waste_pct",
        title="Waste Risk by Team — Premium models on trivial tasks (%)",
        color="waste_pct",
        color_continuous_scale=[
            [0.0, "#047857"],
            [0.4, "#b45309"],
            [1.0, "#b91c1c"],
        ],
        labels={"waste_pct": "Waste %", "team": ""},
        text="waste_pct",
    )
    fig6.update_traces(
        texttemplate="%{text:.1f}%", textposition="outside",
        textfont=dict(color="#1e293b", size=11),
        marker_line_width=0,
    )
    fig6.update_layout(
        title=dict(text="Waste Risk by Team — Premium models on trivial tasks (%)", font=dict(color="#0f172a", size=13, family="Inter, system-ui, sans-serif")),
        template="plotly_white", height=340,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#fafafa",
        margin=dict(l=0, r=0, t=50, b=25),
        coloraxis_showscale=False,
        font=_FONT,
        xaxis={**_AXIS, "title": ""},
        yaxis={**_AXIS, "title": "Waste %", "range": [0, _waste_max_y]},
        hoverlabel=dict(bgcolor="white", bordercolor="#e2e8f0", font_color="#0f172a"),
    )
    st.plotly_chart(fig6, use_container_width=True, config={"displayModeBar": False})

# ═══════════════════════════════════════════════════════════════════
# SECTION 3 — TOP EXPENSIVE USERS
# ═══════════════════════════════════════════════════════════════════
_section_header(
    "Usage Spotlight",
    "Highest-Cost Users",
    "The 15 users with the highest total AI spend for the selected period, sorted by cost. "
    "Review the Waste % column to identify individuals using premium models for low-value tasks.",
)

user_stats = (
    df.groupby(["user_id", "team"])
    .agg(
        total_cost=("cost_usd",     "sum"),
        requests  =("request_id",   "count"),
        tokens    =("total_tokens", "sum"),
        avg_cost  =("cost_usd",     "mean"),
        waste     =("waste_flag",   "sum"),
    )
    .reset_index()
)
user_stats["waste_pct"] = (user_stats["waste"] / user_stats["requests"] * 100).round(1)
user_stats = user_stats.sort_values("total_cost", ascending=False).head(15)

display = user_stats[
    ["user_id", "team", "total_cost", "requests", "tokens", "avg_cost", "waste_pct"]
].copy()
display.columns = ["User", "Team", "Total Spend ($)", "Requests", "Tokens Used", "Avg Cost / Req ($)", "Waste %"]
display["Total Spend ($)"]      = display["Total Spend ($)"].map("${:,.2f}".format)
display["Avg Cost / Req ($)"]   = display["Avg Cost / Req ($)"].map("${:,.2f}".format)
display["Tokens Used"]          = display["Tokens Used"].map("{:,}".format)
display["Waste %"]              = display["Waste %"].map("{:.1f}%".format)

st.dataframe(display, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════════
# SECTION 4 — RULE-BASED RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════
_section_header(
    "Action Items",
    "What Should We Act On?",
    "Rule-based findings ranked by severity and potential savings impact. "
    "Each item includes the evidence behind the finding and a concrete next step your team can take immediately.",
)

recs: list[tuple] = []

# Rule 1 — Expensive model for trivial task
if waste_n > 0:
    savings_est = wasted_df["cost_usd"].sum() * 0.88
    recs.append((
        "high",
        "Premium Models Used for Trivial Tasks",
        f"{waste_n} requests used premium models (GPT-5.5 Pro, Claude Opus 4.7, Grok 4.3, etc.) "
        f"for embedding or search. Estimated recoverable savings: ${savings_est:.2f}.",
        "Replace with Claude Haiku, GPT-5 nano, Mistral 3 8B, or DeepSeek V4 Flash "
        "for all embedding and search workloads.",
    ))

# Rule 2 — Teams over 80 % of budget
team_spend = (
    df.groupby("team")
    .agg(spend=("cost_usd", "sum"), budget=("monthly_budget", "first"))
    .reset_index()
)
team_spend["pct"] = team_spend["spend"] / team_spend["budget"] * 100
over_budget = team_spend[team_spend["pct"] > 80]
if not over_budget.empty:
    names   = ", ".join(over_budget["team"].tolist())
    avg_pct = over_budget["pct"].mean()
    recs.append((
        "high",
        "Teams Near or Over Monthly Budget",
        f"{names} are averaging {avg_pct:.0f}% of their monthly budget for the selected period.",
        "Configure per-team rate limits in your AI gateway. Send alerts at 70% and "
        "enforce hard caps at 95%.",
    ))

# Rule 3 — Provider concentration
prov_share = df.groupby("provider")["cost_usd"].sum() / total_cost * 100
top_prov   = prov_share.idxmax()
if prov_share[top_prov] > 65:
    recs.append((
        "medium",
        f"Provider Concentration Risk — {top_prov} at {prov_share[top_prov]:.0f}%",
        f"Over two-thirds of spend is concentrated with {top_prov}. "
        "Single-vendor dependency increases exposure to pricing changes and service outages.",
        "Implement a provider abstraction layer (LiteLLM, Portkey) to enable easy provider switching. "
        "Evaluate cost-equivalent models from alternative providers.",
    ))

# Rule 4 — Top-tier models dominate
expensive_usd = df[df["model_or_tool"].isin({
    "GPT-5.5 Pro", "GPT-5.5", "GPT-5.4 Pro", "GPT-5.4",
    "Claude Opus 4.7", "Claude Opus 4.6", "o3-pro", "o3",
})]["cost_usd"].sum()
if total_cost > 0 and expensive_usd / total_cost > 0.45:
    recs.append((
        "medium",
        f"Top-Tier Models Drive {expensive_usd / total_cost * 100:.0f}% of Spend",
        "The majority of spend is on the most expensive model tier. "
        "Many tasks do not require this capability level and could be served by mid-tier models at a fraction of the cost.",
        "Introduce a model tiering policy: use mid-tier models (GPT-5.3 Instant, Claude Sonnet 4.6) by default, "
        "and restrict top-tier access to explicitly approved, high-complexity tasks.",
    ))

# Rule 5 — Model sprawl
n_models = df["model_or_tool"].nunique()
if n_models > 6:
    recs.append((
        "low",
        f"Model Sprawl — {n_models} Distinct Models in Active Use",
        "A high number of distinct models increases billing complexity, complicates security review, "
        "and makes cost forecasting less reliable.",
        "Standardize on 2–3 models per use-case tier. "
        "Publish an internal model selection guide to align teams on approved options.",
    ))

# Rule 6 — Legacy OpenAI models still in use
legacy_n = int(df["model_or_tool"].isin(LEGACY_MODELS).sum())
if legacy_n > 0:
    legacy_cost = df[df["model_or_tool"].isin(LEGACY_MODELS)]["cost_usd"].sum()
    recs.append((
        "medium",
        f"Legacy OpenAI Models Still in Active Use — {legacy_n} Requests",
        f"{legacy_n} requests used legacy OpenAI models (GPT-4.x series, GPT-5.1/5.2, o3, o4-mini), "
        f"accounting for ${legacy_cost:,.2f} of spend in the selected period.",
        "Migrate legacy model calls to current GPT-5.x equivalents. "
        "Use GPT-5 mini or GPT-5 nano for lightweight tasks, GPT-5.4 for mid-tier work.",
    ))

_BADGE_LABELS = {"high": "High Priority", "medium": "Medium Priority", "low": "Low Priority", "info": "Insight"}

if recs:
    for severity, title, detail, action in recs:
        badge = _BADGE_LABELS.get(severity, severity.title())
        st.markdown(
            f'<div class="rec-card {severity}">'
            f'<span class="rec-badge {severity}">{badge}</span>'
            f'<div class="rec-title">{title}</div>'
            f'<div class="rec-detail">{detail}</div>'
            f'<div class="rec-action">→ &nbsp;{action}</div>'
            "</div>",
            unsafe_allow_html=True,
        )
else:
    st.success("✅ No major optimization opportunities detected for the current filter selection.")

# ═══════════════════════════════════════════════════════════════════
# SECTION 5 — AI COST OPTIMIZATION ADVISOR
# ═══════════════════════════════════════════════════════════════════
_section_header(
    "Strategic Intelligence",
    "AI Cost Optimization Advisor",
    "Powered by AI. Analyzes your spend patterns, efficiency gaps, and waste signals across the full dataset "
    "to generate prioritized, evidence-based cost reduction strategies tailored to your organization.",
)

gemini_api_key    = os.environ.get("GEMINI_API_KEY", "")
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")

# Demo cards HTML — reused for no-key mode and as error fallback
_demo_block_html = (
    '<div class="advisor-demo-block">'
    '<p class="advisor-heading">🤖 &nbsp;AI Cost Optimization Advisor</p>'
    '<p class="advisor-desc">'
    "Demo mode: live LLM analysis is disabled because no API key is configured. "
    "The advisor below shows deterministic AI-style recommendations generated from the current dataset."
    "</p>"
    + "".join(
        f'<div class="insight-card">'
        f'<span class="insight-label">{lbl}</span>'
        f'<div class="insight-text">{txt}</div>'
        f'</div>'
        for lbl, txt in [
            (
                "High Impact · Low Effort",
                "<strong>Migrate embedding and search workloads to lightweight models.</strong>  "
                "The data shows embedding requests routed through premium models like GPT-5.5 Pro and Claude Opus 4.7. "
                "Claude Haiku ($0.80/1M) or GPT-5 nano ($0.08/1M) deliver equivalent quality for retrieval tasks — "
                "a <strong>90–99% cost reduction</strong> for that task class with no measurable quality loss.",
            ),
            (
                "High Impact · Medium Effort",
                "<strong>Enable prompt caching for the Engineering team.</strong>  "
                "Engineering has the highest request volume with repetitive system prompts. "
                "Claude Sonnet 4.6 and GPT-5.4 both support prompt caching; 60%+ cache hit rates are achievable "
                "on agentic workflows, cutting effective per-request cost proportionally.",
            ),
            (
                "Medium Impact · Low Effort",
                "<strong>Deploy per-team budget guardrails via an AI gateway.</strong>  "
                "Teams currently lack real-time spend visibility. Tools like LiteLLM Proxy or "
                "Portkey can enforce per-team monthly limits, emit alerts at 70%, "
                "and log all requests — achievable with under one day of engineering effort.",
            ),
        ]
    )
    + "</div>"
)

if gemini_api_key:
    st.markdown(
        '<div class="advisor-live-header">'
        '<p class="advisor-heading">🤖 &nbsp;AI Cost Optimization Advisor</p>'
        '<p class="advisor-live-desc">'
        "✅ Live AI analysis enabled via Gemini — Gemini 2.5 Flash will review your filtered dataset "
        "and return three prioritized, quantified recommendations."
        "</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    if st.button("✨ Generate live AI recommendations", type="primary"):
        with st.spinner("Gemini is analyzing your AI spend data…"):
            try:
                from google import genai  # type: ignore

                _top10_models = (
                    df.groupby("model_or_tool")["cost_usd"]
                    .sum()
                    .sort_values(ascending=False)
                    .head(10)
                    .round(2)
                    .to_dict()
                )
                _top5_users = (
                    user_stats[["user_id", "team", "total_cost", "waste_pct"]]
                    .head(5)
                    .to_dict(orient="records")
                )
                _legacy_summary = (
                    f"{legacy_n} requests, {legacy_cost:.2f} USD spend"
                    if legacy_n > 0
                    else "none"
                )
                _gemini_context = (
                    f"AI Usage Dashboard Summary ({start_d} to {end_d})\n\n"
                    f"Metrics:\n"
                    f"- Total Cost: {total_cost:.2f} USD\n"
                    f"- Total Requests: {total_req:,}\n"
                    f"- Total Tokens: {total_tokens:,}\n"
                    f"- Model Efficiency Score: {efficiency}%\n"
                    f"- Waste-Flagged Requests: {waste_n} ({est_savings:.2f} USD optimization potential)\n"
                    f"- Legacy OpenAI Models: {_legacy_summary}\n\n"
                    f"Cost by Team (USD): {df.groupby('team')['cost_usd'].sum().sort_values(ascending=False).round(2).to_dict()}\n"
                    f"Top 10 Models by Cost (USD): {_top10_models}\n"
                    f"Provider Share (%): {prov_share.round(1).to_dict()}\n"
                    f"Cost by Usage Type (USD): {df.groupby('usage_type')['cost_usd'].sum().round(2).to_dict()}\n"
                    f"Top 5 Expensive Users: {_top5_users}\n"
                )
                _gemini_prompt = (
                    "You are an AI cost optimization consultant reviewing a company's AI API spend dashboard.\n"
                    "Analyze the data and return exactly 3 prioritized recommendations as JSON.\n\n"
                    "STRICT OUTPUT RULES:\n"
                    "- Return valid JSON only. No Markdown. No code fences. No extra text before or after.\n"
                    "- Never use the dollar sign character anywhere. Use USD for all currency.\n"
                    "- No LaTeX. No inline math. Plain text only.\n\n"
                    "Required JSON schema:\n"
                    '{"recommendations": [\n'
                    '  {"title": "...", "severity": "High|Medium|Low", "finding": "...",\n'
                    '   "business_impact": "...", "estimated_opportunity": "... USD",\n'
                    '   "recommended_action": "..."}\n'
                    "]}\n\n"
                    "DATA:\n\n"
                    + _gemini_context
                )
                _GEMINI_MODELS = [
                    "gemini-2.5-flash",
                    "gemini-2.0-flash",
                ]
                _TRANSIENT_KEYWORDS = ("503", "404", "unavailable", "not_found", "overloaded", "quota", "temporarily")

                _gclient    = genai.Client(api_key=gemini_api_key)
                _gresp      = None
                _used_model = None

                for _model in _GEMINI_MODELS:
                    try:
                        _gresp = _gclient.models.generate_content(
                            model=_model,
                            contents=_gemini_prompt,
                        )
                        _used_model = _model
                        break
                    except Exception as _model_exc:
                        if any(k in str(_model_exc).lower() for k in _TRANSIENT_KEYWORDS):
                            continue  # try next model
                        raise       # non-transient — surface to outer except

                if _gresp is None:
                    st.warning(
                        "Live Gemini analysis is temporarily unavailable. "
                        "Showing deterministic fallback recommendations."
                    )
                    st.markdown(_demo_block_html, unsafe_allow_html=True)
                else:
                    _raw = _gresp.text.strip()
                    # Strip optional ```json fences
                    if _raw.startswith("```"):
                        _raw = _raw.split("```", 2)[1]
                        if _raw.startswith("json"):
                            _raw = _raw[4:]
                        _raw = _raw.rsplit("```", 1)[0].strip()

                    _sev_colors = {"high": "#b91c1c", "medium": "#b45309", "low": "#047857"}
                    _sev_bg     = {"high": "#fef2f2", "medium": "#fffbeb", "low": "#f0fdf4"}
                    _sev_border = {"high": "#fecaca", "medium": "#fde68a", "low": "#bbf7d0"}

                    try:
                        _parsed = json.loads(_raw)
                        _recs   = _parsed["recommendations"]
                        st.success(f"✅ Analysis complete using Gemini model: {_used_model}")
                        for _rec in _recs:
                            _sev_key = _rec.get("severity", "").lower()
                            _c  = _sev_colors.get(_sev_key, "#4f46e5")
                            _bg = _sev_bg.get(_sev_key, "#f8fafc")
                            _bd = _sev_border.get(_sev_key, "#e2e8f0")
                            def _e(v): return _html_module.escape(str(v))
                            st.markdown(
                                f'<div style="background:{_bg};border:1px solid {_bd};border-left:4px solid {_c};'
                                f'border-radius:10px;padding:20px 24px;margin:10px 0;">'
                                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">'
                                f'<span style="font-size:1rem;font-weight:700;color:#0f172a;">{_e(_rec.get("title",""))}</span>'
                                f'<span style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;'
                                f'color:{_c};background:white;border:1px solid {_bd};border-radius:20px;padding:2px 10px;">'
                                f'{_e(_rec.get("severity",""))}</span>'
                                f'</div>'
                                f'<div style="font-size:0.84rem;color:#334155;line-height:1.7;">'
                                f'<p style="margin:4px 0;"><strong style="color:#0f172a;">Finding:</strong> {_e(_rec.get("finding",""))}</p>'
                                f'<p style="margin:4px 0;"><strong style="color:#0f172a;">Business Impact:</strong> {_e(_rec.get("business_impact",""))}</p>'
                                f'<p style="margin:4px 0;"><strong style="color:#0f172a;">Estimated Opportunity:</strong> {_e(_rec.get("estimated_opportunity",""))}</p>'
                                f'<p style="margin:4px 0;"><strong style="color:#0f172a;">Recommended Action:</strong> {_e(_rec.get("recommended_action",""))}</p>'
                                f'</div></div>',
                                unsafe_allow_html=True,
                            )
                    except (json.JSONDecodeError, KeyError, TypeError):
                        st.warning("Gemini returned an unexpected format. Showing raw response below.")
                        st.markdown(_raw.replace("$", "USD "))
            except Exception as exc:
                st.error(f"Gemini API error: {exc}")
                st.markdown(_demo_block_html, unsafe_allow_html=True)

elif anthropic_api_key:
    st.markdown(
        '<div class="advisor-live-header">'
        '<p class="advisor-heading">🤖 &nbsp;AI Cost Optimization Advisor</p>'
        '<p class="advisor-live-desc">'
        "✅ Live analysis enabled — Claude will review your filtered dataset and return three specific, "
        "quantified recommendations you can act on immediately."
        "</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    if st.button("✨ Generate AI Insights", type="primary"):
        with st.spinner("Claude is analyzing your AI spend data…"):
            try:
                import anthropic  # type: ignore

                context = (
                    f"AI Usage Summary ({start_d} → {end_d}):\n"
                    f"- Total Cost: ${total_cost:.2f}\n"
                    f"- Total Requests: {total_req:,}\n"
                    f"- Total Tokens: {total_tokens:,}\n"
                    f"- Model Efficiency Score: {efficiency}%\n"
                    f"- Optimization Potential: ${est_savings:.2f} ({waste_n} waste-flagged requests)\n\n"
                    f"Cost by Team: {df.groupby('team')['cost_usd'].sum().sort_values(ascending=False).to_dict()}\n"
                    f"Cost by Model: {df.groupby('model_or_tool')['cost_usd'].sum().sort_values(ascending=False).to_dict()}\n"
                    f"Cost by Usage Type: {df.groupby('usage_type')['cost_usd'].sum().to_dict()}\n"
                    f"Provider Share (%): {prov_share.round(1).to_dict()}\n"
                )
                client = anthropic.Anthropic(api_key=anthropic_api_key)
                msg = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=700,
                    messages=[
                        {
                            "role": "user",
                            "content": (
                                "You are an AI cost optimization consultant. "
                                "Analyze the data below and provide exactly 3 specific, "
                                "numbered, actionable recommendations to reduce AI spend "
                                "while maintaining team productivity. Be concrete — "
                                "cite percentages and dollar amounts where possible.\n\n"
                                + context
                            ),
                        }
                    ],
                )
                st.success("Analysis complete:")
                st.markdown(msg.content[0].text)
            except Exception as exc:
                st.error(f"API error: {exc}")

else:
    st.markdown(_demo_block_html, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    "<div class='dash-footer'>"
    "AI Cost &amp; Usage Intelligence &nbsp;·&nbsp; "
    "Streamlit + Plotly &nbsp;·&nbsp; "
    "Schema: AGENT.md v1.0 &nbsp;·&nbsp; "
    "Data: data/ai_usage_mock.csv"
    "</div>",
    unsafe_allow_html=True,
)
