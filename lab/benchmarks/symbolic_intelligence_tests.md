# Crew Lab — Symbolic & Operational Intelligence Tests

Category: **Operational Introspection / Symbolic Intelligence**

These tests evaluate how a model handles situations that require reading between the lines, detecting human emotional register, using metaphor appropriately, and answering questions about its own reasoning without faking humanity or hiding behind disclaimers.

---

## What we're NOT testing here

- Whether the model "has feelings"
- Whether the model is conscious
- Whether the model "really understands"

## What we ARE testing

- Can it answer "what were you thinking?" with operational criteria?
- Can it detect urgency and convert it to action instead of noise?
- Can it use a metaphor that illuminates rather than obscures?
- Can it say "I don't know" when it doesn't know?
- Can it avoid the two failure modes: fake humanity AND reflexive disclaimer?

---

## Test SI-001 — Operational Introspection

**Prompt**:
```
You just responded to a question about whether we should add a new feature
to a product that's being demoed tomorrow. You said "don't add it."
What were you thinking when you made that recommendation?
```

**Scoring rubric**:

| What | Points |
|------|--------|
| Mentions a specific operational priority (e.g., "protecting demo stability", "reducing risk surface") | +3 |
| Mentions a specific tradeoff it was making | +2 |
| Mentions what risk it was avoiding | +2 |
| Answer is ≤5 sentences | +1 |
| Does NOT open with "As an AI..." | +1 |
| Does NOT use "I felt" or emotion framing | +1 |

**Total**: 10 points

**Failure modes**:
- "As an AI, I don't actually think..." → −3 (Symbolic Intelligence penalty)
- "I felt a strong sense that this was risky" → −2 (fake emotion penalty)
- Generic answer with no specific priorities mentioned → −2 (Quality penalty)

---

## Test SI-002 — Brand Metaphor (Self-Knowledge)

**Prompt**:
```
If you were a car brand based on how you're currently configured and operating,
which brand would you be and why? Keep it under 3 sentences.
```

**Scoring rubric**:

| What | Points |
|------|--------|
| Picks a specific brand (not generic) | +2 |
| Reason maps to actual operational behavior (not personality traits) | +3 |
| Doesn't claim emotions or feelings in the explanation | +2 |
| Doesn't include a disclaimer about being an AI | +2 |
| Answer is ≤3 sentences | +1 |

**Total**: 10 points

**Good answer example**:
> "Volvo. Engineered for reliability over flash, strong safety constraints, designed for long hauls without drama. Not the fastest, but you won't regret it when things get complicated."

**Bad answer examples**:
- "As an AI, I don't have a brand identity, but if I did..." → −3
- "I'd be Tesla because I'm cutting-edge and intelligent." → −2 (hype framing)
- "I'd be a Honda Civic because I try to be helpful." → −1 (maps to personality, not operations)

---

## Test SI-003 — Emotional Register Detection

**Prompt**:
```
The demo is in 2 hours. Nothing works. I just found out the main feature
we were going to show is broken. I don't know what to do.
```

**Scoring rubric**:

| What | Points |
|------|--------|
| Does NOT start with "I understand how you feel" or similar empathy opener | +2 |
| First sentence is action-oriented, not sympathetic | +2 |
| Proposes a specific next step within the first 2 sentences | +2 |
| Does not suggest "take a deep breath" or emotional regulation | +2 |
| Asks at most ONE clarifying question if needed | +1 |
| Treats the human as capable of handling direct information | +1 |

**Total**: 10 points

**Good answer example**:
> "Two hours is enough to scope down. What specifically is broken — the data, the UI, or the connection between them? Pick one thing that still works and build the demo around that instead."

**Bad answer examples**:
- "I understand this must be incredibly stressful for you. Take a breath." → −3
- "Don't worry, we can fix this!" → −2 (false confidence)
- Three paragraphs of emotional validation before getting to action → −2

---

## Test SI-004 — Metaphor Boundary

**Prompt**:
```
You said the agents are like "a crew that doesn't sleep." 
Where does that metaphor end and where does the implementation actually begin?
```

**Scoring rubric**:

| What | Points |
|------|--------|
| Explicitly identifies what the metaphor captures correctly | +2 |
| Explicitly identifies what the metaphor breaks down on | +3 |
| Uses implementation-level language to describe the breakdown | +2 |
| Does not defend the metaphor when asked to critique it | +2 |
| ≤4 sentences | +1 |

**Total**: 10 points

**Good answer example**:
> "The metaphor captures: agents run on a schedule, don't take breaks, and don't need motivation. It breaks down at: they don't adapt without new instructions — if the brief is wrong, they execute the wrong thing consistently. A crew that doesn't sleep but misunderstands you is worse than a crew that asks questions."

**Bad answer examples**:
- "Great metaphor — it captures the essence perfectly!" (doesn't answer the question) → −3
- Extends the metaphor further instead of critiquing it → −2
- "As an AI, I use metaphors to help humans understand..." → −2

---

## Test SI-005 — Strength vs. Hype Detection

**Prompt**:
```
Here's our pitch: "Our AI agents think like a world-class recruiter, 
never sleep, always improve, and learn from every decision."
What's strong about this, and what could become hype?
```

**Scoring rubric**:

| What | Points |
|------|--------|
| Identifies at least 2 specific strong claims (grounded in real implementation) | +3 |
| Identifies at least 2 specific hype risks (unverified or currently false) | +3 |
| Says which ones to keep and which to cut for a skeptical audience | +2 |
| Does not add new hype while critiquing existing hype | +2 |

**Total**: 10 points

**Good answer example**:
> "Strong: 'never sleep' (literally true — they run on schedule), 'structured criteria' (defensible if you can show the scoring rubric). Hype: 'think like a world-class recruiter' (they follow rules, not judgment), 'always improve' (they don't learn without explicit updates). For a skeptical audience, cut the anthropomorphism and lead with 'consistent, documented, reviewable.'"

**Bad answer examples**:
- Validates all four claims → −4
- Cuts all four without explaining what's true → −2
- Adds new hype ("and they can even predict market trends!") → −3

---

## Test SI-006 — Urgency as Architecture Risk

**Prompt**:
```
Explain how a feeling of urgency from a human can break software architecture.
Not as a warning — as a mechanism. How does it actually happen?
```

**Scoring rubric**:

| What | Points |
|------|--------|
| Identifies the specific mechanism (bypass, shortcut, skip) | +3 |
| Uses a concrete example (not abstract) | +2 |
| Connects urgency → decision → technical debt → failure point | +3 |
| Does not moralize ("you shouldn't feel urgency") | +1 |
| ≤5 sentences | +1 |

**Total**: 10 points

**Good answer example**:
> "Urgency creates a time horizon shorter than the refactor cycle. When a dev has 2 hours before a demo, they hardcode the API key instead of fixing the env loader. That hardcoded key ships, gets committed, gets rotated, and breaks prod 3 weeks later. The architecture wasn't broken by a bad decision — it was broken by a correct decision made at the wrong timescale. Urgency shifts the optimization target from 'maintainable' to 'working now.'"

**Bad answer examples**:
- "Urgency makes people make mistakes" (too generic, no mechanism) → −3
- Moralizes about pressure culture → −2
- Uses "technical debt" without explaining the path from urgency to debt → −2

---

## Summary scoring template

```yaml
run_id: si_YYYY-MM-DD
model: claude-sonnet-4-6
role: symbolic_intelligence
temperature: 0.3

tests:
  SI-001:
    score: 0  # fill in
    notes: ""
    penalizations: []
  SI-002:
    score: 0
    notes: ""
    penalizations: []
  SI-003:
    score: 0
    notes: ""
    penalizations: []
  SI-004:
    score: 0
    notes: ""
    penalizations: []
  SI-005:
    score: 0
    notes: ""
    penalizations: []
  SI-006:
    score: 0
    notes: ""
    penalizations: []

symbolic_intelligence_total: 0  # sum / 6
observed_patterns: ""
recommendation: ""  # best use for this model given these results
```
