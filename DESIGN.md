# Design & Product Thinking

This document explains *why* the project is built the way it is. The README
covers what it does and how to run it — this one is about the reasoning. I
wrote it the way I'd want to be able to talk through the project in an
interview: honest about the scope, the assumptions, and the things I chose
**not** to do.

---

## 1. Problem statement

Trust & Safety teams deal with a constant stream of moderation tickets across
many policy areas. In a lot of teams the day-to-day reality is:

- Triage is **manual and inconsistent** — two analysts can prioritise the same
  ticket differently, and there's no shared definition of "urgent".
- Prioritisation is **gut-feel**, so genuinely sensitive cases (e.g. child
  safety, self-harm) can sit behind low-risk noise like spam.
- Leads have **limited visibility** into workflow health — backlog size,
  escalation rate, and how long things actually take to resolve.
- Decisions are **hard to audit** after the fact, because the reasoning behind
  a priority call usually isn't written down anywhere.

The core problem this project explores is: **how do you make moderation triage
faster and more consistent without removing the human, and without turning the
prioritisation into an unexplainable black box?**

This is a simulation built on synthetic data, so it doesn't solve that problem
for a real team. It's a working model of an approach to it.

---

## 2. User personas

I designed the three pages around three real roles a tool like this would
serve. Each persona has a different question they're trying to answer.

### Trust & Safety Operations Analyst (primary user)
- **Does:** Works the moderation queue ticket by ticket, all day.
- **Needs:** To know *what to pick up next* and *why*, without re-reading a
  whole case to make a triage call.
- **Question they ask:** "Which ticket is most urgent right now, and what's the
  recommended next step?"
- **Serves them:** Ticket Dashboard (risk-sorted queue, filters) and AI Ticket
  Review (summary + risk reasoning).

### Policy Lead
- **Does:** Owns the policy definitions and escalation rules; signs off on how
  sensitive cases are handled.
- **Needs:** To trust and tune the prioritisation logic, and to defend any
  decision in an audit or appeal.
- **Question they ask:** "Why was this ticket scored this way, and is that
  consistent with our policy?"
- **Serves them:** The explainable risk score with a full reasoning trail, and
  the responsible-AI / escalation notes in the Platform Guide.

### Product Operations Manager
- **Does:** Runs the operational side — staffing, SLAs, reporting upward.
- **Needs:** A read on workflow health and where the bottlenecks are.
- **Question they ask:** "Are we keeping pace? Where is the backlog building
  up, and is the escalation rate normal?"
- **Serves them:** The KPI section and the BRD/MRD generator (turning oper
  pain points into a structured improvement spec).

---

## 3. Why each feature exists

Each feature maps back to a persona's question — none of them are there just to
have more pages.

| Feature | Why it exists |
|---|---|
| **Ticket Dashboard + filters** | An analyst can't work a flat, unsorted list. Sorting by risk and filtering to *their* queue is the difference between "where do I start" and "I know what's next." |
| **KPI section** | A manager can't manage what they can't see. Backlog, escalation rate, and average resolution time together answer "are we coping?" in one glance. |
| **Explainable risk score** | This is the heart of the project. A score on its own is just another opaque number. The *reasoning trail* is what lets a Policy Lead trust it, tune it, and defend a decision. I deliberately chose a transparent rule model over a more accurate black box for this reason. |
| **AI ticket summary** | Re-reading every ticket from scratch is the slow part of triage. A structured summary (issue / next action / escalation) speeds the analyst up — it doesn't decide for them. |
| **BRD/MRD generator** | Ops improvements usually start as messy notes in a doc and die there. Structuring them into a real spec is a product-thinking step, and it shows I can do more than build UI. |
| **Platform Guide** | A tool nobody knows how to use correctly is a liability in a safety context. Enablement docs (including the escalation process and limits) are part of the deliverable, not an afterthought. |

---

## 4. Assumptions

I'm being explicit about these because they're the things that would have to be
re-validated before this approach was anywhere near a real team:

- **Incoming tickets are reasonably well-structured** — category, status,
  content type, and timestamps are present and trustworthy. Real moderation
  intake is much messier than my synthetic data.
- **Category sensitivity is roughly stable** — the scoring weights assume, for
  example, that child safety always outranks spam. A real deployment would
  need a Policy Lead to own and version these weights.
- **The reviewer is the decision-maker** — the system assumes a human always
  acts on the output. None of the logic auto-actions anything.
- **Resolution time is a usable proxy for effort/health** — fine for a demo;
  in reality it's affected by shift patterns, ticket complexity, and reopen
  rates, which I don't model.
- **English-language, single-tenant context** — no localisation or
  multi-team routing logic.
- **Synthetic data is representative enough to demonstrate the workflow** —
  it's deliberately mild and balanced, which real queues are not.

---

## 5. Trade-offs

These are choices I made knowingly, with the alternative in mind.

**Streamlit instead of React + a separate API.**
A React front end with a Python/FastAPI back end would be the "production"
shape and would scale to many concurrent users. I chose Streamlit because the
point of this project is the *reasoning* — the risk model, the workflow, the
product thinking — not front-end engineering. Streamlit let me build all four
pages in pure Python so the logic stays front-and-centre and reviewable. The
cost is that it's single-process and not built for many concurrent analysts;
I'd outgrow it quickly in a real team.

**SQLite instead of PostgreSQL.**
Postgres is what you'd actually run this on — concurrent writes, real users,
backups. I used SQLite because it's zero-setup: the project runs with one
command and no database server, which matters for something meant to be cloned
and reviewed. I isolated all data access in `database.py` specifically so
swapping to Postgres later is a contained change, not a rewrite.

**Rule-based scoring instead of a trained model.**
A model trained on labelled outcomes could be more accurate. I chose an
explicit additive rule model because in Trust & Safety, *being able to explain
and defend a decision* is worth more than a few points of accuracy. A Policy
Lead can read every rule, challenge a weight, and audit any score. That's a
deliberate accuracy-for-explainability trade.

**Local rule-based AI fallback as the default, LLM optional.**
The summary feature works with no API key at all. I did this so the project is
never broken by missing config and so it doesn't depend on a paid service to
be evaluated. The trade-off is that the default summaries are templated and
less fluent than an LLM's — but they're deterministic and free, and the LLM
path is there when wanted.

**Synthetic, mild data instead of realistic content.**
Realistic moderation data would make the demo more convincing, but it would be
irresponsible and unsafe. I kept all descriptions deliberately non-graphic.
The trade-off is realism; the reason is that handling harmful content for a
portfolio project is not justifiable.

---

## 6. Limitations of the current version

Things I'd flag honestly rather than hide:

- **It's a simulation.** Synthetic data, no real intake pipeline, no auth, no
  audit log persistence. Not production-ready and not meant to be.
- **Scoring weights are hand-set by me**, not validated against outcomes. They
  are reasonable, not proven.
- **No feedback loop** — the system never learns whether a priority call was
  actually correct, so it can't improve.
- **Single user, single process** — Streamlit + SQLite won't support a real
  team working concurrently.
- **No reviewer wellbeing features** — a real moderation tool needs content
  warnings, blurring, and rotation safeguards. Out of scope here precisely
  because the data is non-graphic.
- **The LLM path is lightly integrated** — one provider, simple prompt, no
  evaluation of the LLM's output quality or safety.
- **Local AI summaries are templated** and will read repetitively across
  similar tickets.

---

## 7. Future improvements

Roughly in the order I'd actually do them:

1. **Make scoring weights configurable and versioned**, owned by a Policy Lead
   in the UI rather than hard-coded — and log which weight version scored each
   ticket.
2. **Add an outcome feedback loop** — let reviewers mark whether the priority
   was right, and report on score-vs-outcome accuracy over time.
3. **Persist an audit trail** — store every score, its reasons, and the action
   taken, so decisions are reviewable after the fact.
4. **Move to Postgres + an API + auth** when concurrent users matter; the
   data-access isolation is already there to make this contained.
5. **Evaluate the AI layer properly** — measure summary quality, add output
   safety checks, and compare the local vs LLM path.
6. **Reviewer wellbeing safeguards** before anything resembling real content.
7. **Bias review of the scoring weights** — check that no category or region
   is being systematically over- or under-prioritised.

---

## 8. Responsible AI

A few principles this project is built around, and the reasoning behind them:

- **AI here is assistive, not authoritative.** The summary and the risk score
  are decision *support*. A human reviewer always makes and owns the call.
  Nothing in the system takes an automated enforcement action.
- **Explainability is a feature, not a nice-to-have.** Moderation decisions
  affect people and get appealed. If you can't explain *why* a ticket was
  prioritised, you can't defend it — so the risk model is intentionally
  transparent and fully traceable rather than a black box.
- **Fail safe, not silent.** If the optional LLM call fails, the system falls
  back to the deterministic local engine rather than breaking or guessing. The
  default state requires no external AI at all.
- **Don't handle harm to build a demo.** All data is synthetic and
  non-graphic. Sensitive categories are modelled at the *workflow* level only.
- **Know what's missing.** A responsible real version would also need reviewer
  wellbeing protections, bias auditing of the weights, access controls, and a
  persistent audit log. I've listed these openly rather than implying the
  current version is complete.

The short version I'd say out loud: *the AI speeds the analyst up and makes the
reasoning visible; it never replaces the human, and it's honest about what it
can't do.*
