# FAROS Developer Guide

## 1. Purpose

This document is the working handbook for contributors to the FAROS release branch.

The repository is no longer just a cleaned copy of `LLM-Scientist`.
Its current role is:

- preserve a runnable LLM-domain release baseline
- evolve the project from an application into a reusable AutoResearch runtime
- keep the system safe for parallel development by multiple contributors
- make future refactors happen behind stable module and runtime boundaries

This guide is therefore not a conceptual overview.
It is an operational document for people changing the code.

---

## 2. Current Product Definition

FAROS currently means:

- a runtime under `backend/app/faros`
- domain implementations under `backend/app/modules/*`
- one runnable baseline profile: `faros_llm`
- one runnable baseline blueprint: `ml_paper`
- one current end-to-end workflow:
  - `idea -> experiment -> paper -> review`

The system is intentionally in a transitional state.

What is already true:
- FAROS has its own runtime package
- FAROS owns blueprint loading, profile loading, run orchestration, runtime memory, event logging, artifact recording, and baseline verification
- the old domain modules still provide the real implementation logic

What is not yet true:
- FAROS is not yet a full DAG scheduler
- FAROS is not yet cross-domain in a mature sense
- the `experiment` stage is a baseline scaffold, not full autonomous code synthesis + execution
- frontend still exposes module-native tooling more strongly than runtime-native FAROS tooling

---

## 3. Codebase Map

### 3.1 Runtime Layer

Path:
- `backend/app/faros/`

Responsibility:
- runtime models
- blueprint/profile asset loading
- capability registry
- provider registry
- orchestrator
- run state persistence
- event log
- artifact recording
- research memory
- verification hooks
- FAROS API

Treat this directory as the primary surface for all future runtime work.

### 3.2 Domain Module Layer

Paths:
- `backend/app/modules/idea`
- `backend/app/modules/code`
- `backend/app/modules/paper`
- `backend/app/modules/review`
- `backend/app/modules/platform`

Responsibility:
- actual business logic and storage facades for the current LLM workflow
- stable integration points for FAROS capability adapters
- module-native APIs that remain useful for debugging, direct use, or frontend integration

### 3.3 Legacy / Compatibility Layer

Paths:
- `backend/app/api/v1/*`
- `backend/app/services/*`

Responsibility:
- compatibility wrappers
- legacy service implementations still used by current modules
- migration residue from the earlier product structure

These directories still matter operationally, but they should not be treated as the preferred home for new architecture.

---

## 4. Module Ownership and Boundaries

### 4.1 `idea`

Path:
- `backend/app/modules/idea`

Owns:
- idea session lifecycle
- literature-linked candidate generation
- ranking and selection output
- idea contracts and storage facade

Good future work here:
- better literature retrieval
- gap extraction and evidence grounding
- multi-judge scoring
- stronger candidate traceability
- structured idea evaluation

Do not use this module for:
- shared orchestration logic
- global provider policy
- cross-workflow memory handling

### 4.2 `code`

Path:
- `backend/app/modules/code`

Owns:
- code sessions
- code projects
- generation status
- repository browsing and indexing
- code project persistence and export

Good future work here:
- true code synthesis for FAROS experiment stage
- greenfield repo generation
- repo understanding and planning
- execution validation
- structured experiment/code linkage

Do not use this module for:
- global FAROS run state
- runtime memory merging
- provider orchestration across capabilities

### 4.3 `paper`

Path:
- `backend/app/modules/paper`

Owns:
- paper records
- paper context linkage
- LaTeX assembly
- PDF generation
- venue-aware template integration

Good future work here:
- stronger evidence grounding from experiments and runs
- better section constraints
- claim-to-evidence consistency checks
- citation verification improvements
- richer artifact packaging

Do not use this module for:
- generalized workflow logic
- non-paper global verification policy

### 4.4 `review`

Path:
- `backend/app/modules/review`

Owns:
- review records
- review generation
- action item extraction
- improvement requests

Good future work here:
- review schema refinement
- paper/code/idea-specific review tracks
- review severity normalization
- improvement request automation

Do not use this module for:
- global memory
- runtime policy branching

### 4.5 `platform`

Path:
- `backend/app/modules/platform`

Owns:
- shared providers
- experiments
- runs
- templates
- plan links
- shared storage facades and system-level endpoints

Good future work here:
- provider settings and lifecycle
- experiment/runs shared infrastructure
- template distribution
- stable cross-module storage surfaces

Do not use this module for:
- stuffing unrelated module-specific logic just because multiple modules touch it once

---

## 5. FAROS Runtime Boundaries

### 5.1 What Belongs in `faros/`

Put code in `backend/app/faros` when it is about:
- executing workflows
- interpreting blueprints
- binding profiles
- resolving providers
- coordinating capability execution
- storing FAROS run metadata
- storing FAROS events
- storing FAROS runtime memory
- validating capability outputs at runtime
- exposing FAROS runtime APIs

### 5.2 What Does Not Belong in `faros/`

Do not put code in `backend/app/faros` when it is actually about:
- how idea generation works internally
- how paper drafting works internally
- how code projects are stored and indexed internally
- how a review report is formatted in detail

That logic belongs in the domain modules and should be reached through adapters.

### 5.3 Adapter Rule

If FAROS needs to use an existing module capability:
1. keep the real logic in the module
2. create or refine an adapter in `faros/capabilities/adapters`
3. normalize the output into a `CapabilityResult`
4. never clone the module’s business logic into FAROS unless the module is being intentionally retired

---

## 6. Approved Development Surfaces

### Preferred places for new work

Within a domain module:
- `router.py`
- `*_api.py`
- `service.py`
- `storage.py`
- `contracts.py`
- `interfaces.py`

Within FAROS:
- `models/`
- `runtime/`
- `registry/`
- `capabilities/`
- `providers/`
- `verification/`
- `api/`
- `blueprints/`
- `profiles/`

### Avoid for new long-term architecture

- `backend/app/api/v1/*`
- `backend/app/services/*`

These paths can still be edited when necessary for release stability or migration, but they should not accumulate new architecture by default.

---

## 7. Runtime and Storage Rules

### 7.1 Current Storage Model

The repository currently uses a mixed model:
- DB-backed state for parts of the code module
- filesystem-backed state for many runtime and artifact paths
- JSON-backed records for papers, reviews, experiments, FAROS runs, and some metadata

This is accepted for the current release baseline.

### 7.2 Current Rule of Thumb

- use filesystem / JSON where the system already uses filesystem / JSON and stability matters more than purity
- avoid introducing a second new storage pattern unless necessary
- if adding FAROS runtime state, prefer extending the existing FAROS file-backed store unless the work is explicitly a storage migration task

### 7.3 Artifact Rule

Every capability should ideally emit:
- a normalized output payload
- zero or more artifact records
- enough metadata for later reconstruction and downstream consumption

If a capability produces something durable, record it as a FAROS artifact even if the payload already exists elsewhere.

---

## 8. How To Add New Runtime Work

### 8.1 Add a Capability

Checklist:
1. decide whether this is a true new capability or just a refinement inside an existing module
2. add or update an adapter under `backend/app/faros/capabilities/adapters`
3. return a normalized `CapabilityResult`
4. register the capability in `backend/app/faros/registry/capability_registry.py`
5. update verification rules if required outputs changed
6. update relevant blueprint assets if the workflow graph changes
7. add or update tests

### 8.2 Add a Blueprint

Checklist:
1. add a new asset under `backend/app/faros/blueprints/<blueprint_id>/blueprint.json`
2. keep the graph and outputs explicit
3. declare required capability order and output expectations clearly
4. avoid embedding provider assumptions into the blueprint
5. test that it loads and that plan-mode creation works

### 8.3 Add a Profile

Checklist:
1. add a new asset under `backend/app/faros/profiles/<profile_id>/profile.json`
2. keep provider bindings explicit
3. avoid mixing business logic into the profile
4. use the profile to express execution strategy, not workflow semantics

### 8.4 Add a Provider

Checklist:
1. add the provider implementation under `backend/app/faros/providers`
2. register it in `provider_registry.py`
3. keep the provider API generic
4. do not leak one provider’s assumptions into all capabilities

---

## 9. Parallel Development Rules

The repository is being prepared for multi-contributor work.
These rules matter.

### 9.1 Split by ownership, not random files

Prefer assigning tasks by:
- runtime
- idea
- code
- paper
- review
- platform
- docs / release

### 9.2 Every task should define

- target module or runtime area
- allowed write scope
- public interfaces touched
- storage implications
- required tests
- explicit non-goals

### 9.3 Avoid cross-cutting surprise edits

If you are touching more than one of the following in one task:
- `faros/runtime`
- `modules/code`
- `modules/paper`
- `modules/platform`

then document the reason clearly, because those are the areas most likely to create unintended coupling.

---

## 10. Testing and Validation

### 10.1 Current expected checks

Backend syntax:
- `python -m py_compile ...`

Backend tests in the known working environment:
- `cd backend && conda run -n aist python -m pytest -q tests`

Release checks:
- `bash scripts/check_release.sh`
- `bash backend/scripts/check_backend_release.sh`
- `bash frontend/scripts/check_frontend_release.sh`

### 10.2 When specific checks are mandatory

If you touch FAROS runtime:
- run backend tests
- validate FAROS route mounting
- validate blueprint/profile loading

If you touch paper templates or rendering:
- compile-check the paper path
- ensure a PDF path still exists

If you touch code project storage or experiment linkage:
- validate creation path for project and experiment records
- ensure IDs propagate into downstream steps

### 10.3 Current accepted warnings

Known warnings still accepted in this release branch:
- Pydantic v2 config deprecation warnings
- `datetime.utcnow()` deprecation warnings
- FastAPI `on_event` deprecation warnings

Do not ignore them forever, but do not derail unrelated release work to eliminate them unless your task is specifically cleanup.

---

## 11. Known Technical Debt

These are known and accepted right now:

1. FAROS execution is still linear, not a true DAG scheduler.
2. `experiment` is currently a scaffold, not full code synthesis + execution.
3. Several modules still depend on legacy `app.services` implementations.
4. Storage is mixed across DB, JSON, and filesystem paths.
5. Verification is still baseline-level and mostly structural.
6. Frontend is still more module-native than FAROS-native.
7. Some release-facing docs and runtime conventions are still stabilizing.

---

## 12. Pre-PR Checklist

Before opening a PR or handing off a patch:

- backend Python files compile
- targeted backend tests pass
- no secrets are committed
- no local runtime data is committed
- no `node_modules`, `dist`, `.venv`, `.verify-venv`, or generated DB files are committed
- paper template changes are compile-validated if touched
- README / docs changes match the current release direction
- FAROS-facing changes are reflected in blueprint/profile/runtime docs if relevant

---

## 13. Contributor Rule of Thumb

If you are unsure where code should go:

- if it changes how research workflows are executed, it probably belongs in `faros/`
- if it changes how one domain feature actually works, it probably belongs in `modules/*`
- if it only exists because of old compatibility, do not make it the new default extension surface
