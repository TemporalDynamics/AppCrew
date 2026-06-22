# AppCrew / Vertical: Recruit

Executive talent sourcing crew — a domain-specific extension of AppCrew for recruiting firms.

**All data in this directory is fictional.** Real client data, real candidate profiles, and real company strategies live in private repos (e.g., `.crew/` inside the private repo of each client engagement), never here.

---

## What this vertical adds

The Recruit vertical extends AppCrew with:

- **Criterion Intake** — structured capture of the human recruiter's criteria before any search
- **Golden Calibration Set** — 4 reference profiles to measure if the system thinks like the recruiter
- **Talent Mission Capsule** — a full mission brief wrapping a recruiting run
- **Human Approval Gate** — no candidate is contacted without explicit human approval

---

## Core concepts

### Criterion Intake

Before the crew searches, it captures:
- Target role(s) and markets
- Positive signals (what makes a strong candidate)
- Negative signals (automatic disqualifiers)
- Preferred background context
- Outreach tone

This produces a `criteria.yaml` file that all agents use.

### Golden Calibration Set

4 reference profiles provided by the human recruiter:

| Type | What it is |
|------|-----------|
| `obvious_yes` | The recruiter would approve immediately |
| `hidden_gem` | Strong but not obvious — requires reading between lines |
| `risky_maybe` | Looks good but has a flag that must be validated |
| `false_positive` | Impressive on paper but the recruiter knows to reject |

The crew scores these alongside its discoveries. The calibration shows whether the system's criterion understanding aligns with the recruiter's judgment.

### Talent Mission Capsule

```
mission_brief
  ↓
criterion intake (recruiter's criteria)
  ↓
micro-cells hydrated (one kernel, different market/industry context)
  ↓
candidates scored + golden calibration
  ↓
shortlist (top N, human-reviewable)
  ↓
human decision (approve / reject / ask for more evidence)
  ↓
outreach drafts (never sent without approval)
  ↓
MCP ledger (tamper-detectable record)
```

---

## Agents (fictional demo)

- **Talent Cell Commander** — orchestrates the mission, writes the brief
- **Demand Radar** — scans market signals (role openings, company movements)
- **Talent Sourcing** — finds candidate profiles matching criteria
- **Career Context** — reads career trajectory, not just title
- **Talent Signal** — detects mobility signals (advisory roles, founder exits)
- **Fit Scoring** — scores candidates against criteria
- **Outreach** — drafts first contact (never sends without approval)
- **Auditor** — verifies scoring reasoning, flags hallucinated signals

---

## Hydration (micro-cell pattern)

All sourcing agents share one `BaseAgent` kernel. What differentiates them is the context injected at instantiation:

```python
cell_fintech_mx = TalentScout(config={
    "market": "Mexico",
    "industry": "fintech",
    "role_focus": "CTO / VP Engineering",
    "signals": ["scaled_team_20_plus", "managed_pnl"],
    "token_budget": 500,
})

cell_retail_latam = TalentScout(config={
    "market": "LATAM",
    "industry": "retail",
    "role_focus": "Country Manager",
    "signals": ["opened_new_market", "managed_pnl"],
    "token_budget": 500,
})
```

Same kernel. Different context. The army grows, not the complexity.

---

## Demo (fictional)

See `demos/fake_recruit_demo/` for a complete offline demo using fictional company names and fictional candidates. No real people, no real companies, no real strategies.

Fictional brand used in demos: **Northstar Talent** / **Atlas Recruiting**

---

## What is NOT here

- Real candidate names or profiles
- Real client company strategies
- Real recruiter criteria
- Real InMail templates with real names
- Any data from Global Executive or any real client engagement
