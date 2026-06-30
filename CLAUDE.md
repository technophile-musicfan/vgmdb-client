# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Create beads tasks AFTER `/superpowers:writing-plans` produces the plan — never before; tasks must reflect the plan structure
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember "insight"` for ALL persistent knowledge — search with `bd memories <keyword>`
- Do NOT use the auto-memory file system (the `~/.claude-personal/.../memory/` directory) — ignore it entirely
- **Track every deferral.** When a design/spec marks something "Out of scope" or an "accepted caveat", file a bead for it in the **same commit** as the doc — *documented ≠ tracked*. (A 2026-06-13 audit found 4 leaked caveats: API-token hashing, ObjectStore GC, Postgres manual migrations, rebase-assets.)

## Session Completion

1. **File issues for remaining work** — create issues for anything needing follow-up
2. **Update issue status** — close finished work, update in-progress items
3. **Push beads** — `bd dolt push` before finishing the branch

> Git push is handled by `/superpowers:finishing-a-development-branch` (Workflow 2, step 11).
<!-- END BEADS INTEGRATION -->


## Tool Ecosystem

Three layers work together — each has a specific role:

| Tool | Role |
|------|------|
| **OpenSpec** | Spec layer — delta specs, living docs, and feature proposals only |
| **Superpowers** | Implementation layer — brainstorming, planning, executing |
| **Beads** | Tracking layer — cross-session issue/epic tracking |

## Development Workflows

### Workflow 1: Product Vision (Initial Design)

Use when starting a new product or defining major scope.

1. **Brainstorm vision** — `/superpowers:brainstorming`; Claude asks "what does done look like?", surfaces constraints and goals
2. **Define feature map** — second brainstorm refines into feature areas (MVP / Beta / V1) with dependency map
3. **Save brainstorm docs** to `docs/superpowers/`:
   - Vision doc: `YYYY-MM-DD_<major_scope>.md`
   - Feature map: `YYYY-MM-DD_<major_scope>_feature_map.md`
4. **Create Beads epics** — one epic per feature area, with description and sub-epic for each major feature.

> **STOP.** Workflow 1 ends here. Do NOT start Workflow 2 unless explicitly asked to work on a feature.

### Workflow 2: Feature Implementation

Use for each individual feature once the epic exists.

> **Ceremony scaling inside W2 (decided 2026-06-13, bead 3s6).** Three steps are **non-negotiable — never skip or substitute**: step 8 `/opsx:verify` (NOT `openspec validate` — that only checks the spec is well-formed; verify checks implementation-vs-delta and catches e.g. unticked tasks), step 9 `/opsx:archive` (a skipped archive is silent — it leaves a shipped change rotting in `openspec/changes/`; added 2026-06-13 after rvq.27 Change A was found un-archived), and step 10 `/code-review`. Steps 5 (`writing-plans` as a **separate** plan doc) and 7 (`/superpowers:subagent-driven-development` with its per-unit spec-review → quality-review) are **required only when the change adds/changes schema OR spans ≥2 subsystems**; for a single-subsystem, no-schema feature the openspec `design.md`+`tasks.md` may serve as the plan and beads may be **grouped** (not one-per-step), with implementation by direct subagent dispatch that still ends in a real `/code-review`. The brainstorm → propose → verify-delta → worktree → archive → finish spine is always run. When in doubt, go full.

1. **Brainstorm** — `/superpowers:brainstorming` to surface unknowns; produces a design document saved to `docs/superpowers/<major_scope>/YYYY-MM-DD_<feature_name>_design.md`

   > **Transition after brainstorm:** The next step is ALWAYS `/opsx:propose` — prompt the user to run it. Never suggest `writing-plans` here. The brainstorming skill's terminal state says otherwise but it is WRONG for this project.

2. **Propose change spec** — `/opsx:propose` using the design doc + memory → delta spec created in `openspec/changes/`
3. **Verify delta** — make sure that the delta spec has no delta with the initial design
4. **Isolate workspace** — `/superpowers:using-git-worktrees`

   > **Pre-writing-plans gate** — steps 2 - 4 MUST be done before writing-plans. The brainstorming skill's terminal state says "invoke writing-plans" but that is WRONG for this project. Do NOT invoke writing-plans until the delta spec exists and the worktree is active.

5. **Write plan** — `/superpowers:writing-plans` using the delta spec + brainstorm design doc *(required for schema/multi-subsystem changes; for a single-subsystem no-schema feature the openspec `design.md`+`tasks.md` is the plan — see the ceremony-scaling note above)*
6. **Create Beads issues** — create tasks/subtasks following beads conventions, linked to the parent epic *(mirror the plan when one exists; otherwise group from the openspec `tasks.md`)*

   > **Pre-implementation gate** — beads issues MUST be created before starting implementation. Do NOT proceed to step 7 until issues exist.

7. **Implement** — `/superpowers:subagent-driven-development` or `/superpowers:executing-plans` (required for schema/multi-subsystem changes); otherwise direct subagent dispatch is fine *as long as step 10 still runs*
   > **Post-subtask gate** validate the corresponding checkbox in the delta spec

8. **Verify** — `/opsx:verify` *(non-negotiable; never substitute `openspec validate`)*
9. **Archive spec + workflow docs** — `/opsx:archive` *(non-negotiable; a skipped archive silently leaves a shipped change in `openspec/changes/`)*, then move this change's now-stale workflow docs into sibling `archive/` subfolders (keep the original filenames):
   - design doc → `docs/superpowers/<major_scope>/archive/`
   - plan → `docs/superpowers/plans/archive/`
   - any local design spec → `docs/superpowers/specs/archive/`

   > Archive the docs in the **same commit/step** as the opsx change so active folders only hold in-flight work. NEVER archive the Workflow 1 vision/feature-map docs (top-level `docs/superpowers/*.md`) or ad-hoc investigation/analysis notes — those are living docs.
10. **Code review** — `/code-review` before merging *(non-negotiable)*
11. **Finish branch** — `/superpowers:finishing-a-development-branch` (handles git push for feature branches; satisfies the Session Completion protocol above)

### Workflow 3: Explicit bugfix implementation

Use for targeted bugfixes where a spec is overkill but the change is non-trivial.

1. **Debug** — `/superpowers:systematic-debugging` to investigate root cause and scope
2. **Create Beads issue** — `bd create --type=bug` with reproduction steps and expected behavior
3. **Isolate workspace** — `/superpowers:using-git-worktrees`
4. **Implement** — `/superpowers:executing-plans` or direct edit
5. **Verify** — run tests; confirm bug is gone and no regressions
6. **Code review** — `/code-review` before merging
7. **Finish branch** — `/superpowers:finishing-a-development-branch`

> **STOP.** Do NOT use `/opsx:propose` for bugfixes — a delta spec is not required here.

### Workflow 4: Other workflow

Use for small tasks that don't warrant a feature workflow or bugfix investigation (docs, config, dependency bumps, refactors).

1. **Create Beads issue** — `bd create --type=task` describing the change
2. **Implement** — directly, no worktree needed unless risky
3. **Code review** — `/code-review` before merging
4. **Finish branch** — `/superpowers:finishing-a-development-branch` if on a branch, or commit directly to main for trivial changes
