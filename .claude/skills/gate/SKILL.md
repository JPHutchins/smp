---
name: gate
description: Keep the workspace green while you edit — the free PostToolBatch autofix, and delegating the check-and-fix loop to the camas-fixer subagent so residuals never spend your reasoning. Read after a batch of edits and before declaring work done.
---

The camas gate keeps the workspace green as you edit, in two layers — both driven by what the
project declares in `Config.agent`:

- **Fix (automatic, free).** A `PostToolBatch` hook runs `camas mcp fix` after each edit batch —
  the node the project registered as `Config.agent.fix` (its mutating, behavior-preserving
  auto-fixers: formatters, `--fix` linters), scoped to the just-changed files (delivered on
  stdin), at zero model tokens. It never asks you anything; with no fix registered it is a no-op.
- **Check (you delegate — there is no check hook).** The check node (`Config.agent.check`,
  else the default task) is read-only: it runs the project's checks and classifies the result
  `green` or `needs_reasoning`. After a batch of edits, and before you declare work done,
  **delegate the check-and-fix loop to the `camas-fixer` subagent** rather than running the
  checks and chasing residuals in your own context.

Delegate by spawning `camas-fixer` with the changed paths as its scope. It gates that scope,
fixes what it can, and re-gates in a loop on a cheap model, in its own context window — so the
loop costs you no reasoning and only its final result returns. Run it in the background and
keep working; for independent changed scopes, spawn one fixer per scope so they run in
parallel. Each fixer hands back only what it could not settle: a green result means that scope
is done; a result quoting remaining diagnostics is the residual that needs your reasoning —
take it from there.

Never mask a residual — yours or a fixer's: do not suppress, disable, or loosen a check to
make the gate pass. A green gate must mean the work is actually correct.