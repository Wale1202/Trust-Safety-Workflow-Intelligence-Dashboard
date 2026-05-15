# Design Decisions

This is a short record of the main decisions I made on this project and the
reasoning behind each one. I wanted a single place where the "why" behind the
big calls is written down — partly so I can defend them in an interview, and
partly because I think writing decisions down is a good habit. `DESIGN.md`
covers the full product thinking; this file is the focused decision log.

---

### Why focus on Trust & Safety workflow operations?

I wanted a domain where the *operations* problem is genuinely interesting, not
just a CRUD app with a different label on it. Trust & Safety fits that well:
there's a real queue, real prioritisation pressure, sensitive cases that can't
be allowed to slip, and decisions that have to be defensible afterwards. It
forces you to think about consistency, auditability, and human-in-the-loop
design rather than just "list and edit records."

It's also a domain where I could show product judgement without needing deep
specialist knowledge: the hard part isn't the policy itself, it's the
workflow around it — how work gets triaged, escalated, measured, and
explained. That's the part an early-career technical product / ops person
would actually own, so it felt like an honest thing to build.

### Why synthetic data?

Two reasons, and the order matters.

First, **responsibility.** Real moderation data means real harmful content and
real people. Using it for a portfolio project would be unjustifiable and
unsafe, so it was never an option. Every description in the dataset is
deliberately mild and non-graphic, and sensitive categories are referenced
only at a policy/workflow level.

Second, **control.** Synthetic data let me generate a reproducible, balanced
dataset (fixed random seed) so the demo behaves consistently and the
screenshots don't change every run. The trade-off is realism — real queues are
far messier and more skewed than mine — and I've called that out as an
assumption rather than pretending the data is representative.

### Why is the risk scoring rule-based and explainable?

This was the most important decision in the project, so I want to be clear
about it. A model trained on labelled outcomes could plausibly be more
accurate. I chose an explicit additive rule model anyway, because in a Trust &
Safety context **being able to explain and defend a decision matters more than
a few points of accuracy.**

Moderation decisions get appealed and audited. A Policy Lead needs to be able
to read every rule, challenge a specific weight, and reconstruct exactly why a
given ticket was scored the way it was. A black-box score can't do that — it
just produces a number. So the scorer returns a full reasoning trail
(every point attributed to a named signal), and the weights are plain Python
anyone can read in `src/risk_scoring.py`. This is a deliberate
accuracy-for-explainability trade, not a limitation I backed into.

### Why are AI summaries treated as assistive only?

Because the slow part of triage is re-reading each case, not making the final
call — so that's the part I wanted to speed up, and only that part. The summary
gives an analyst a structured starting point (issue, suggested next action,
escalation flag), but the human still reads the ticket and still owns the
decision. Nothing in the system takes an automated enforcement action.

I also built the AI layer to **fail safe rather than fail silent.** The
default path is a deterministic local rule-based summariser that needs no API
key, so the project is never broken by missing config and never depends on a
paid service to be evaluated. The optional LLM path falls back to the local
engine automatically if it errors. Treating AI as assistive isn't just a
disclaimer here — it's reflected in how the fallback and the human-in-the-loop
flow are actually wired.

### Why these KPIs (backlog, escalation rate, avg resolution time, high-risk)?

I picked the four metrics that together answer a manager's real question:
**"are we coping, and is anything going wrong?"**

- **Backlog** — the most direct signal of whether the team is keeping pace. If
  it's growing, nothing else matters yet.
- **Average resolution time** — paired with backlog, it tells you *why*: are
  things slow, or just numerous?
- **Escalation rate** — a leading indicator. A sudden rise can mean a policy
  gap or a coordinated event, not just more volume, and it's worth raising
  early.
- **High-risk count** — backlog treats all tickets equally; this one doesn't.
  It surfaces whether the *dangerous* work specifically is under control.

I deliberately avoided vanity metrics. Every KPI on the dashboard is one a lead
could act on, not just look at.

### Why Streamlit?

The point of this project is the reasoning — the risk model, the workflow, the
product thinking — not front-end engineering. Streamlit let me build all four
pages in pure Python so that logic stays front-and-centre and easy to review,
and the whole thing runs with one command and no build step. For rapid
prototyping of a data-driven internal tool, that's exactly the right tool.

I'm aware of the cost: Streamlit is single-process and not built for many
concurrent analysts, so a real team would outgrow it. I made the same kind of
call with SQLite over PostgreSQL — zero-setup so the project is trivially
cloneable and reviewable — and isolated all data access in `database.py`
specifically so swapping the database later is a contained change. These are
prototype-appropriate choices made with the production shape in mind, not
defaults I didn't think about.

### What I would improve for production

Honestly, quite a lot — a prototype's job is to validate the idea, not to be
the system. In rough priority order:

1. **Make scoring weights configurable and versioned**, owned by a Policy Lead
   in the UI instead of hard-coded, and record which weight version scored
   each ticket.
2. **Add an outcome feedback loop** — let reviewers mark whether a priority
   call was right, and report score-vs-outcome accuracy over time. Without
   this the system can't improve.
3. **Persist an audit trail** of every score, its reasoning, and the action
   taken, so decisions stay reviewable after the fact.
4. **Move to PostgreSQL + an API + authentication** once concurrent users
   matter; the data-access isolation already makes this contained.
5. **Evaluate the AI layer properly** — measure summary quality, add output
   safety checks, and compare the local vs LLM paths rather than assuming.
6. **Add reviewer wellbeing safeguards** (content warnings, blurring,
   rotation) before anything resembling real content is ever involved.
7. **Bias-review the scoring weights** to check no category or region is being
   systematically over- or under-prioritised.

The thing I'd want to be judged on isn't that the current version is complete —
it isn't, and I've said so — but that the decisions behind it were made
deliberately and I can explain the trade-offs.
