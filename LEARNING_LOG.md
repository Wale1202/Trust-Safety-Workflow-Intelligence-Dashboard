# Learning Log

A personal, honest record of what I was actually trying to learn while
building this project, where I got stuck, and what I'd do differently. This
isn't the polished pitch (that's in `INTERVIEW.md`) — it's the messier
behind-the-scenes version, written for myself as much as anyone reading the
repo.

---

## 1. What I was trying to learn

Going in, I wasn't mainly trying to learn a framework. I wanted to practise
**thinking like a product/operations person who can also build**, not just a
coder following a spec. Concretely, I wanted to get better at:

- starting from a problem and a user instead of starting from features,
- designing logic I could actually *explain and defend*, not just code that
  works,
- integrating AI in a way that's useful but not reckless,
- and writing down my reasoning so the decisions are visible.

Streamlit, SQLite and pytest were means to an end. The real goal was the
judgement around them.

## 2. What I found challenging

A few things were genuinely harder than I expected.

The first was **resisting feature creep**. My instinct was to keep adding
pages and options. The harder discipline was stopping and asking "which
persona's question does this answer?" — and cutting things that didn't have a
good answer.

The second was **making the synthetic data tell a believable story**. My
first version was basically uniform random noise, and the dashboard charts
were flat and boring. Getting it to show realistic patterns — sensitive
categories escalating more, an aging backlog — took more thought than I
assumed. I actually got it *wrong* the first time: I made the backlog younger
than the resolved tickets, the opposite of a real aging backlog, because old
tickets were more likely to have had their resolution window pass. I only
caught it because I checked the numbers instead of trusting the code.

The third was **keeping the AI integration honest**. My first attempt had the
LLM produce part of the answer and the rule engine produce the rest, stitched
together in a way that was confusing to explain. Refactoring that into a clear
rule — "the LLM only rewrites the prose, never the recommendation" — was a
better design *and* a better story, but it took a second pass to see it.

## 3. How I approached the risk scoring logic

I started from a constraint, not from an algorithm: **whatever I build, I have
to be able to explain why any given ticket scored what it did.** That ruled
out a trained model almost immediately — not because ML is bad, but because in
this domain "the model said so" isn't an acceptable answer to an appeal.

So I went with a simple additive model: a handful of signals, each adding (or
subtracting) points, with a written reason attached to every contribution. I
deliberately split it into five small functions — one per signal — so that
each rule could be read, tested, and challenged on its own. The first version
was one long function; breaking it up made it both cleaner and far easier to
talk about ("here are the five things we score on").

The weights are hand-set and I'm honest that they're *reasonable, not
proven*. Picking them made me realise how much of real Trust & Safety
prioritisation is policy judgement, not maths — which is exactly why making
them explainable and tunable mattered more than making them "accurate".

## 4. Why I used synthetic data

Two reasons, and the order matters to me.

First, **responsibility**. Real moderation data means real harmful content and
real people. Using it for a portfolio project would be unjustifiable, so it
was never an option. Every description in the dataset is deliberately mild and
non-graphic, and the sensitive categories are referenced only at a
workflow/policy level.

Second, **control**. Synthetic data let me deliberately build the patterns I
wanted to demonstrate and keep them reproducible with a fixed seed. The
trade-off is realism — a generated dataset is cleaner and more balanced than a
real queue — and I learned it's better to state that limitation openly than to
pretend the data is representative.

## 5. What I learned about Trust & Safety workflows

The biggest shift in my thinking: in this domain, **being able to defend a
decision can matter more than being marginally more accurate**. Decisions get
appealed and audited, so traceability isn't a nice-to-have, it's part of the
core requirement.

I also came to appreciate why **escalation and prioritisation are the heart of
it**, not the content review itself. Sensitive cases can't be allowed to sit
behind low-risk noise like spam, so a sensible default ordering and a clear
escalation path are doing a lot of the real work. And I learned that workflow
health (backlog, aging, escalation rate) is its own signal — a rising
escalation rate can mean a policy gap, not just more volume.

Finally, it made the **human-in-the-loop point concrete for me**. It's easy to
say "keep a human in the loop" as a slogan; designing the system so the human
is genuinely the decision-maker — and the AI can't quietly replace the
explainable part — is a real design constraint.

## 6. What I learned about AI-assisted tools

The main lesson: **be precise about what the AI is allowed to touch.** Vague
"AI-powered" features are easy to build and hard to trust. Restricting the LLM
to rewriting the human-readable summary, while keeping the recommendation
rule-based, made the tool both more trustworthy and easier to reason about.

I also learned the value of **designing for the AI not being there**. Building
the rule-based fallback as the default — not as an afterthought — meant the
project never depends on a key or a paid service to work or be evaluated, and
it forced me to actually think through the non-AI logic properly instead of
hiding behind the model.

And I learned that **AI output needs a verification story**. Right now that
story is "a human always reviews it", which is honest but minimal — it made me
understand why real systems need evaluation and feedback loops, which is now on
the roadmap rather than something I pretended to have.

## 7. What I would do differently next time

- **Shape the data model and its patterns earlier.** I built features and then
  realised the data wasn't interesting enough to show them off. Next time I'd
  design the "story the data should tell" up front.
- **Write at least a couple of tests before refactoring, not after.** The
  tests I wrote later caught a real behaviour (the first-match-wins routing
  quirk) — if they'd existed earlier they'd have caught it sooner and shaped
  the design.
- **Decide the AI boundary on day one.** The confusing first integration
  happened because I added the LLM before I'd decided exactly what it was and
  wasn't allowed to do. That boundary should be a design decision, not
  something discovered during a refactor.
- **Keep a running decisions doc from the start.** Reconstructing my reasoning
  afterwards for `DESIGN_DECISIONS.md` was harder than it would have been to
  jot decisions down as I made them.

Overall I'm happy with the judgement the project demonstrates more than any
single feature in it — and the honest version of that is that I learned most
of these lessons by getting the first attempt slightly wrong and fixing it.
