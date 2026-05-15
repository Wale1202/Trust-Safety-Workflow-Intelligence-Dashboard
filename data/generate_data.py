"""
Synthetic ticket data generator for the Trust & Safety Workflow Intelligence
Dashboard.

This produces a reproducible, completely FAKE dataset. No real user data and
no graphic / harmful content -- every description is intentionally mild and
non-graphic.

The data is NOT uniformly random. It is shaped to create the kinds of patterns
a real Trust & Safety operations dashboard would surface, so the charts tell a
story you can actually talk through:

  * Sensitive categories (Child Safety, Self-Harm, Hate Speech) escalate far
    more often than Spam.
  * There is a deliberate tail of old, still-open tickets, so the backlog
    skews old (aging backlog is a real ops problem).
  * Some regions (APAC, MENA) are modelled as under-staffed, so they carry a
    higher share of open tickets.
  * Rich content (Live Stream, Video) takes much longer to resolve than a
    Comment or Text Post, because it takes longer to review.

Every one of those patterns is set explicitly below and commented, so it can
be explained rather than hand-waved.

Run from the project root with:

    python data/generate_data.py

It writes/overwrites ``data/sample_tickets.csv``.
"""

from __future__ import annotations

import csv
import os
import random
from datetime import datetime, timedelta

# Fixed seed -> the dataset is stable, so demos and screenshots don't change.
random.seed(42)

# Everything is dated relative to "now" so the age distribution stays
# meaningful whenever the data is regenerated.
NOW = datetime.now()

NUM_TICKETS = 220

CONTENT_TYPES = ["Text Post", "Comment", "Image", "Video", "Direct Message", "Live Stream"]
CATEGORIES = [
    "Bullying / Harassment",
    "Hate Speech",
    "Self-Harm",
    "Child Safety",
    "Animal Harm",
    "Spam",
    "Misinformation",
]
PRIORITIES = ["Low", "Medium", "High"]
REGIONS = ["North America", "Europe", "LATAM", "APAC", "MENA", "Africa"]

# --- Pattern controls ----------------------------------------------------- #

# How often a ticket in each category gets escalated. Sensitive categories
# escalate far more than spam -- this drives the "escalation rate by category"
# chart.
ESCALATION_RATE = {
    "Child Safety": 0.55,
    "Self-Harm": 0.45,
    "Hate Speech": 0.32,
    "Bullying / Harassment": 0.18,
    "Misinformation": 0.12,
    "Animal Harm": 0.22,
    "Spam": 0.03,
}

# Volume mix. Spam is common; child safety is rare but high-impact.
CATEGORY_WEIGHTS = [22, 14, 7, 5, 10, 28, 14]

# Region volume + how well-staffed each region is. A lower "resolve_rate"
# means more tickets stay open there -> APAC and MENA carry more backlog.
REGION_PROFILE = {
    "North America": {"weight": 26, "resolve_rate": 0.72},
    "Europe":        {"weight": 24, "resolve_rate": 0.70},
    "LATAM":         {"weight": 14, "resolve_rate": 0.55},
    "APAC":          {"weight": 18, "resolve_rate": 0.40},  # under-staffed
    "MENA":          {"weight": 10, "resolve_rate": 0.38},  # under-staffed
    "Africa":        {"weight":  8, "resolve_rate": 0.50},
}

# How much longer each content type takes to resolve (multiplier on base
# hours). Rich media is slow to review; short text is fast.
CONTENT_RESOLUTION_FACTOR = {
    "Live Stream": 2.4,
    "Video": 1.9,
    "Image": 1.2,
    "Text Post": 1.0,
    "Comment": 0.7,
    "Direct Message": 0.9,
}
CONTENT_WEIGHTS = [22, 26, 16, 14, 14, 8]

# Specialist routing: sensitive categories go to specialist queues.
SENSITIVE = {"Child Safety", "Self-Harm", "Hate Speech"}
GENERAL_TEAMS = ["Tier 1 Moderation", "Tier 2 Specialist", "Policy Review"]

# Mild, safe, non-graphic placeholder descriptions per category.
DESCRIPTIONS = {
    "Bullying / Harassment": [
        "User reports repeated unwanted negative comments from another account.",
        "Reported comment contains mocking language directed at a user.",
        "Account flagged for sending repetitive teasing messages.",
        "User says a group is targeting them with mean replies.",
        "Reporter asks for help with persistent unkind direct messages.",
    ],
    "Hate Speech": [
        "Post flagged by automated filter for potentially exclusionary language.",
        "User reports a comment that may target a protected group.",
        "Content flagged for review under hate speech policy keywords.",
        "Reported phrase appears to demean a community; needs policy check.",
        "Comment flagged for a borderline term; needs context review.",
    ],
    "Self-Harm": [
        "User expresses sadness and may need supportive resources.",
        "Post flagged for language suggesting the user is struggling emotionally.",
        "Comment indicates the user is going through a hard time.",
        "Automated system flagged a post for a wellbeing check-in.",
        "Reporter is worried about a friend's recent low mood posts.",
    ],
    "Child Safety": [
        "Account flagged for an unverified age on the profile.",
        "Reported profile may belong to a minor; needs age verification.",
        "Content flagged for a routine minor-safety policy review.",
        "User reports a suspicious friend request pattern toward younger users.",
        "Profile flagged for an age-appropriateness review.",
    ],
    "Animal Harm": [
        "Reported video may show unsafe handling of a pet; needs review.",
        "User flags an image as potentially distressing animal content.",
        "Post flagged for a policy check on animal welfare guidelines.",
        "Comment jokes about mistreating a pet; needs context review.",
        "Reporter asks whether a pet-care clip breaks animal guidelines.",
    ],
    "Spam": [
        "Account posting the same promotional link many times.",
        "User reports repetitive advertising messages in their inbox.",
        "Automated filter flagged bulk identical comments.",
        "Profile flagged for suspected bot-like posting behaviour.",
        "Account mass-tagging users in unrelated promotional posts.",
    ],
    "Misinformation": [
        "Post shares an unverified claim about a public event.",
        "Reported content links to a low-credibility source.",
        "User flags a post for spreading a misleading statistic.",
        "Content flagged for a fact-check review queue.",
        "Reporter questions an out-of-context quote in a viral post.",
    ],
}


def _weighted(profile_key: str) -> str:
    """Pick a region using its configured volume weight."""
    regions = list(REGION_PROFILE.keys())
    weights = [REGION_PROFILE[r][profile_key] for r in regions]
    return random.choices(regions, weights=weights, k=1)[0]


def _pick_age_days() -> float:
    """Ticket age distribution.

    Deliberately fat-tailed: most tickets are recent, but ~22% are old. The
    old, still-open ones are what build a realistic aging backlog.
    """
    bucket = random.random()
    if bucket < 0.48:
        return round(random.uniform(0, 21), 1)      # recent
    if bucket < 0.78:
        return round(random.uniform(21, 75), 1)     # mid-age
    return round(random.uniform(75, 180), 1)        # old tail


def _priority(category: str, escalated: bool) -> str:
    """Sensitive or escalated tickets skew high priority."""
    if category in SENSITIVE or escalated:
        return random.choices(PRIORITIES, weights=[10, 30, 60], k=1)[0]
    if category in ("Bullying / Harassment", "Misinformation", "Animal Harm"):
        return random.choices(PRIORITIES, weights=[35, 45, 20], k=1)[0]
    return random.choices(PRIORITIES, weights=[60, 32, 8], k=1)[0]  # spam etc.


def _resolution_hours(priority: str, category: str, content_type: str) -> float:
    """Hours to resolve = base(priority) x content factor x urgency, + jitter.

    Sensitive categories are handled with urgency (faster). Rich media is
    slower to review (content factor)."""
    base = {"Low": 70, "Medium": 28, "High": 9}[priority]
    urgency = 0.4 if category in ("Child Safety", "Self-Harm") else 1.0
    factor = CONTENT_RESOLUTION_FACTOR[content_type]
    jitter = random.uniform(0.6, 1.6)
    return round(base * urgency * factor * jitter, 1)


def _assign_team(category: str, escalated: bool) -> str:
    if escalated:
        # Legal handles a slice of escalations; the rest go to Safety Escalations.
        return "Legal & Compliance" if random.random() < 0.25 else "Safety Escalations"
    if category in SENSITIVE:
        return "Tier 2 Specialist"
    return random.choice(GENERAL_TEAMS)


def _status(escalated: bool, resolved: bool, age_days: float) -> str:
    """Resolve, escalate, or leave open. Older unresolved tickets are more
    likely to still be 'Open' -- that is the aging backlog."""
    if resolved:
        return "Resolved"
    if escalated:
        return "Escalated"
    # Unresolved & not escalated: older ones tilt toward Open over In Review.
    if age_days > 45:
        return random.choices(["Open", "In Review"], weights=[75, 25], k=1)[0]
    return random.choices(["Open", "In Review"], weights=[45, 55], k=1)[0]


def generate_rows(n: int = NUM_TICKETS) -> list[dict]:
    rows = []
    for i in range(1, n + 1):
        category = random.choices(CATEGORIES, weights=CATEGORY_WEIGHTS, k=1)[0]
        content_type = random.choices(CONTENT_TYPES, weights=CONTENT_WEIGHTS, k=1)[0]
        region = _weighted("weight")
        age_days = _pick_age_days()
        created = NOW - timedelta(days=age_days)

        escalated = random.random() < ESCALATION_RATE[category]
        priority = _priority(category, escalated)
        res_hours = _resolution_hours(priority, category, content_type)

        # A ticket resolves only if its work window has closed AND it actually
        # got handled. The handling chance drops sharply with age: an old
        # ticket that still hasn't been resolved tends to stay stuck in the
        # queue. That "old + stuck" mass is what creates the aging backlog.
        resolved_date = created + timedelta(hours=res_hours)
        time_elapsed = resolved_date <= NOW
        age_penalty = 1.0 if age_days <= 21 else (0.7 if age_days <= 75 else 0.3)
        handled = random.random() < REGION_PROFILE[region]["resolve_rate"] * age_penalty
        is_resolved = time_elapsed and handled and not escalated

        status = _status(escalated, is_resolved, age_days)

        if status == "Resolved":
            resolved_str = resolved_date.strftime("%Y-%m-%d %H:%M")
            res_hours_out: float | str = res_hours
        else:
            resolved_str = ""
            res_hours_out = ""

        rows.append(
            {
                "ticket_id": f"TS-{1000 + i}",
                "content_type": content_type,
                "category": category,
                "priority": priority,
                "status": status,
                "assigned_team": _assign_team(category, escalated),
                "created_date": created.strftime("%Y-%m-%d %H:%M"),
                "resolved_date": resolved_str,
                "resolution_time_hours": res_hours_out,
                "region": region,
                "short_description": random.choice(DESCRIPTIONS[category]),
            }
        )
    return rows


def main() -> None:
    out_path = os.path.join(os.path.dirname(__file__), "sample_tickets.csv")
    rows = generate_rows()
    fieldnames = list(rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} synthetic tickets to {out_path}")


if __name__ == "__main__":
    main()
