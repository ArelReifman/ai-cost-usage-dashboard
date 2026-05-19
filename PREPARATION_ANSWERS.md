# Preparation Questions - AI Cost & Usage Intelligence Dashboard

## 1. Which metrics did you choose, and why?

I chose metrics that give a clear view of both cost and usage: total cost, total requests, total tokens, average cost per request, efficiency score, estimated savings, and waste risk.

The goal was to make the dashboard useful for different stakeholders. Finance can quickly understand overall spend, engineering can spot inefficient model usage, and leadership can identify where there are real opportunities to optimize costs.

## 2. Which AI feature did you build, and what problem does it solve?

I built a live AI Advisor powered by the Gemini API.

The advisor looks at the currently filtered dashboard data and generates three prioritized optimization recommendations. Each recommendation includes the finding, business impact, estimated opportunity, and recommended action.

The main idea is that a dashboard should not only show what happened, but also help the user understand what to do next.

To keep it safe and reliable, the advisor sends only aggregated data, not raw CSV rows. It also has fallback logic, so if Gemini is unavailable or no API key is configured, the dashboard still provides rule-based recommendations.

## 3. What would you do differently with another week of work?

With another week, I would focus on making the prototype closer to a production-ready product.

I would connect it to real provider billing and usage APIs, add a proper data store, user-level drill-downs, budget tracking, anomaly detection, and historical comparisons.

I would also improve the AI Advisor with response caching, follow-up questions, and period-over-period analysis.

## 4. How would you obtain real data and scale this in production?

In production, I would collect data from provider usage and billing APIs where available, such as OpenAI, Anthropic, and Google Cloud Billing exports.

For tools that do not provide detailed usage data, I would use an AI gateway such as LiteLLM, Portkey, or an internal proxy to log each request with the relevant team, user, model, token usage, cost, and purpose.

The data would be stored as raw events and then aggregated into a database or warehouse such as PostgreSQL or BigQuery. The dashboard would query pre-aggregated data, with SSO, role-based access, row-level permissions, budget alerts, and governance rules around approved model usage.
