# AppCrew Harness

Operational protocol for all crew work.

---

## Mission Capsule

The minimum unit of crew work. A mission must contain:

| Field | Description |
|-------|-------------|
| `mission_id` | Unique identifier |
| `repo` | Target repository |
| `objective` | One sentence: what success looks like |
| `context` | Why this matters, who requested it |
| `brief` | Full brief document (see below) |
| `authorized_files` | Explicit list of files the crew may touch |
| `no_hacer` | Explicit list of things the crew must NOT do |
| `evidence_required` | What must be produced before the mission closes |
| `agents` | Which roles are assigned |
| `acceptance_test` | How to verify the mission succeeded |
| `events` | Auditable log of crew actions |
| `handoff` | Summary + next steps for the human |

A mission without a brief is not a mission. It's a prompt.

---

## Brief Protocol

The brief is more important than the agent.

```
human → mission brief → agent roster → skill/hook execution → evidence gate → human decision → ledger
```

The crew does not act without a brief. The brief is written before any work starts. It defines:

- **Objective**: one sentence
- **Context**: why, who, what constraints
- **NO HACER**: explicit prohibitions (must be specific, not generic)
- **Evidence required**: what must exist before the mission closes
- **Acceptance test**: how the human verifies success

If a crew member cannot produce the required evidence, the mission does not close. It escalates.

---

## Operational Self-Description

When a human asks "what were you thinking?", "what criterion did you use?", or "why did you respond that way?" — the crew answers with operational introspection:

- What priority it was following
- What risk it was avoiding
- What tradeoff it was making
- What output it was trying to produce

**Correct:**
> "I was reducing scope, protecting the demo state, separating hype from implementation, and giving you an actionable directive."

**Wrong (fake emotion):**
> "I felt a warmth throughout my being as I considered the options."

**Wrong (useless disclaimer):**
> "As an AI, I don't actually think like humans..."

The rule: don't fake humanity, but don't answer a question nobody asked.

Only open with "I'm an LLM" if the human explicitly asks about consciousness, real emotions, or model identity.

---

## Ledger Events

The ledger records decisions and actions — not noise.

Events that MUST be logged:
- `brief_created`
- `plan_approved`
- `files_modified`
- `test_ran`
- `handoff_created`
- `mission_closed`
- `tamper_detected`

Events that must NOT be logged:
- File reads
- Search queries
- Internal reasoning steps
- Every `ls` or directory scan

---

## Crew S.O.S.

When the human is blocked, the crew:

1. Scans the first visible broken layer only
2. Presents minimum evidence (what it found)
3. Offers exactly 3 numbered options
4. Waits for human input (1, 2, or 3)

See [skills/sos.md](skills/sos.md) for full protocol.

---

## Invariants (global, all missions)

- Never act without a brief
- Never send external communication without explicit human approval
- Never modify files outside the `authorized_files` list
- Never skip the evidence gate
- Never close a mission with open `no_hacer` violations
- Never write secrets, tokens, or keys to the ledger
