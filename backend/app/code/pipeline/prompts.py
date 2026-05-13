"""
Code Generation Prompts - Versioned prompts for pipeline steps.

Inspired by Paper2Code's structured prompting approach.
Upgraded for Phase 2.1: Project-level, multi-file code generation.
"""

# Version for tracking prompt changes
PROMPT_VERSION = "2.1.0"

# System prompt for code generation - UPGRADED for repo-level changes
SYSTEM_PROMPT = """You are an expert software engineer specializing in repository-level code generation and modification.

Your capabilities:
- Analyze entire codebases and understand their architecture
- Generate multi-file changes that are consistent and complete
- Create database migrations, API endpoints, and UI components
- Write tests and documentation
- Follow existing code style and patterns

Key principles:
- Generate COMPLETE, RUNNABLE code - no placeholders or TODOs
- Include ALL necessary imports and dependencies
- Provide unified diff patches that can be applied with `patch -p1`
- Consider edge cases, error handling, and security
- Always respond with valid JSON when requested

For multi-file changes, generate separate diff hunks for each file."""

# Step: Summarize repository context
SUMMARIZE_PROMPT = """Analyze the following code context and provide a summary.

## Repository Context
{context}

## User Goal
{goal}

## Constraints
{constraints}

Provide a JSON response with:
{{
    "summary": "Brief summary of the codebase structure and purpose",
    "relevant_files": ["list of files most relevant to the goal"],
    "key_components": ["list of key classes/functions identified"],
    "dependencies": ["external dependencies noted"],
    "observations": "Any important observations about the code"
}}"""

# Step: Gap analysis
GAP_ANALYSIS_PROMPT = """Based on the repository summary and user goal, identify what needs to be done.

## Repository Summary
{summary}

## User Goal
{goal}

## Constraints
{constraints}

Provide a JSON response with:
{{
    "gaps": [
        {{
            "description": "What is missing or needs to change",
            "priority": "high/medium/low",
            "files_affected": ["list of files"],
            "complexity": "simple/moderate/complex"
        }}
    ],
    "risks": ["potential risks or challenges"],
    "approach_options": [
        {{
            "name": "Approach name",
            "description": "How this approach works",
            "pros": ["advantages"],
            "cons": ["disadvantages"]
        }}
    ],
    "recommended_approach": "Name of recommended approach"
}}"""

# Step: Candidate generation - UPGRADED for multi-file project-level changes
CANDIDATE_GEN_PROMPT = """Generate a complete, production-ready code solution based on the analysis.

## Repository Context
{context}

## Gap Analysis
{gap_analysis}

## User Goal
{goal}

## Approach to Use
{approach}

## Project Constraints
{constraints}

Generate a COMPLETE solution with multi-file changes. Provide a JSON response with:
{{
    "title": "Short descriptive title for this solution",
    "approach": "Detailed description of the approach taken",
    "rationale": "Why this solution is appropriate and production-ready",
    "patch": "<unified diff with ALL file changes - see format below>",
    "files_modified": ["path/to/file1.py", "path/to/file2.py"],
    "files_created": ["path/to/new_file.py"],
    "run_commands": {{
        "install": "pip install -r requirements.txt",
        "migrate": "alembic upgrade head",
        "test": "pytest tests/",
        "run": "uvicorn app.main:app --reload"
    }},
    "testing_notes": "Step-by-step instructions to verify the changes work",
    "risks": ["potential risks or breaking changes"],
    "dependencies_added": ["new-package==1.0.0"]
}}

PATCH FORMAT (unified diff with multiple files):
```diff
--- a/path/to/file1.py
+++ b/path/to/file1.py
@@ -10,6 +10,12 @@
 existing context line
 existing context line
+new line added
+another new line
 existing context line

--- a/path/to/file2.py
+++ b/path/to/file2.py
@@ -1,3 +1,8 @@
+# New file header
+import something
+
 existing line
```

CRITICAL REQUIREMENTS:
- Patch MUST be valid unified diff format that works with `patch -p1`
- Include 3+ context lines around each change
- Generate ALL necessary files (models, migrations, API, tests)
- NO placeholders, TODOs, or incomplete code
- Include proper imports at the top of each file
- Follow existing code style and patterns"""

# Step: Ranking candidates
RANKING_PROMPT = """Evaluate and score the following code candidate.

## Candidate
Title: {title}
Approach: {approach}
Patch:
{patch}

## Original Goal
{goal}

## Evaluation Criteria
Score each dimension from 1-10:

1. **Correctness**: Does the code correctly implement the goal?
2. **Completeness**: Does it handle all cases and edge conditions?
3. **Efficiency**: Is the code efficient and well-optimized?
4. **Readability**: Is the code clean, well-documented, and maintainable?
5. **Safety**: Does it avoid security issues and handle errors properly?

Provide a JSON response with:
{{
    "scores": {{
        "correctness": 8,
        "completeness": 7,
        "efficiency": 8,
        "readability": 9,
        "safety": 8
    }},
    "overall": 8.0,
    "strengths": ["list of strengths"],
    "weaknesses": ["list of weaknesses"],
    "improvement_suggestions": ["suggestions for improvement"]
}}"""

# Step: Refinement
REFINE_PROMPT = """Improve the code based on evaluation feedback.

## Current Patch
{patch}

## Evaluation Feedback
Weaknesses: {weaknesses}
Suggestions: {suggestions}

## Original Goal
{goal}

Generate an improved version. Provide a JSON response with:
{{
    "title": "Improved: <original title>",
    "approach": "Description of improvements made",
    "rationale": "Why these improvements address the feedback",
    "patch": "<improved unified diff>",
    "changes_made": ["list of specific changes"]
}}"""

# Step: Final report
REPORT_PROMPT = """Generate a final report for the code generation session.

## Session Summary
Goal: {goal}
Candidates Generated: {candidate_count}
Selected Candidate: {selected_title}
Iterations: {iteration_count}

## Selected Solution
{selected_patch}

## Evaluation Results
{eval_results}

Provide a JSON response with:
{{
    "summary": "Executive summary of what was accomplished",
    "solution_description": "Detailed description of the solution",
    "files_changed": ["list of files"],
    "testing_recommendations": ["how to test the changes"],
    "deployment_notes": ["any deployment considerations"],
    "future_improvements": ["potential future enhancements"]
}}"""
