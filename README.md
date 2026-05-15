# 🛡️ Trust & Safety Workflow Intelligence Dashboard

A synthetic operations platform that simulates how a Trust & Safety team
triages moderation tickets, monitors workflow health, generates AI-assisted
ticket summaries, scores risk in an **explainable** way, and drafts BRD/MRD
product documentation.

> ⚠️ **Synthetic and safe by design.** There is no real user data and no
> graphic or harmful content anywhere in this project. Policy categories
> (bullying, hate speech, self-harm, child safety, animal harm, spam,
> misinformation) are referenced only at a *workflow* level — every ticket
> description is intentionally mild and non-graphic. This is a learning /
> portfolio simulation, **not** a production moderation system.

---

## 1. Project overview

This project is a multipage [Streamlit](https://streamlit.io) application that
models the day-to-day operational workflow of a Trust & Safety team:

- a filterable queue of 220 synthetic moderation tickets,
- a KPI layer (backlog, escalation rate, resolution time, high-risk volume),
- an explainable risk score for every ticket,
- an AI-assisted ticket summary (with a no-API-key fallback),
- a BRD/MRD generator that turns messy stakeholder notes into a structured
  product document,
- and an enablement guide for the people who would actually use it.

It is deliberately scoped as a *working simulation*: the goal is to show
product and operations thinking backed by clean, tested code — not to ship a
production moderation system.

## 2. Why I built it

I wanted a portfolio project that demonstrates more than UI assembly. Trust &
Safety operations is a domain where the interesting problems are *operational*
— consistency, prioritisation under pressure, auditability, and keeping a human
in the loop — which is exactly the kind of work an early-career technical
product / operations person would own.

It let me practise the full loop: defining the problem, identifying users,
designing explainable logic, integrating AI responsibly, writing tests, and
documenting the reasoning. The detailed decision log is in
[DESIGN.md](DESIGN.md) and [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md).

## 3. Problem it solves

Moderation triage in many teams is **manual, inconsistent, and hard to
audit**. Two analysts can prioritise the same ticket differently, genuinely
sensitive cases can sit behind low-risk noise, leads have limited visibility
into backlog and escalation health, and the reasoning behind a priority call is
rarely written down.

This project explores one question: **how do you make triage faster and more
consistent without removing the human, and without turning prioritisation into
an unexplainable black box?**

## 4. Target users

| Persona | The question they need answered | Where the app helps |
|---|---|---|
| **Trust & Safety Operations Analyst** *(primary)* | "Which ticket is most urgent, and what's the next step?" | Risk-sorted Ticket Dashboard + AI Ticket Review |
| **Policy Lead** | "Why was this scored this way, and is it consistent with policy?" | Explainable risk score with a full reasoning trail |
| **Product Operations Manager** | "Are we keeping pace? Where is the backlog building?" | KPI section + BRD/MRD generator |

## 5. Key features

- **Ticket Dashboard** — filter the queue by status, category, priority, team,
  content type, and region; the table is sorted by risk so the most urgent
  work is at the top. KPI cards and charts (by category, status, priority,
  region, and resolution time) sit above it.
- **AI Ticket Review** — pick a ticket and get a structured summary (short
  summary, likely issue, suggested next action, escalation recommendation)
  plus the explainable risk score and its full reasoning trail.
- **BRD/MRD Generator** — paste unstructured stakeholder notes and get a
  structured 9-section product document with a downloadable Markdown export.
- **Platform Guide** — a plain-language enablement page covering how to review
  tickets, interpret scores, use AI summaries, the escalation process, and
  responsible-AI limitations.

## 6. Tech stack

| Layer | Choice | Why |
|---|---|---|
| Language | **Python 3** | Standard for data + ops tooling |
| UI | **Streamlit** | Build a data app in pure Python; fast to prototype |
| Storage | **SQLite** | Zero-setup local store; one-command run |
| Data | **Pandas** | Filtering and aggregation |
| Charts | **Plotly** | Interactive dashboard charts |
| Config | **python-dotenv** | Environment variables |
| AI (optional) | **OpenAI SDK** | Optional LLM path; rule-based fallback works with no key |
| Tests | **pytest** | Verifies the core logic |

## 7. Architecture overview

The project separates **data access**, **business logic**, and **UI** so each
part can be read, tested, and explained on its own.

```
                ┌────────────────────────────┐
                │  Streamlit UI (app.py +     │
                │  pages/) — display only     │
                └──────────────┬──────────────┘
                               │ calls
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
┌───────▼────────┐   ┌─────────▼─────────┐   ┌────────▼────────┐
│ risk_scoring   │   │ kpi_calculations  │   │ ai_summary /    │
│ (5 explainable │   │ (metrics + chart  │   │ brd_generator   │
│  rules)        │   │  aggregations)    │   │ (rule + opt LLM)│
└───────┬────────┘   └─────────┬─────────┘   └────────┬────────┘
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │ reads
                  ┌────────────▼────────────┐
                  │ database.py  →  SQLite   │
                  │ (seeded from CSV)        │
                  └────────────▲─────────────┘
                               │ generated by
                  ┌────────────┴─────────────┐
                  │ data/generate_data.py    │
                  │ (synthetic, reproducible)│
                  └──────────────────────────┘
```

Key principle: **the UI never contains business logic, and the LLM never makes
a decision** — it only improves wording. Everything decision-relevant is
rule-based and testable.

```
├── app.py                       # Home page + live snapshot
├── data/
│   ├── generate_data.py         # Synthetic data generator (reproducible)
│   └── sample_tickets.csv       # 220 fake tickets with realistic patterns
├── src/
│   ├── database.py              # SQLite layer (seed + load)
│   ├── risk_scoring.py          # 5 explainable scoring rules
│   ├── ai_summary.py            # Summary (rule-based + optional LLM)
│   ├── brd_generator.py         # Notes → structured BRD/MRD
│   └── kpi_calculations.py      # KPI maths & aggregations
├── pages/
│   ├── 1_Ticket_Dashboard.py
│   ├── 2_AI_Ticket_Review.py
│   ├── 3_BRD_MRD_Generator.py
│   └── 4_Platform_Guide.py
├── tests/                       # pytest suite (25 tests)
├── requirements.txt
├── README.md · DESIGN.md · DESIGN_DECISIONS.md
└── .env.example · .gitignore
```

## 8. Data model

Tickets are stored in a single SQLite table, seeded on first run from the
synthetic CSV. One row = one moderation ticket.

| Column | Type | Description |
|---|---|---|
| `ticket_id` | TEXT (PK) | Unique ID, e.g. `TS-1042` |
| `content_type` | TEXT | Text Post, Comment, Image, Video, Direct Message, Live Stream |
| `category` | TEXT | Policy area (7 categories) |
| `priority` | TEXT | Low / Medium / High |
| `status` | TEXT | Open / In Review / Escalated / Resolved |
| `assigned_team` | TEXT | Tier 1, Tier 2, Policy Review, Safety Escalations, Legal & Compliance |
| `created_date` | TEXT | When the ticket was raised |
| `resolved_date` | TEXT | When it was closed (blank if open) |
| `resolution_time_hours` | REAL | Hours to resolve (blank if open) |
| `region` | TEXT | One of 6 regions |
| `short_description` | TEXT | Mild, non-graphic placeholder text |

`age_days` is **computed at load time** (now − `created_date`) rather than
stored, so ticket age is always current. The synthetic data is deliberately
shaped to produce realistic patterns — sensitive categories escalate more,
under-staffed regions carry more open tickets, rich media resolves slower, and
old unresolved tickets build an aging backlog.

## 9. Risk scoring explanation

The risk score is intentionally **not** a machine-learning model. In Trust &
Safety you must be able to explain *why* a ticket was prioritised. So the score
is a transparent sum of five rules, each returning its points **and** a
plain-English reason (the audit trail).

| Rule | What it looks at | Rationale |
|---|---|---|
| Category sensitivity | Policy category | Child Safety / Self-Harm cost the most if missed |
| Content reach | Content type | A live stream spreads faster than a DM |
| Ticket age | Days open (unresolved only) | Aging unresolved tickets are riskier |
| Status | Workflow state | Escalated adds points; Resolved subtracts |
| Escalation signal | Sensitive **and** unresolved | Implies it needs a specialist |

The total is clamped to **0–100** and banded: **High ≥ 60**, **Medium ≥ 30**,
otherwise **Low**. Every rule lives in its own small function in
[`src/risk_scoring.py`](src/risk_scoring.py) so any weight can be challenged or
re-tuned in isolation. This is a deliberate accuracy-for-explainability
trade-off — auditability matters more than marginal accuracy here.

## 10. Responsible AI considerations

- **AI is assistive, not authoritative.** Summaries and scores are decision
  *support*. A human reviewer always makes and owns the final call — nothing in
  the system auto-actions.
- **The LLM never makes the decision.** When an API key is configured, the LLM
  only rewrites the prose summary; the next action and escalation
  recommendation stay rule-based and explainable.
- **Fail safe, not silent.** If the optional LLM call fails, the app falls back
  to the deterministic local engine. The default state needs no external AI.
- **No handling harm to build a demo.** All data is synthetic and non-graphic;
  sensitive categories are modelled only at the workflow level.
- **Honest about gaps.** A responsible production version would still need
  reviewer wellbeing safeguards, bias review of the scoring weights, access
  controls, and a persistent audit log. These are documented, not implied to
  exist. Full reasoning is in [DESIGN.md § 8](DESIGN.md#8-responsible-ai).

## 11. How to run locally

```bash
# 1. (Recommended) create a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) enable the LLM path
cp .env.example .env               # add OPENAI_API_KEY if you have one

# 4. Run the app
streamlit run app.py
```

Open the URL Streamlit prints (default `http://localhost:8501`). The SQLite
database is created and seeded automatically on first run. To regenerate the
synthetic dataset:

```bash
python data/generate_data.py       # rewrites data/sample_tickets.csv
# then delete data/tickets.db so it reseeds from the new CSV
```

## 12. How to run tests

The core logic (risk scoring, KPIs, BRD/MRD structure, AI fallback) is covered
by a focused `pytest` suite in [`tests/`](tests/). The tests target
*behaviour worth defending* — score range and ordering, one reason per rule
(explainability), KPI definitions, the BRD section contract, and that the AI
summary works with **no API key**.

```bash
pip install -r requirements.txt    # includes pytest
pytest                             # from the project root
```

Expected: **`25 passed`**. The suite uses small hand-built fixtures, so it
does not touch the database, the network, or any API.

## 13. Limitations (what this is *not*)

I want to be honest about scope. This is a **prototype and a portfolio
simulation**, not a production-ready enterprise platform. Specifically:

- **Synthetic data only.** All 220 tickets are generated and deliberately
  mild/non-graphic. There is no real intake, no real users, and the data is
  more balanced than a real queue would be.
- **Rule-based scoring, not trained ML.** The risk score is a hand-set additive
  rule model. The weights are reasonable and explainable, but they are *not*
  validated against real outcomes and there is no learned component.
- **No real moderation workflow integration.** It does not connect to any
  platform, content system, or ticketing tool. Nothing it outputs takes an
  action — there is no enforcement path.
- **No authentication or role-based access control yet.** Anyone who can open
  the app sees everything. The personas (Analyst, Policy Lead, Ops Manager)
  are a design lens, not enforced roles.
- **AI summaries require human review.** The summaries are decision *support*
  and can be wrong or incomplete. A human reviewer is always accountable; the
  optional LLM only rewrites prose, never the recommendation.
- **SQLite is for prototype use, not scale.** It's a single-file, largely
  single-writer store chosen for zero-setup. It is not suitable for many
  concurrent users or production load.
- **No audit log, alerting, or SLA tracking.** Scores and actions are not
  persisted for later review, and there is no monitoring layer.
- **Not security- or bias-reviewed.** The scoring weights have not been audited
  for bias, and the app has had no security review.

These aren't apologies — they're deliberate boundaries for a project whose
point is the *reasoning and design*, not production hardening. The roadmap
below is how I'd close them.

## 14. Future improvements

Each item below maps directly to a limitation above. Roughly in the order I'd
tackle them:

1. **PostgreSQL migration** — move off SQLite for concurrent access and real
   load. Data access is already isolated in one module to keep this contained.
2. **Role-based access control** — real authentication and per-role views
   (Analyst vs Policy Lead vs Ops Manager) so the personas become enforced
   permissions, not just a design lens.
3. **Audit logs** — persist every score, its full reasoning, and the action
   taken, so decisions are reviewable and defensible after the fact.
4. **API integration** — a proper service layer so it could connect to a real
   ticketing/content system instead of a seeded CSV.
5. **Human feedback loop** — let reviewers mark whether a priority call was
   right, and feed that back into reporting (and eventually weight tuning).
6. **Model evaluation** — measure AI summary quality and add output safety
   checks; make the rule-vs-LLM comparison measurable rather than assumed.
7. **Dashboard alerts** — proactive flags when, e.g., the escalation rate
   spikes or the backlog crosses a threshold, instead of relying on someone
   watching the charts.
8. **Workflow SLA tracking** — define per-priority/per-category SLAs and track
   breaches, so "are we keeping pace?" has a hard answer.
9. **Configurable, versioned scoring weights** owned by a Policy Lead in the
   UI, plus a **bias review** so no category or region is systematically
   over- or under-prioritised.
10. **Reviewer wellbeing safeguards** before anything resembling real content
    is ever involved.
