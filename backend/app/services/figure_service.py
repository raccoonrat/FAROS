"""
Figure Generation Service — LLM-driven figure spec + matplotlib rendering.

Supports all mainstream chart types:
line, bar, groupedBar, stackedBar, scatter, bubble,
histogram, boxplot, violin, heatmap, radar, roc, pr

Data sources: experiment metrics OR uploaded datasets.

Pipeline:
1. Fetch data (metrics or uploaded dataset)
2. Ask LLM to propose FigureSpec (or validate user spec)
3. Render with matplotlib (PNG + PDF)
4. Persist artifacts
"""

import io
import json
import logging
from typing import Optional, Dict, Any, List

from app.llm.provider_client import get_provider_client, ChatMessage
from app.storage.experiment_storage import get_metrics, save_figure_artifact

logger = logging.getLogger(__name__)

ALL_FIGURE_TYPES = [
    "line", "bar", "groupedBar", "stackedBar",
    "scatter", "bubble", "histogram", "boxplot", "violin",
    "heatmap", "radar", "roc", "pr",
]

FIGURE_SPEC_PROMPT = """You are a scientific visualization expert. Given the experiment data below, design a paper-ready figure.

**Data:**
{data_json}

**Preferred figure type (optional):** {preferred_type}

**Requirements:**
- Choose the best figure type from: {allowed_types}
- Use ICML/NeurIPS style (clean, professional)
- Provide clear title, axis labels, legend
- Select appropriate data series
- Write a 1-2 sentence caption

**Output (strict JSON):**
```json
{{
  "figureType": "one of the types above",
  "title": "...",
  "xLabel": "...",
  "yLabel": "...",
  "series": [
    {{"name": "Series Name", "x": [1, 2, 3], "y": [0.8, 0.9, 0.95]}}
  ],
  "heatmapData": null,
  "notes": "Any rendering notes",
  "caption": "Figure caption for paper."
}}
```

If figureType is heatmap, use:
"heatmapData": {{"labels": ["A","B"], "matrix": [[1,2],[3,4]]}}

Return ONLY valid JSON.
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


RECOMMEND_PROMPT = """You are a scientific visualization expert. Given the experiment data below, recommend 3-5 paper-ready figures.

**Data:**
{data_json}

**Requirements:**
- Choose from: {allowed_types}
- Rank by usefulness for a research paper
- Each recommendation must have a clear purpose
- Different chart types preferred (don't repeat the same type)

**Output (strict JSON):**
```json
{{
  "recommendations": [
    {{
      "figureType": "one of the types",
      "title": "...",
      "xLabel": "...",
      "yLabel": "...",
      "series": [{{"name": "...", "x": [1,2,3], "y": [0.8,0.9,0.95]}}],
      "heatmapData": null,
      "caption": "...",
      "rationale": "Why this figure is useful",
      "rank": 1
    }}
  ]
}}
```

Return ONLY valid JSON.
"""


def _generate_plot_code(spec: Dict[str, Any]) -> str:
    """Generate the exact matplotlib Python code that reproduces the figure."""
    fig_type = spec.get("figureType", "bar")
    series = spec.get("series", [])
    title = spec.get("title", "")
    x_label = spec.get("xLabel", "")
    y_label = spec.get("yLabel", "")
    heatmap_data = spec.get("heatmapData")

    colors_str = repr(["#2196F3", "#FF5722", "#4CAF50", "#9C27B0", "#FF9800", "#607D8B", "#E91E63", "#00BCD4"])

    lines = [
        '"""Auto-generated figure plotting code."""',
        'import matplotlib',
        'matplotlib.use("Agg")',
        'import matplotlib.pyplot as plt',
        'import numpy as np',
        '',
        '# Paper style',
        'plt.rcParams.update({',
        '    "font.family": "serif", "font.size": 10,',
        '    "axes.labelsize": 11, "axes.titlesize": 12,',
        '    "legend.fontsize": 9, "xtick.labelsize": 9, "ytick.labelsize": 9,',
        '    "figure.figsize": (6, 4), "figure.dpi": 150,',
        '    "axes.grid": True, "grid.alpha": 0.3,',
        '    "axes.spines.top": False, "axes.spines.right": False,',
        '})',
        '',
        f'COLORS = {colors_str}',
        '',
        f'# Data',
        f'series = {json.dumps(series, default=str)}',
    ]

    if fig_type == "radar":
        lines.append('fig, ax = plt.subplots(subplot_kw={"polar": True})')
    else:
        lines.append('fig, ax = plt.subplots()')

    lines.append('')
    lines.append(f'# Chart type: {fig_type}')

    if fig_type in ("bar", "groupedBar"):
        lines += [
            'if series and series[0].get("x"):',
            '    x_labels = [str(v) for v in series[0]["x"]]',
            '    x = np.arange(len(x_labels))',
            '    width = 0.8 / max(len(series), 1)',
            '    for i, s in enumerate(series):',
            '        y = (s.get("y", []) + [0] * len(x))[:len(x)]',
            '        offset = (i - len(series) / 2 + 0.5) * width',
            '        ax.bar(x + offset, y, width, label=s.get("name", f"S{i+1}"), color=COLORS[i % len(COLORS)])',
            '    ax.set_xticks(x)',
            '    ax.set_xticklabels(x_labels, rotation=45 if len(x_labels) > 5 else 0)',
        ]
    elif fig_type == "stackedBar":
        lines += [
            'if series and series[0].get("x"):',
            '    x_labels = [str(v) for v in series[0]["x"]]',
            '    x = np.arange(len(x_labels))',
            '    bottom = np.zeros(len(x))',
            '    for i, s in enumerate(series):',
            '        y = np.array((s.get("y", []) + [0]*len(x))[:len(x)], dtype=float)',
            '        ax.bar(x, y, 0.6, bottom=bottom, label=s.get("name", f"S{i+1}"), color=COLORS[i % len(COLORS)])',
            '        bottom += y',
            '    ax.set_xticks(x)',
            '    ax.set_xticklabels(x_labels)',
        ]
    elif fig_type == "line":
        lines += [
            'for i, s in enumerate(series):',
            '    x = s.get("x", list(range(len(s.get("y", [])))))',
            '    y = s.get("y", [])',
            '    ax.plot(x[:len(y)], y, marker="o", markersize=4, label=s.get("name", f"S{i+1}"), color=COLORS[i % len(COLORS)], linewidth=1.5)',
        ]
    elif fig_type == "scatter":
        lines += [
            'for i, s in enumerate(series):',
            '    x, y = s.get("x", []), s.get("y", [])',
            '    n = min(len(x), len(y))',
            '    ax.scatter(x[:n], y[:n], label=s.get("name", f"S{i+1}"), color=COLORS[i % len(COLORS)], s=40, alpha=0.7)',
        ]
    elif fig_type == "bubble":
        lines += [
            'for i, s in enumerate(series):',
            '    x, y = s.get("x", []), s.get("y", [])',
            '    sizes = s.get("sizes", [40]*len(x))',
            '    n = min(len(x), len(y), len(sizes))',
            '    ax.scatter(x[:n], y[:n], s=sizes[:n], label=s.get("name", f"S{i+1}"), color=COLORS[i % len(COLORS)], alpha=0.6, edgecolors="white")',
        ]
    elif fig_type in ("histogram", "hist"):
        lines += [
            'for i, s in enumerate(series):',
            '    data = s.get("y", s.get("x", []))',
            '    if data:',
            '        ax.hist(data, bins=min(30, max(5, len(data)//3)), alpha=0.7, label=s.get("name", f"S{i+1}"), color=COLORS[i % len(COLORS)], edgecolor="white")',
        ]
    elif fig_type in ("boxplot", "box"):
        lines += [
            'box_data = [s.get("y", []) for s in series if s.get("y")]',
            'box_labels = [s.get("name", f"S{i+1}") for i, s in enumerate(series) if s.get("y")]',
            'if box_data:',
            '    bp = ax.boxplot(box_data, labels=box_labels, patch_artist=True)',
            '    for i, patch in enumerate(bp["boxes"]):',
            '        patch.set_facecolor(COLORS[i % len(COLORS)])',
            '        patch.set_alpha(0.7)',
        ]
    elif fig_type == "violin":
        lines += [
            'viol_data = [s.get("y", []) for s in series if s.get("y")]',
            'viol_labels = [s.get("name", f"S{i+1}") for i, s in enumerate(series) if s.get("y")]',
            'if viol_data:',
            '    vp = ax.violinplot(viol_data, showmeans=True, showmedians=True)',
            '    for i, body in enumerate(vp.get("bodies", [])):',
            '        body.set_facecolor(COLORS[i % len(COLORS)])',
            '        body.set_alpha(0.7)',
            '    ax.set_xticks(range(1, len(viol_labels)+1))',
            '    ax.set_xticklabels(viol_labels)',
        ]
    elif fig_type == "heatmap":
        lines += [
            f'heatmap_data = {json.dumps(heatmap_data or {}, default=str)}',
            'matrix = heatmap_data.get("matrix", [])',
            'labels = heatmap_data.get("labels", [])',
            'if matrix:',
            '    data = np.array(matrix, dtype=float)',
            '    im = ax.imshow(data, cmap="YlOrRd", aspect="auto")',
            '    fig.colorbar(im, ax=ax)',
            '    if labels:',
            '        ax.set_xticks(range(len(labels)))',
            '        ax.set_xticklabels(labels, rotation=45, ha="right")',
            '        ax.set_yticks(range(len(labels)))',
            '        ax.set_yticklabels(labels)',
        ]
    elif fig_type == "radar":
        lines += [
            'if series:',
            '    categories = [str(v) for v in series[0].get("x", [])]',
            '    n_cats = len(categories)',
            '    if n_cats >= 3:',
            '        angles = np.linspace(0, 2*np.pi, n_cats, endpoint=False).tolist()',
            '        angles += angles[:1]',
            '        for i, s in enumerate(series):',
            '            vals = s.get("y", [])[:n_cats]',
            '            vals += vals[:1]',
            '            ax.plot(angles, vals, linewidth=1.5, label=s.get("name", f"S{i+1}"), color=COLORS[i % len(COLORS)])',
            '            ax.fill(angles, vals, alpha=0.1, color=COLORS[i % len(COLORS)])',
            '        ax.set_xticks(angles[:-1])',
            '        ax.set_xticklabels(categories)',
        ]
    elif fig_type == "roc":
        lines += [
            'for i, s in enumerate(series):',
            '    fpr, tpr = s.get("x", []), s.get("y", [])',
            '    n = min(len(fpr), len(tpr))',
            '    auc_val = s.get("auc", "?")',
            '    ax.plot(fpr[:n], tpr[:n], linewidth=1.5, label=f\'{s.get("name", f"S{i+1}")} (AUC={auc_val})\', color=COLORS[i % len(COLORS)])',
            'ax.plot([0,1],[0,1],"k--",alpha=0.3,linewidth=1)',
            'ax.set_xlim([0,1])',
            'ax.set_ylim([0,1.05])',
        ]
    elif fig_type == "pr":
        lines += [
            'for i, s in enumerate(series):',
            '    recall, precision = s.get("x", []), s.get("y", [])',
            '    n = min(len(recall), len(precision))',
            '    ax.plot(recall[:n], precision[:n], linewidth=1.5, label=s.get("name", f"S{i+1}"), color=COLORS[i % len(COLORS)])',
            'ax.set_xlim([0,1])',
            'ax.set_ylim([0,1.05])',
        ]

    # Common formatting
    lines += [
        '',
        '# Formatting',
        f'ax.set_title({repr(title)}, pad=15)',
        f'ax.set_xlabel({repr(x_label)})',
        f'ax.set_ylabel({repr(y_label)})',
    ]
    if len(series) > 1:
        lines.append('ax.legend(frameon=True, framealpha=0.8)')
    lines += [
        'plt.tight_layout()',
        '',
        '# Save',
        'fig.savefig("figure.png", bbox_inches="tight", dpi=300)',
        'fig.savefig("figure.pdf", bbox_inches="tight")',
        'plt.close(fig)',
        'print("Figure saved to figure.png and figure.pdf")',
    ]

    return "\n".join(lines)


def _apply_paper_style():
    """Apply ICML/NeurIPS-like style to matplotlib, meeting academic publication standards."""
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif", "Bitstream Vera Serif"],
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "legend.fontsize": 9,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "figure.figsize": (6, 4),
        "figure.dpi": 150,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })


COLORS = ["#2196F3", "#FF5722", "#4CAF50", "#9C27B0", "#FF9800", "#607D8B", "#E91E63", "#00BCD4"]


def _render_figure(spec: Dict[str, Any]) -> tuple:
    """Render a figure from spec using matplotlib. Returns (png_bytes, pdf_bytes)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    _apply_paper_style()

    fig_type = spec.get("figureType", "bar")
    series = spec.get("series", [])

    # Special layout for some types
    if fig_type == "radar":
        fig, ax = plt.subplots(subplot_kw={"polar": True})
    else:
        fig, ax = plt.subplots()

    # ── bar / groupedBar ──
    if fig_type in ("bar", "groupedBar"):
        n_series = len(series)
        if n_series > 0 and series[0].get("x"):
            x_labels = [str(v) for v in series[0]["x"]]
            x = np.arange(len(x_labels))
            width = 0.8 / max(n_series, 1)
            for i, s in enumerate(series):
                y = s.get("y", [])
                y = (y + [0] * len(x))[:len(x)]
                offset = (i - n_series / 2 + 0.5) * width
                ax.bar(x + offset, y, width, label=s.get("name", f"S{i+1}"), color=COLORS[i % len(COLORS)])
            ax.set_xticks(x)
            ax.set_xticklabels(x_labels, rotation=45 if len(x_labels) > 5 else 0, ha="right" if len(x_labels) > 5 else "center")

    # ── stackedBar ──
    elif fig_type == "stackedBar":
        if series and series[0].get("x"):
            x_labels = [str(v) for v in series[0]["x"]]
            x = np.arange(len(x_labels))
            bottom = np.zeros(len(x))
            for i, s in enumerate(series):
                y = np.array((s.get("y", []) + [0] * len(x))[:len(x)], dtype=float)
                ax.bar(x, y, 0.6, bottom=bottom, label=s.get("name", f"S{i+1}"), color=COLORS[i % len(COLORS)])
                bottom += y
            ax.set_xticks(x)
            ax.set_xticklabels(x_labels, rotation=45 if len(x_labels) > 5 else 0, ha="right" if len(x_labels) > 5 else "center")

    # ── line ──
    elif fig_type == "line":
        for i, s in enumerate(series):
            x = s.get("x", list(range(len(s.get("y", [])))))
            y = s.get("y", [])
            ax.plot(x[:len(y)], y, marker="o", markersize=4, label=s.get("name", f"S{i+1}"), color=COLORS[i % len(COLORS)], linewidth=1.5)

    # ── scatter ──
    elif fig_type == "scatter":
        for i, s in enumerate(series):
            x, y = s.get("x", []), s.get("y", [])
            n = min(len(x), len(y))
            ax.scatter(x[:n], y[:n], label=s.get("name", f"S{i+1}"), color=COLORS[i % len(COLORS)], s=40, alpha=0.7)

    # ── bubble ──
    elif fig_type == "bubble":
        for i, s in enumerate(series):
            x, y = s.get("x", []), s.get("y", [])
            sizes = s.get("sizes", [40] * len(x))
            n = min(len(x), len(y), len(sizes))
            ax.scatter(x[:n], y[:n], s=sizes[:n], label=s.get("name", f"S{i+1}"), color=COLORS[i % len(COLORS)], alpha=0.6, edgecolors="white")

    # ── histogram ──
    elif fig_type in ("histogram", "hist"):
        for i, s in enumerate(series):
            data = s.get("y", s.get("x", []))
            if data:
                ax.hist(data, bins=min(30, max(5, len(data) // 3)), alpha=0.7, label=s.get("name", f"S{i+1}"), color=COLORS[i % len(COLORS)], edgecolor="white")

    # ── boxplot ──
    elif fig_type in ("boxplot", "box"):
        box_data = [s.get("y", []) for s in series if s.get("y")]
        box_labels = [s.get("name", f"S{i+1}") for i, s in enumerate(series) if s.get("y")]
        if box_data:
            bp = ax.boxplot(box_data, labels=box_labels, patch_artist=True)
            for i, patch in enumerate(bp["boxes"]):
                patch.set_facecolor(COLORS[i % len(COLORS)])
                patch.set_alpha(0.7)

    # ── violin ──
    elif fig_type == "violin":
        viol_data = [s.get("y", []) for s in series if s.get("y")]
        viol_labels = [s.get("name", f"S{i+1}") for i, s in enumerate(series) if s.get("y")]
        if viol_data:
            vp = ax.violinplot(viol_data, showmeans=True, showmedians=True)
            for i, body in enumerate(vp.get("bodies", [])):
                body.set_facecolor(COLORS[i % len(COLORS)])
                body.set_alpha(0.7)
            ax.set_xticks(range(1, len(viol_labels) + 1))
            ax.set_xticklabels(viol_labels)

    # ── heatmap ──
    elif fig_type == "heatmap":
        hm = spec.get("heatmapData", {})
        matrix = hm.get("matrix", [])
        labels = hm.get("labels", [])
        if matrix:
            data = np.array(matrix, dtype=float)
            im = ax.imshow(data, cmap="YlOrRd", aspect="auto")
            fig.colorbar(im, ax=ax)
            if labels:
                ax.set_xticks(range(len(labels)))
                ax.set_xticklabels(labels, rotation=45, ha="right")
                ax.set_yticks(range(len(labels)))
                ax.set_yticklabels(labels)

    # ── radar ──
    elif fig_type == "radar":
        if series:
            categories = [str(v) for v in series[0].get("x", [])]
            n_cats = len(categories)
            if n_cats >= 3:
                angles = np.linspace(0, 2 * np.pi, n_cats, endpoint=False).tolist()
                angles += angles[:1]
                for i, s in enumerate(series):
                    vals = s.get("y", [])[:n_cats]
                    vals += vals[:1]
                    ax.plot(angles, vals, linewidth=1.5, label=s.get("name", f"S{i+1}"), color=COLORS[i % len(COLORS)])
                    ax.fill(angles, vals, alpha=0.1, color=COLORS[i % len(COLORS)])
                ax.set_xticks(angles[:-1])
                ax.set_xticklabels(categories)

    # ── ROC curve ──
    elif fig_type == "roc":
        for i, s in enumerate(series):
            fpr, tpr = s.get("x", []), s.get("y", [])
            n = min(len(fpr), len(tpr))
            auc_val = s.get("auc", "?")
            ax.plot(fpr[:n], tpr[:n], linewidth=1.5, label=f"{s.get('name', f'S{i+1}')} (AUC={auc_val})", color=COLORS[i % len(COLORS)])
        ax.plot([0, 1], [0, 1], "k--", alpha=0.3, linewidth=1)
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1.05])

    # ── PR curve ──
    elif fig_type == "pr":
        for i, s in enumerate(series):
            recall, precision = s.get("x", []), s.get("y", [])
            n = min(len(recall), len(precision))
            ax.plot(recall[:n], precision[:n], linewidth=1.5, label=s.get("name", f"S{i+1}"), color=COLORS[i % len(COLORS)])
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1.05])

    # Common formatting
    if fig_type != "radar":
        ax.set_title(spec.get("title", ""), pad=15)
        ax.set_xlabel(spec.get("xLabel", ""))
        ax.set_ylabel(spec.get("yLabel", ""))
    else:
        ax.set_title(spec.get("title", ""), pad=20)

    if series and len(series) > 1 and fig_type not in ("boxplot", "box", "violin", "heatmap"):
        ax.legend(frameon=True, framealpha=0.8)

    plt.tight_layout()

    png_buf = io.BytesIO()
    fig.savefig(
        png_buf,
        format="png",
        bbox_inches="tight",
        dpi=300,
        pad_inches=0.05
    )
    png_bytes = png_buf.getvalue()

    pdf_buf = io.BytesIO()
    fig.savefig(
        pdf_buf,
        format="pdf",
        bbox_inches="tight",
        pad_inches=0.05
    )
    pdf_bytes = pdf_buf.getvalue()

    plt.close(fig)
    return png_bytes, pdf_bytes


def generate_figure(
    experiment_id: str,
    provider_name: str = "moonshot",
    model: str = "moonshot-v1-8k",
    preferred_figure_type: Optional[str] = None,
    user_spec: Optional[Dict] = None,
    data_override: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Full pipeline: fetch data → LLM FigureSpec → render → persist.
    
    Args:
        data_override: If provided, use this data instead of metrics (for uploaded datasets)
        user_spec: If provided, skip LLM and render directly from this spec
    
    Returns the FigureArtifact dict.
    """
    # 1. Fetch data
    if data_override is not None:
        data = data_override
    else:
        data = get_metrics(experiment_id)
    if not data:
        raise ValueError(f"No data found for experiment {experiment_id}. Ingest metrics or upload data first.")

    if user_spec and user_spec.get("figureType"):
        spec = user_spec
    else:
        # 2. Ask LLM for FigureSpec
        client = get_provider_client(provider_name)
        data_json = json.dumps(data[:50], indent=2, default=str)
        prompt = FIGURE_SPEC_PROMPT.format(
            data_json=data_json,
            preferred_type=preferred_figure_type or "auto-detect best type",
            allowed_types=", ".join(ALL_FIGURE_TYPES),
        )

        resp = client.chat(
            messages=[ChatMessage(role="user", content=prompt)],
            model=model, temperature=0.3, max_tokens=2000,
        )

        spec = _extract_json(resp.text)
        if not spec or "figureType" not in spec:
            raise ValueError(f"LLM returned invalid FigureSpec: {resp.text[:300]}")

    # 3. Render
    try:
        png_bytes, pdf_bytes = _render_figure(spec)
    except Exception as e:
        logger.error(f"Figure rendering failed: {e}", exc_info=True)
        raise ValueError(f"Figure rendering failed: {e}")

    # 4. Generate plotting code
    plot_code = _generate_plot_code(spec)

    # 5. Persist
    caption = spec.get("caption", "")
    artifact = save_figure_artifact(
        exp_id=experiment_id,
        figure_type=spec["figureType"],
        spec=spec,
        png_bytes=png_bytes,
        pdf_bytes=pdf_bytes,
        caption=caption,
        prompt_used="user_spec" if user_spec else "llm_generated",
        model_used=model,
        plot_code=plot_code,
    )

    return artifact


def recommend_figures(
    experiment_id: str,
    provider_name: str = "moonshot",
    model: str = "moonshot-v1-8k",
    data_override: Optional[List[Dict]] = None,
) -> List[Dict[str, Any]]:
    """
    LLM-driven figure recommendation. Returns list of FigureSpec recommendations.
    """
    from app.storage.experiment_storage import get_metrics
    if data_override is not None:
        data = data_override
    else:
        data = get_metrics(experiment_id)
    if not data:
        raise ValueError(f"No data for experiment {experiment_id}")

    client = get_provider_client(provider_name)
    data_json = json.dumps(data[:50], indent=2, default=str)
    prompt = RECOMMEND_PROMPT.format(
        data_json=data_json,
        allowed_types=", ".join(ALL_FIGURE_TYPES),
    )
    resp = client.chat(
        messages=[ChatMessage(role="user", content=prompt)],
        model=model, temperature=0.4, max_tokens=4000,
    )
    parsed = _extract_json(resp.text)
    if not parsed or "recommendations" not in parsed:
        raise ValueError(f"LLM returned invalid recommendations: {resp.text[:300]}")
    return parsed["recommendations"]
