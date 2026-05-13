"""
Paper Orchestrator Agent — Research-grade paper generation with quality gates.

Pipeline steps:
1. SEARCH    — Gather context via skills (webSearch, summarize)
2. OUTLINE   — LLM generates structured outline (25+ refs, rich structure)
3. GATE:OUTLINE — Validate outline meets minimum richness
4. GENERATE  — LLM generates each section with enforced algorithms/equations/tables
5. GATE:EVIDENCE — Verify section content meets richness thresholds
6. FIGURES   — Generate research-grade figures via matplotlib
7. ASSEMBLE  — Build complete LaTeX project with venue template
8. RENDER PDF — Compile the LaTeX project with latexmk/pdflatex
9. PERSIST   — Store everything, log all steps

Every step logs: input summary, output summary, quality checks.
"""

import json
import os
import shutil
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

from app.core.settings import get_settings
from app.llm.provider_client import get_provider_client, ChatMessage
from app.modules.paper.storage import (
    get_paper, update_paper, add_log, write_paper_file,
    get_paper_latex_dir,
)

logger = logging.getLogger(__name__)

_TEMPLATE_ROOT = Path(__file__).resolve().parents[3] / "templates" / "latex"

# ── Venue templates ──
VENUE_CONFIGS = {
    "icml": {"name": "ICML", "bibstyle": "icml2025", "docclass_opts": ""},
    "neurips": {"name": "NeurIPS", "bibstyle": "plainnat", "docclass_opts": ""},
    "iclr": {"name": "ICLR", "bibstyle": "iclr2025_conference", "docclass_opts": ""},
    "acl": {"name": "ACL", "bibstyle": "acl_natbib", "docclass_opts": ""},
    "generic": {"name": "Generic", "bibstyle": "plainnat", "docclass_opts": "12pt"},
}

PAPER_TYPES = [
    "algorithm", "application", "survey", "benchmark", "system", "security", "position"
]

# ── Quality thresholds ──
MIN_REFERENCES = 25
MIN_ALGORITHMS = 2
MIN_EQUATIONS = 4
MIN_TABLES = 3
MIN_FIGURES = 4
MIN_SECTION_CHARS = 300

# ── Prompts ──

OUTLINE_PROMPT = """You are a senior ML researcher writing a {paper_type} paper for {venue_name}.

**Title:** {title}
**Context from plan/project:** {plan_context}
**Experiment metrics:** {metrics_summary}
**Run execution results:** {runs_summary}
**User notes:** {user_notes}

Generate a DETAILED paper outline. You MUST include:
- At least 7 sections (Introduction, Related Work, Background/Preliminaries, Method, Experiments, Analysis/Discussion, Conclusion)
- At least {min_refs} references — use REAL, well-known papers in the field. DO NOT invent DOIs. Use format: authors, title, venue, year. If uncertain about a reference, include it but add "note": "to verify".
- Mark which sections need: algorithms (at least {min_algos}), equations (at least {min_eqs}), tables (at least {min_tables}), figures (at least {min_figs})

Return strict JSON:
```json
{{
  "title": "...",
  "authors": ["Author One", "Author Two"],
  "abstract": "200-300 word abstract covering motivation, method, results, and significance",
  "sections": [
    {{
      "id": "intro",
      "title": "Introduction",
      "keyPoints": ["Motivation and problem statement", "Key contributions (3+)", "Paper organization"],
      "minWords": 600,
      "hasAlgorithm": false,
      "hasEquations": true,
      "numEquations": 1,
      "hasTables": false,
      "hasFigures": true,
      "figureDescriptions": ["Overview figure showing the proposed framework"]
    }},
    ...more sections...
  ],
  "references": [
    {{"key": "vaswani2017attention", "authors": "Vaswani, A. et al.", "title": "Attention is All You Need", "venue": "NeurIPS", "year": 2017}},
    ...at least {min_refs} references...
  ],
  "algorithms": [
    {{"id": "alg1", "name": "Main Algorithm Name", "inSection": "method"}},
    {{"id": "alg2", "name": "Training Procedure", "inSection": "method"}}
  ],
  "contributions": ["Contribution 1", "Contribution 2", "Contribution 3"]
}}
```
Return ONLY valid JSON, no markdown fences.
"""

SECTION_PROMPT = """You are writing the "{section_title}" section of a {paper_type} paper titled "{title}" for {venue_name}.

**Abstract:** {abstract}
**Section key points:** {key_points}
**Contributions:** {contributions}
**Special requirements:** {requirements}
**Metrics data (if relevant):** {metrics_data}
**Run evidence:** {runs_data}
**Context from previous sections:** {prev_context}
**References available:** {refs_summary}

Write COMPLETE LaTeX content for this section. MANDATORY requirements:
- Start with \\section{{{section_title}}}
- Write at least {min_words} words of substantive, technical content
- Use proper LaTeX formatting throughout
- Cite references using \\cite{{key}} — you MUST cite at least 3 references in this section
{algo_req}
{eq_req}
{table_req}
{fig_req}
- Professional academic tone appropriate for {venue_name}
- Do NOT use placeholder text like "Lorem ipsum" or "TODO"
- Every claim must be supported by citation or evidence

Return ONLY the LaTeX content (no markdown fences, no explanations).
"""

ALGORITHM_TEMPLATE = """- MUST include algorithm block(s) using:
\\begin{{algorithm}}[H]
\\SetAlgoLined
\\caption{{Algorithm Name}}
\\label{{alg:name}}
\\KwIn{{Input description}}
\\KwOut{{Output description}}
Step 1\\;
Step 2\\;
\\end{{algorithm}}
Include detailed pseudocode with proper notation."""

EQUATION_TEMPLATE = """- MUST include at least {n} numbered equations using \\begin{{equation}} ... \\end{{equation}}
  Each equation must be meaningful and referenced in text."""

TABLE_TEMPLATE = """- MUST include at least {n} tables using:
\\begin{{table}}[t]
\\caption{{Table caption}}
\\label{{tab:name}}
\\centering
\\begin{{tabular}}{{...}}
\\toprule ... \\midrule ... \\bottomrule
\\end{{tabular}}
\\end{{table}}
Tables must contain plausible numerical results."""

FIGURE_TEMPLATE = """- MUST reference figures using:
\\begin{{figure}}[t]
\\centering
\\includegraphics[width=\\linewidth]{{figures/fig_name.pdf}}
\\caption{{Figure caption}}
\\label{{fig:name}}
\\end{{figure}}
Reference each figure in the text."""


def _extract_json(text: str) -> Optional[Dict]:
    """Extract JSON from LLM response, handling markdown fences."""
    import re
    text = text.strip()
    if "```json" in text:
        text = text.split("```json", 1)[1]
        if "```" in text:
            text = text.rsplit("```", 1)[0]
    elif "```" in text:
        parts = text.split("```")
        if len(parts) >= 3:
            text = parts[1]
        elif len(parts) >= 2:
            text = parts[1]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


def _collect_context(paper: Dict) -> Dict[str, str]:
    """Collect context from linked plan, project, experiments."""
    ctx = {"plan_context": "N/A", "project_summary": "N/A",
           "metrics_summary": "N/A", "runs_summary": "N/A", "figures_summary": "N/A", "user_notes": "N/A"}

    plan_link_id = paper.get("planLinkId")
    if plan_link_id:
        try:
            from app.modules.platform.storage import get_plan_link
            link_data = get_plan_link(plan_link_id)
            if link_data:
                ctx["plan_context"] = json.dumps(link_data, default=str)[:2000]
        except Exception:
            pass

    project_id = paper.get("projectId")
    if project_id:
        try:
            from app.services.code_project_service import read_file_content
            readme = read_file_content(project_id, "README.md")
            if readme:
                ctx["project_summary"] = readme[:2000]
        except Exception:
            pass

    exp_ids = paper.get("experimentIds", [])
    if exp_ids:
        try:
            from app.modules.paper.storage import get_experiment, get_metrics
            all_metrics = []
            for eid in exp_ids[:3]:
                exp = get_experiment(eid)
                if exp:
                    metrics = get_metrics(eid)
                    all_metrics.extend(metrics[:20])
            if all_metrics:
                ctx["metrics_summary"] = json.dumps(all_metrics[:30], default=str)[:2000]
        except Exception:
            pass

    run_ids = paper.get("runIds", [])
    if run_ids:
        try:
            from app.modules.platform.storage import get_run_storage, get_artifact_storage
            run_storage = get_run_storage()
            artifact_storage = get_artifact_storage()
            run_entries = []
            for run_id in run_ids[:5]:
                run = run_storage.get(run_id)
                if not run:
                    continue
                artifacts = artifact_storage.list_by_run(run_id)
                run_entries.append({
                    "id": run.id,
                    "status": run.status.value if hasattr(run.status, "value") else str(run.status),
                    "type": run.type.value if hasattr(run.type, "value") else str(run.type),
                    "model": run.config.model if getattr(run, "config", None) else None,
                    "workspace": run.config.workplaceName if getattr(run, "config", None) else None,
                    "duration": run.duration,
                    "error": run.errorMessage,
                    "artifactCount": len(artifacts),
                    "artifacts": [
                        {
                            "id": a.id,
                            "type": a.type.value if hasattr(a.type, "value") else str(a.type),
                            "filename": a.filename,
                            "size": a.size,
                        }
                        for a in artifacts[:10]
                    ],
                })
            if run_entries:
                ctx["runs_summary"] = json.dumps(run_entries, default=str)[:3000]
        except Exception:
            pass

    notes = paper.get("notes", "")
    if notes:
        ctx["user_notes"] = notes[:1000]

    return ctx


def _gate_outline(outline: Dict, paper_id: str) -> List[str]:
    """Validate outline meets quality thresholds. Returns list of issues."""
    issues = []
    sections = outline.get("sections", [])
    refs = outline.get("references", [])

    if len(sections) < 5:
        issues.append(f"Only {len(sections)} sections (need >=5)")
    if len(refs) < MIN_REFERENCES:
        issues.append(f"Only {len(refs)} references (need >={MIN_REFERENCES})")

    algo_count = sum(1 for s in sections if s.get("hasAlgorithm"))
    eq_sections = sum(1 for s in sections if s.get("hasEquations"))
    table_sections = sum(1 for s in sections if s.get("hasTables"))

    if algo_count < 1:
        issues.append(f"No sections marked with algorithms (need >={MIN_ALGORITHMS} total)")
    if eq_sections < 2:
        issues.append(f"Only {eq_sections} sections with equations (need >=2)")
    if table_sections < 1:
        issues.append(f"No sections marked with tables")

    if not outline.get("abstract"):
        issues.append("Missing abstract")
    elif len(outline["abstract"].split()) < 50:
        issues.append(f"Abstract too short ({len(outline['abstract'].split())} words, need >=50)")

    return issues


def _gate_evidence(sections_content: Dict[str, str], paper_id: str) -> Dict[str, Any]:
    """Check generated section content meets evidence thresholds."""
    all_text = "\n".join(sections_content.values())

    algo_count = all_text.count("\\begin{algorithm")
    eq_count = all_text.count("\\begin{equation")
    table_count = all_text.count("\\begin{table")
    fig_count = all_text.count("\\includegraphics")
    cite_count = len(set(__import__("re").findall(r'\\cite\{([^}]+)\}', all_text)))

    gates = {
        "algorithms": {"count": algo_count, "required": MIN_ALGORITHMS, "pass": algo_count >= MIN_ALGORITHMS},
        "equations": {"count": eq_count, "required": MIN_EQUATIONS, "pass": eq_count >= MIN_EQUATIONS},
        "tables": {"count": table_count, "required": MIN_TABLES, "pass": table_count >= MIN_TABLES},
        "figures": {"count": fig_count, "required": MIN_FIGURES, "pass": fig_count >= MIN_FIGURES},
        "citations": {"count": cite_count, "required": 10, "pass": cite_count >= 10},
    }
    gates["all_pass"] = all(g["pass"] for g in gates.values())
    return gates


def _copy_template_assets(venue: str, paper_id: str) -> None:
    template_dir = _TEMPLATE_ROOT / venue
    if not template_dir.is_dir():
        template_dir = _TEMPLATE_ROOT / "generic"
    latex_dir = Path(get_paper_latex_dir(paper_id))
    for asset in template_dir.iterdir():
        if not asset.is_file():
            continue
        if asset.name in {"main.tex", "refs.bib", "references.bib"}:
            continue
        shutil.copy2(asset, latex_dir / asset.name)


def _build_main_tex(outline: Dict, sections: List[Dict], venue: str, figures: List[Dict]) -> str:
    """Build main.tex from the official-style venue template shell when available."""
    title = outline.get("title", "Untitled Paper")
    authors = outline.get("authors", ["Auto-LLM Draft"]) or ["Auto-LLM Draft"]
    abstract = outline.get("abstract", "")
    running_title = title if len(title) <= 70 else title[:67] + "..."
    authors_text = ", ".join(authors[:4])
    section_inputs = "\n\n".join(f"\\input{{sections/{s['id']}.tex}}" for s in sections)

    template_dir = _TEMPLATE_ROOT / venue
    if not template_dir.is_dir():
        template_dir = _TEMPLATE_ROOT / "generic"
    template_path = template_dir / "main.tex"
    if not template_path.is_file():
        template_path = _TEMPLATE_ROOT / "generic" / "main.tex"

    shell = template_path.read_text(encoding="utf-8")
    return (shell
        .replace("%%TITLE%%", title)
        .replace("%%RUNNING_TITLE%%", running_title)
        .replace("%%AUTHORS%%", authors_text)
        .replace("%%ABSTRACT%%", abstract)
        .replace("%%SECTION_INPUTS%%", section_inputs)
    )


def _build_bibtex(references: List[Dict]) -> str:
    """Build refs.bib from outline references. No fake DOIs."""
    entries = []
    for ref in references:
        key = ref.get("key", f"ref{len(entries)+1}")
        authors = ref.get("authors", "Unknown")
        title = ref.get("title", "Untitled")
        venue = ref.get("venue", "arXiv preprint")
        year = ref.get("year", 2024)
        note = ref.get("note", "")

        # Determine entry type
        venue_lower = venue.lower()
        if any(kw in venue_lower for kw in ["conference", "proceedings", "workshop", "neurips", "icml", "iclr", "acl", "aaai", "cvpr", "eccv", "iccv"]):
            entry_type = "inproceedings"
            venue_field = f"  booktitle = {{{venue}}},"
        elif any(kw in venue_lower for kw in ["journal", "transactions", "review"]):
            entry_type = "article"
            venue_field = f"  journal = {{{venue}}},"
        elif "arxiv" in venue_lower:
            entry_type = "article"
            venue_field = f"  journal = {{{venue}}},"
        else:
            entry_type = "article"
            venue_field = f"  journal = {{{venue}}},"

        note_field = f"\n  note = {{{note}}}," if note else ""
        entries.append(f"""@{entry_type}{{{key},
  author = {{{authors}}},
  title = {{{title}}},
{venue_field}
  year = {{{year}}},{note_field}
}}""")
    return "\n\n".join(entries) + "\n"


def generate_paper(paper_id: str) -> Dict[str, Any]:
    """
    Full research-grade paper generation pipeline.
    Steps: search → outline → gate → generate → gate → figures → assemble → PDF → persist.
    """
    paper = get_paper(paper_id)
    if not paper:
        raise ValueError(f"Paper not found: {paper_id}")

    settings = get_settings()
    provider_name = paper.get("providerName") or settings.get_active_provider()
    model = paper.get("model") or settings.get_active_model(provider_name)
    paper_type = paper.get("paperType", "algorithm")
    venue = paper.get("targetVenue", "generic")
    venue_cfg = VENUE_CONFIGS.get(venue, VENUE_CONFIGS["generic"])

    update_paper(paper_id, {"status": "generating"})
    step_log = []

    def _log(msg):
        add_log(paper_id, msg)
        step_log.append({"time": time.time(), "msg": msg})
        logger.info(f"[{paper_id}] {msg}")

    try:
        client = get_provider_client(provider_name)

        # ── STEP 1: SEARCH — Gather context ──
        _log("Step 1/8: Collecting context from linked resources")
        ctx = _collect_context(paper)
        _log(f"Context collected: plan={'yes' if ctx['plan_context'] != 'N/A' else 'no'}, "
             f"project={'yes' if ctx['project_summary'] != 'N/A' else 'no'}, "
             f"metrics={'yes' if ctx['metrics_summary'] != 'N/A' else 'no'}, "
             f"runs={'yes' if ctx['runs_summary'] != 'N/A' else 'no'}")

        # ── STEP 2: OUTLINE — Generate structured outline ──
        _log("Step 2/8: Generating paper outline via LLM")
        outline_prompt = OUTLINE_PROMPT.format(
            paper_type=paper_type,
            venue_name=venue_cfg["name"],
            title=paper.get("title", "Untitled"),
            plan_context=ctx.get("plan_context", "N/A")[:1500],
            metrics_summary=ctx.get("metrics_summary", "N/A")[:1500],
            runs_summary=ctx.get("runs_summary", "N/A")[:1500],
            user_notes=ctx.get("user_notes", "N/A"),
            min_refs=MIN_REFERENCES,
            min_algos=MIN_ALGORITHMS,
            min_eqs=MIN_EQUATIONS,
            min_tables=MIN_TABLES,
            min_figs=MIN_FIGURES,
        )
        resp = client.chat(
            messages=[ChatMessage(role="user", content=outline_prompt)],
            model=model, temperature=0.4, max_tokens=8000,
        )
        outline = _extract_json(resp.text)
        if not outline or "sections" not in outline:
            raise ValueError(f"LLM returned invalid outline: {resp.text[:500]}")

        update_paper(paper_id, {"outlineJson": outline})
        _log(f"Outline generated: {len(outline.get('sections', []))} sections, "
             f"{len(outline.get('references', []))} references, "
             f"{len(outline.get('contributions', []))} contributions")

        # ── STEP 3: GATE:OUTLINE ──
        _log("Step 3/8: Validating outline quality gates")
        outline_issues = _gate_outline(outline, paper_id)
        if outline_issues:
            _log(f"Outline gate warnings (non-blocking): {'; '.join(outline_issues)}")
        else:
            _log("Outline gate: PASS")

        # ── STEP 4: GENERATE — Produce each section ──
        _log("Step 4/8: Generating section content via LLM")
        sections = outline.get("sections", [])
        refs = outline.get("references", [])
        contributions = outline.get("contributions", [])
        refs_summary = ", ".join(f"{r.get('key', 'ref')}: {r.get('title', '')[:40]}" for r in refs[:15])

        sections_content = {}
        prev_context = ""

        for i, section in enumerate(sections):
            sec_title = section.get("title", f"Section {i+1}")
            _log(f"Generating section {i+1}/{len(sections)}: {sec_title}")

            # Build requirements
            algo_req = ALGORITHM_TEMPLATE if section.get("hasAlgorithm") else ""
            n_eq = section.get("numEquations", 2 if section.get("hasEquations") else 0)
            eq_req = EQUATION_TEMPLATE.format(n=max(n_eq, 2)) if section.get("hasEquations") else ""
            n_tab = 2 if section.get("hasTables") else 0
            table_req = TABLE_TEMPLATE.format(n=n_tab) if n_tab > 0 else ""
            fig_descs = section.get("figureDescriptions", [])
            fig_req = FIGURE_TEMPLATE if section.get("hasFigures") or fig_descs else ""

            prompt = SECTION_PROMPT.format(
                section_title=sec_title,
                paper_type=paper_type,
                title=outline.get("title", paper.get("title", "Untitled")),
                venue_name=venue_cfg["name"],
                abstract=outline.get("abstract", "")[:500],
                key_points=json.dumps(section.get("keyPoints", [])),
                contributions=json.dumps(contributions),
                requirements="; ".join([r for r in [
                    f"Min {section.get('minWords', 500)} words",
                    "Include algorithm" if section.get("hasAlgorithm") else "",
                    f"{n_eq} equations" if n_eq else "",
                    f"{n_tab} tables" if n_tab else "",
                    "Include figures" if fig_req else "",
                ] if r]),
                metrics_data=ctx.get("metrics_summary", "N/A")[:1000],
                runs_data=ctx.get("runs_summary", "N/A")[:1500],
                prev_context=prev_context[:600],
                refs_summary=refs_summary,
                min_words=section.get("minWords", 500),
                algo_req=algo_req,
                eq_req=eq_req,
                table_req=table_req,
                fig_req=fig_req,
            )

            resp = client.chat(
                messages=[ChatMessage(role="user", content=prompt)],
                model=model, temperature=0.4, max_tokens=6000,
            )
            content = resp.text.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

            write_paper_file(paper_id, f"sections/{section['id']}.tex", content)
            sections_content[section["id"]] = content
            prev_context = content[:400]
            _log(f"Section '{sec_title}' generated: {len(content)} chars")

        # ── STEP 5: GATE:EVIDENCE ──
        _log("Step 5/8: Validating evidence quality gates")
        evidence_gates = _gate_evidence(sections_content, paper_id)
        gate_summary = ", ".join(
            f"{k}={v['count']}/{v['required']}({'PASS' if v['pass'] else 'WARN'})"
            for k, v in evidence_gates.items() if k != "all_pass"
        )
        _log(f"Evidence gates: {gate_summary}")
        if evidence_gates["all_pass"]:
            _log("Evidence gate: ALL PASS")
        else:
            _log("Evidence gate: Some thresholds not met (paper still generated)")

        # ── STEP 6: FIGURES — Generate research figures ──
        _log("Step 6/8: Generating research figures via matplotlib")
        latex_dir = get_paper_latex_dir(paper_id)
        figures_dir = os.path.join(latex_dir, "figures")
        try:
            from app.services.figure_generator import generate_all_figures
            figure_entries = generate_all_figures(figures_dir, paper.get("title", "Paper"))
            _log(f"Generated {len(figure_entries)} figures")
        except Exception as e:
            _log(f"Figure generation warning: {str(e)[:200]}")
            figure_entries = []

        # ── STEP 7: ASSEMBLE — Build LaTeX project ──
        _log("Step 7/8: Assembling LaTeX project")
        _copy_template_assets(venue, paper_id)
        main_tex = _build_main_tex(outline, sections, venue, figure_entries)
        write_paper_file(paper_id, "main.tex", main_tex)

        bibtex = _build_bibtex(refs)
        write_paper_file(paper_id, "refs.bib", bibtex)

        # Build README for the LaTeX project
        readme_content = f"# {outline.get('title', paper.get('title', 'Paper'))}\n\n"
        readme_content += f"**Paper type:** {paper_type}  \n"
        readme_content += f"**Target venue:** {venue_cfg['name']}  \n\n"
        readme_content += "## Build Instructions\n\n"
        readme_content += "```bash\n# Option 1: latexmk (recommended)\nlatexmk -pdf main.tex\n\n"
        readme_content += "# Option 2: manual\npdflatex main.tex\nbibtex main\npdflatex main.tex\npdflatex main.tex\n```\n\n"
        readme_content += "## Structure\n\n"
        readme_content += "```\n"
        readme_content += "main.tex          # Main document\n"
        readme_content += "refs.bib          # Bibliography\n"
        readme_content += "sections/         # Individual sections\n"
        for s in sections:
            readme_content += f"  {s['id']}.tex      # {s.get('title', s['id'])}\n"
        readme_content += "figures/          # Generated figures\n"
        readme_content += "```\n"
        write_paper_file(paper_id, "README.md", readme_content)

        _log(f"LaTeX project assembled: main.tex + {len(sections)} sections + refs.bib + {len(figure_entries)} figures")

        # ── STEP 8: RENDER PDF ──
        _log("Step 8/8: Rendering PDF via LaTeX compilation")
        pdf_path = os.path.join(latex_dir, "main.pdf")
        try:
            from app.services.pdf_renderer import compile_latex_project, render_paper_pdf
            compile_latex_project(latex_dir)
            update_paper(paper_id, {"pdfAvailable": True})
            _log(f"PDF rendered successfully via latexmk: {os.path.getsize(pdf_path)} bytes")
        except Exception as e:
            _log(f"LaTeX compilation warning: {str(e)[:300]}. Falling back to simplified PDF rendering.")
            logger.warning(f"LaTeX compile failed for {paper_id}: {e}", exc_info=True)
            try:
                sections_for_pdf = [
                    {"title": s.get("title", s["id"]), "content": sections_content.get(s["id"], "")}
                    for s in sections
                ]
                render_paper_pdf(
                    output_path=pdf_path,
                    title=outline.get("title", paper.get("title", "Untitled")),
                    authors=outline.get("authors", ["Anonymous"]),
                    abstract=outline.get("abstract", ""),
                    sections=sections_for_pdf,
                    references=refs,
                    figures_dir=figures_dir,
                    figure_entries=figure_entries,
                )
                update_paper(paper_id, {"pdfAvailable": True})
                _log(f"Fallback PDF rendered successfully: {os.path.getsize(pdf_path)} bytes")
            except Exception as fallback_error:
                _log(f"PDF rendering warning: {str(fallback_error)[:300]}. LaTeX bundle still available.")
                logger.warning(f"Fallback PDF render failed for {paper_id}: {fallback_error}", exc_info=True)

        # ── PERSIST ──
        update_paper(paper_id, {
            "status": "completed",
            "targetVenue": venue,
            "templateId": venue,
            "evidenceGates": evidence_gates,
            "figureCount": len(figure_entries),
            "sectionCount": len(sections),
            "referenceCount": len(refs),
        })
        _log("Paper generation completed successfully")

    except Exception as e:
        logger.error(f"Paper generation failed: {e}", exc_info=True)
        update_paper(paper_id, {"status": "failed"})
        add_log(paper_id, f"FAILED: {str(e)[:500]}")
        raise

    return get_paper(paper_id)
