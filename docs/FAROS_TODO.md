# FAROS TODO

This file is the structured backlog for the next FAROS phases after the first release baseline.

It is intentionally more detailed than the short TODO summary in the root README.
Tasks here are grouped by milestone, then by concrete engineering objective.

---

## 1. Roadmap Overview

### Release Baseline Completed

Already landed in the current release branch:
- FAROS runtime package exists
- FAROS API exists
- blueprint and profile loading exists
- capability registry and provider registry exist
- file-backed FAROS runs, events, artifacts, and memory exist
- current LLM workflow exists:
  - `idea -> experiment -> paper -> review`

### Next Phases

- `P0`: make the current LLM workflow deeper and safer
- `P1`: strengthen runtime quality, verification, and frontend visibility
- `P2`: generalize FAROS into a wider AutoResearch platform

---

## 2. P0 Runtime Hardening

Goal:
Make the current FAROS runtime safe enough to support more capabilities and more contributors without rewriting it again immediately.

### P0.1 Replace linear execution with true graph semantics

Current state:
- the graph builder is effectively linear
- blueprint edges are present but not yet used as a real execution planner

Tasks:
- implement dependency-aware graph planning
- validate no missing upstream nodes before execution
- support topological ordering
- detect cycles and invalid graphs at load time
- surface graph validation errors through FAROS API

Acceptance:
- blueprint load fails clearly on cycles
- runtime can execute workflows based on edges rather than implicit order only
- tests cover valid DAG and invalid DAG cases

### P0.2 Run lifecycle controls

Current state:
- runs can be created and executed
- cancellation, retry, and resume are not properly supported

Tasks:
- add explicit FAROS run states for retryable failure vs terminal failure
- add retry operation for failed runs
- add resume operation for interrupted runs
- add cancellation semantics
- record retry history in event log

Acceptance:
- a failed run can be retried without manual JSON edits
- cancellation updates state cleanly
- run lifecycle transitions are validated

### P0.3 Step-level execution safety

Tasks:
- add step timeouts
- add per-step error categorization
- add provider failure classification vs capability failure classification
- add budget / token guardrails where meaningful

Acceptance:
- one broken capability does not produce ambiguous runtime state
- failure reason is visible in run detail and events

### P0.4 Event model cleanup

Current state:
- events are still mostly free-form dictionaries

Tasks:
- define event schema categories: lifecycle, capability, verification, artifact, provider, warning, error
- normalize event payloads
- add event versioning field for future compatibility

Acceptance:
- event consumers no longer rely on free-form message parsing only

---

## 3. P0 LLM Workflow Depth

Goal:
The current LLM workflow should become truly useful, not just structurally complete.

### P0.1 Idea stage depth

Tasks:
- split current `idea_refinement` into smaller internal or future external capability steps:
  - `literature_understanding`
  - `gap_analysis`
  - `idea_ranking`
- improve literature evidence mapping
- make candidate selection traceable and explainable
- attach richer structured outputs for downstream paper and experiment stages

Acceptance:
- downstream stages consume structured idea outputs without scraping large blobs
- candidate quality is easier to evaluate and debug

### P0.2 Experiment stage depth

Current state:
- `experiment` currently provisions project + experiment records and a minimal scaffold
- it does not yet perform true autonomous code synthesis and execution

Tasks:
- replace scaffold-only experiment stage with real code generation for the LLM domain
- decide execution contract for the first true experiment capability
- support experiment design output from selected idea candidate
- generate execution scripts, config, and evaluation entrypoints
- connect experiment record to figures, metrics, and later paper evidence

Acceptance:
- experiment stage produces a meaningful runnable research project
- project and experiment outputs are usable by paper stage directly

### P0.3 Run / metric / figure integration

Tasks:
- connect experiment outputs to run creation or run referencing
- enable metrics ingestion into experiment path
- enable figure generation and figure referencing for paper stage
- define minimal experiment evidence contract for paper grounding

Acceptance:
- paper stage can consume experiment-linked metrics and figures through explicit fields

### P0.4 Paper stage depth

Tasks:
- improve run and experiment grounding in prompts and output artifacts
- strengthen section consistency checks
- strengthen citation verification and evidence binding
- better reflect experiment outputs in methods and experiments sections

Acceptance:
- paper content is less detached from upstream experiment state

### P0.5 Review stage depth

Tasks:
- separate review outputs into structured categories more cleanly
- connect review action items back to FAROS artifacts or follow-up requests
- improve reviewer prompts with experiment awareness

Acceptance:
- review is more actionable and less like a generic paper critique

---

## 4. P0 Provider Layer

Goal:
Make provider handling less hardcoded and more runtime-native.

### P0.1 Remove hardcoded profile assumptions

Current state:
- `faros_llm` currently includes fixed provider defaults in the profile asset

Tasks:
- allow profile to inherit active provider/model by policy
- make explicit override optional rather than mandatory
- define provider resolution precedence

Suggested precedence:
1. request input override
2. profile binding override
3. runtime active provider/model
4. provider config default

### P0.2 Add fallback policy support

Tasks:
- support fallback model lists per capability
- distinguish provider unavailable vs provider rejected vs quota exceeded
- log provider fallback decisions explicitly

### P0.3 Prepare non-LLM providers

Tasks:
- define `tool` provider contract
- define `human` provider contract
- keep interfaces generic enough for later domain-specific systems

Acceptance:
- provider abstraction is no longer effectively LLM-only in design

---

## 5. P1 Verification

Goal:
Move verification from “field exists” to “result is trustworthy enough to continue”.

### P1.1 Structural verification

Tasks:
- expand required-key checks into typed output-schema checks
- validate artifact presence where required
- validate stage-to-stage dependency contracts

### P1.2 Evidence verification

Tasks:
- verify paper evidence linkage
- verify experiment-linked claims have upstream support
- verify review findings reference real sections or outputs

### P1.3 Consistency verification

Tasks:
- check naming consistency across stages
- check venue constraints in paper stage
- check idea -> experiment -> paper continuity

### P1.4 Blueprint-level verification assets

Tasks:
- allow verification rules to be loaded from blueprint assets
- separate runtime-wide default verification from blueprint-specific verification

Acceptance:
- blueprints can express domain-specific quality gates

---

## 6. P1 Research Memory

Goal:
Turn FAROS memory from a flat merged dictionary into a meaningful runtime component.

### P1.1 Typed memory partitions

Tasks:
- separate run-scoped memory from node-scoped memory
- define artifact-backed memory vs transient context memory
- avoid uncontrolled key collision across capabilities

### P1.2 Retrieval support

Tasks:
- allow later capabilities to query prior outputs by type
- support memory views such as:
  - selected idea
  - current experiment evidence
  - current paper summary
  - current review actions

### P1.3 Cross-run reuse

Tasks:
- support retrieval from prior runs where useful
- prepare memory for future iterative or branching workflows

---

## 7. P1 Frontend

Goal:
Expose FAROS as a first-class runtime, not only through module-native pages.

### P1.1 FAROS console

Tasks:
- add blueprint list page
- add profile list page
- add run creation page
- add run detail page
- add event timeline view
- add artifact list view
- add verification panel

### P1.2 Keep module-native tooling intact

Tasks:
- preserve current module pages for direct debugging and editing
- do not force all workflows through FAROS UI immediately

Acceptance:
- frontend supports both runtime view and module view

---

## 8. P1 Storage

Goal:
Stabilize runtime persistence without rushing unnecessary rewrites.

### P1.1 DB-backed FAROS metadata

Tasks:
- define DB models for:
  - `faros_runs`
  - `faros_steps`
  - `faros_artifacts`
  - `faros_memories`
- keep large payloads and artifact files on filesystem initially

### P1.2 Migration strategy

Tasks:
- define migration path from current JSON-only FAROS persistence
- keep backward compatibility during migration

Acceptance:
- move toward queryable runtime state without breaking existing artifacts

---

## 9. P2 Ecosystem Expansion

Goal:
Generalize FAROS beyond one LLM research workflow.

### P2.1 More blueprints

Candidate blueprint families:
- reproducibility reports
- benchmark studies
- survey / synthesis workflows
- domain-specific scientific workflows

### P2.2 More profiles

Candidate profile families:
- LLM-heavy fast profile
- verification-heavy profile
- human-in-the-loop profile
- code-execution-heavy profile

### P2.3 Plugin contract

Tasks:
- define plugin format for third-party blueprints
- define plugin format for third-party capabilities
- define version compatibility expectations

---

## 10. Suggested Task Packaging

For task splitting, prefer this format:

### Task Template

- Title
- Target area
- Priority
- Goal
- Allowed write scope
- Interface changes
- Data / storage impact
- Required tests
- Non-goals
- Acceptance criteria

### Example split areas

- Runtime orchestration
- Runtime memory and artifacts
- Provider system
- Idea capability depth
- Experiment capability depth
- Paper evidence grounding
- Review actionability
- Frontend FAROS console
- Storage migration
- Verification framework

---

## 11. Current Highest-Value Next Tasks

If work starts immediately after this release, the best order is:

1. real graph execution instead of linear planning
2. deepen `experiment` for true LLM-domain code synthesis and execution
3. connect experiment outputs to metrics and figures
4. improve paper evidence grounding
5. upgrade verification rules
6. add a FAROS frontend console

That order keeps the runtime coherent while improving real workflow value.
