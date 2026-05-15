# Interview Explanation

This is how I'd talk through the project out loud. It's written the way I'd
actually say it, not as marketing copy — structured so I can give the short
version or go deeper depending on how much time I have.

If I only had 30 seconds: *"I built a Trust & Safety operations dashboard on
synthetic data. It risk-scores moderation tickets with a fully explainable
rule model, gives analysts an AI-assisted summary to speed up triage, and
keeps a human accountable for every decision. The interesting part isn't the
UI — it's the design choices, like choosing an explainable score over a
black box because in this domain you have to defend decisions."*

---

## 1. Why I built it

I wanted a portfolio project that showed more than the ability to wire up a
UI. A lot of demo projects are CRUD apps with a different label on them, and
they don't really show product or operations thinking.

Trust & Safety appealed to me because the hard part isn't the technology — it's
the operational problem underneath it: a constant queue of work, real
prioritisation pressure, sensitive cases you can't afford to miss, and
decisions that get appealed and audited. That's the kind of problem an
early-career technical product or operations person actually owns, so it let
me practise the whole loop: defining the problem, identifying the users,
designing logic I can defend, integrating AI responsibly, writing tests, and
documenting why I made each call.

## 2. The problem it solves

In a lot of moderation teams, triage is manual, inconsistent, and hard to
audit. Two analysts can look at the same ticket and prioritise it differently.
Genuinely sensitive cases — child safety, self-harm — can end up sitting behind
low-risk noise like spam. Team leads don't have a clear read on backlog or
escalation health. And the reasoning behind a priority call usually isn't
written down anywhere, so it can't be reviewed later.

So the question I framed the project around was: *how do you make triage faster
and more consistent without removing the human, and without turning
prioritisation into an unexplainable black box?* I want to be clear in an
interview that this is a simulation on synthetic data — it's a working model of
an approach to that problem, not a solution I'm claiming works for a real team.

## 3. How the system works

End to end, it's four steps.

First, **data**. There's a generator that produces about 220 fully synthetic,
non-graphic tickets. It's not random — I deliberately shaped it so the
dashboard tells a story: sensitive categories escalate more, under-staffed
regions carry more open tickets, rich media takes longer to resolve, and old
unresolved tickets build an aging backlog. It seeds a local SQLite database on
first run.

Second, **scoring**. Every ticket goes through a risk model that's a sum of
five rules — category sensitivity, content reach, ticket age, status, and
whether escalation is implied. Each rule returns its points *and* a
plain-English reason, so the output is a 0-to-100 score, a Low/Medium/High
band, and a full reasoning trail.

Third, **the operational layer**. KPIs — backlog, escalation rate, average
resolution time, high-risk count — are calculated separately from the UI so
they're testable. The dashboard sorts by risk so the most urgent work is at
the top.

Fourth, **AI assistance**. You can pick a ticket and get a structured summary —
short summary, likely issue, suggested next action, escalation recommendation.
By default that's all rule-based and works with no API key. If an API key is
configured, the LLM rewrites *only* the prose summary; the next action and
escalation stay rule-based.

The one architectural idea I'd lead with: data access, scoring, KPI maths, and
UI are separated, and the AI never makes a decision — it only improves wording.

## 4. My main design decisions

There are four I'd actually talk about, because I made each one knowing the
alternative.

**Explainable rule-based scoring instead of a machine-learning model.** A
trained model might be slightly more accurate, but in Trust & Safety you have
to be able to explain and defend a decision when it's appealed or audited. A
Policy Lead can read every rule, challenge a weight, and reconstruct exactly
why a ticket scored what it did. That's a deliberate
accuracy-for-explainability trade-off, not a shortcut.

**AI as assistive, not authoritative — and enforced in code.** It would have
been easy to let the LLM produce the whole recommendation. I deliberately
restricted it to rewriting the readable summary, and kept the
decision-relevant fields rule-based, so the explainable part can't be
silently replaced.

**A local fallback as the default.** The summary works with zero config and no
API key, and the LLM path falls back automatically if it fails. I didn't want
the project to be broken by missing configuration or to depend on a paid
service just to be evaluated.

**Streamlit and SQLite over React and Postgres.** I knew the production shape
would be a proper front end, an API, and a real database. But the point of
this project is the reasoning, so I chose tools that keep the logic in pure
Python and let it run with one command. I isolated all data access in one
module specifically so moving to Postgres later would be a contained change,
not a rewrite — so it's a deliberate prototype choice, not a default I didn't
think about.

## 5. What I learned

A few things stuck with me.

The biggest one is that **explainability is a feature, not overhead.**
Splitting the score into five small functions that each return a reason made
the logic easier to test, easier to change, and far easier to talk about. The
constraint improved the design.

I also learned to **let tests change my mind.** One test failed and it turned
out the keyword router for the document generator is first-match-wins, so a
sentence matching several categories lands in the first one. Instead of
gold-plating the router, I wrote a test that pins and documents that
limitation. Knowing what *not* to over-engineer is a skill.

And on a softer level, **writing the reasoning down was as valuable as the
code.** Forcing myself to state assumptions, trade-offs, and limitations
explicitly is what made it feel like a real product decision rather than a
demo.

## 6. What I would improve next

In priority order: make the scoring weights configurable and versioned so a
Policy Lead owns them in the UI rather than them being hard-coded; add an
outcome feedback loop so reviewers can mark whether a priority call was right
and we can measure score-versus-outcome accuracy; persist an audit trail of
every score and action; and then move to Postgres with an API and
authentication once concurrent users actually matter. Beyond that, properly
evaluating the AI layer and a bias review of the scoring weights.

I'd also be honest that a real version needs reviewer wellbeing safeguards —
that's deliberately out of scope here precisely because the data is
non-graphic.

## 7. How it relates to the kind of work I want to do

**Systems / infrastructure.** The whole project is built around separation of
concerns — data access, logic, and UI are isolated, which is exactly why the
logic is testable and the database could be swapped without a rewrite. That's
the same instinct you need for maintainable infrastructure.

**Trust & Safety.** It's a direct model of T&S operations: triage,
prioritisation of sensitive categories, an escalation process, and an emphasis
on auditable decisions and a human always being accountable.

**AI workflows.** It's a concrete example of integrating AI as a co-pilot
rather than a decision-maker — with a clear boundary on what the model is
allowed to touch and a deterministic fallback when it isn't available.

**Product operations.** The personas, the KPI layer, and the BRD/MRD generator
are all about turning operational reality into something measurable and
actionable — and the documentation shows I can reason about users and
trade-offs, not just build features.

**Process optimisation.** At its core the project is about making a workflow
faster and more consistent — risk-sorting the queue, surfacing aging backlog,
and using AI to cut the slow part of triage — while keeping the process
transparent enough to trust and improve.

---

*The thread through all of it: I care about making operational work faster and
more consistent, while keeping the reasoning visible enough that a human can
trust it, audit it, and improve it.*
