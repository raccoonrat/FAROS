"""
Review Service — LLM-driven paper review generation.

Pipeline:
1. Load paper content (main.tex + sections)
2. LLM generates structured review
3. Parse into actionable items
4. Persist review
"""

import json
import logging
from typing import Optional, Dict, Any, List

from app.core.settings import get_settings
from app.llm.provider_client import get_provider_client, ChatMessage
from app.modules.review.storage import get_paper, read_paper_file, list_paper_files
from app.modules.review.storage import get_review, update_review

logger = logging.getLogger(__name__)

REVIEW_PROMPT = """You are a senior ML conference reviewer (ACL/NeurIPS/ICML caliber).
Review the following paper submission rigorously.

**Paper Title:** {title}
**Paper Type:** {paper_type}

**LaTeX Content:**
{latex_content}

**Your review MUST include ALL of the following:**

1. **Overall Assessment** (2-3 sentences)
2. **Score Suggestion** (1-10 scale, 6+ = accept)
3. **Strengths** (at least 3 specific points)
4. **Weaknesses** (at least 3 specific points)
5. **Questions for Authors** (at least 3)
6. **Missing Experiments** (at least 2 suggestions)
7. **Writing Issues** (grammar, clarity, structure — at least 2)
8. **Action Items** — EXACTLY 12 concrete, actionable items, each with:
   - description: what needs to be done
   - section: which section of the paper this applies to (e.g. "Method", "Experiments", "Introduction")
   - severity: one of BLOCKER, MAJOR, MINOR
   - targetModule: one of "papers" (rewrite section), "experiments" (new figure/table), "code" (code improvement)
   - suggestedEdit: brief description of the fix

**Return strict JSON:**
```json
{{
  "overallAssessment": "...",
  "scoreSuggestion": 5,
  "strengths": ["...", "...", "..."],
  "weaknesses": ["...", "...", "..."],
  "questions": ["...", "...", "..."],
  "missingExperiments": ["...", "..."],
  "writingIssues": ["...", "..."],
  "actionItems": [
    {{
      "description": "...",
      "section": "Method",
      "severity": "MAJOR",
      "targetModule": "papers",
      "suggestedEdit": "..."
    }}
  ]
}}
```

Be thorough, critical but constructive. Return ONLY valid JSON.
"""


def _extract_json(text: str) -> Optional[Dict]:
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


def _collect_paper_content(paper_id: str) -> str:
    """Collect all LaTeX content from a paper."""
    files = list_paper_files(paper_id)
    tex_files = [f for f in files if not f["isDir"] and (f["name"].endswith(".tex") or f["name"].endswith(".bib"))]

    content_parts = []
    # main.tex first
    main = read_paper_file(paper_id, "main.tex")
    if main:
        content_parts.append(f"=== main.tex ===\n{main}")

    for f in tex_files:
        if f["path"] == "main.tex":
            continue
        c = read_paper_file(paper_id, f["path"])
        if c:
            content_parts.append(f"=== {f['path']} ===\n{c}")

    return "\n\n".join(content_parts)[:8000]


def generate_review(review_id: str) -> Dict[str, Any]:
    """
    Full pipeline: load paper → LLM review → parse → persist.
    Returns updated review record.
    """
    review = get_review(review_id)
    if not review:
        raise ValueError(f"Review not found: {review_id}")

    paper_id = review.get("paperId")
    paper = get_paper(paper_id)
    if not paper:
        raise ValueError(f"Paper not found: {paper_id}")

    settings = get_settings()
    provider_name = review.get("providerName") or settings.get_active_provider()
    model = review.get("model") or settings.get_active_model(provider_name)

    update_review(review_id, {"status": "generating"})

    try:
        client = get_provider_client(provider_name)

        # Collect paper content
        latex_content = _collect_paper_content(paper_id)
        if not latex_content:
            raise ValueError("Paper has no LaTeX content. Generate the paper first.")

        prompt = REVIEW_PROMPT.format(
            title=paper.get("title", "Untitled"),
            paper_type=paper.get("paperType", "algorithm"),
            latex_content=latex_content,
        )

        resp = client.chat(
            messages=[ChatMessage(role="user", content=prompt)],
            model=model, temperature=0.4, max_tokens=6000,
        )

        report = _extract_json(resp.text)
        if not report or "actionItems" not in report:
            raise ValueError(f"LLM returned invalid review: {resp.text[:300]}")

        # Build markdown report
        md_parts = [
            f"# Paper Review: {paper.get('title', 'Untitled')}",
            f"\n## Overall Assessment\n{report.get('overallAssessment', 'N/A')}",
            f"\n**Score Suggestion:** {report.get('scoreSuggestion', 'N/A')}/10",
            "\n## Strengths",
        ]
        for s in report.get("strengths", []):
            md_parts.append(f"- {s}")
        md_parts.append("\n## Weaknesses")
        for w in report.get("weaknesses", []):
            md_parts.append(f"- {w}")
        md_parts.append("\n## Questions for Authors")
        for q in report.get("questions", []):
            md_parts.append(f"- {q}")
        md_parts.append("\n## Missing Experiments")
        for m in report.get("missingExperiments", []):
            md_parts.append(f"- {m}")
        md_parts.append("\n## Writing Issues")
        for w in report.get("writingIssues", []):
            md_parts.append(f"- {w}")
        md_parts.append("\n## Action Items")
        for i, item in enumerate(report.get("actionItems", []), 1):
            md_parts.append(f"\n### {i}. [{item.get('severity', 'MAJOR')}] {item.get('description', '')}")
            md_parts.append(f"- **Section:** {item.get('section', 'N/A')}")
            md_parts.append(f"- **Target:** {item.get('targetModule', 'papers')}")
            md_parts.append(f"- **Suggested Edit:** {item.get('suggestedEdit', 'N/A')}")

        markdown_report = "\n".join(md_parts)

        update_review(review_id, {
            "status": "completed",
            "scoreSuggestion": report.get("scoreSuggestion"),
            "jsonReport": report,
            "markdownReport": markdown_report,
            "actionItems": report.get("actionItems", []),
        })

    except Exception as e:
        logger.error(f"Review generation failed: {e}", exc_info=True)
        update_review(review_id, {"status": "failed", "markdownReport": f"Generation failed: {str(e)[:500]}"})
        raise

    return get_review(review_id)
