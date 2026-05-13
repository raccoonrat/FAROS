"""
Prompt Templates for Idea Generation Pipeline

Each step in the pipeline has a dedicated prompt template.
Templates use Python string formatting with named placeholders.
"""

# Step 1: Query Expansion
EXPAND_QUERY_SYSTEM = """You are a research assistant specializing in expanding research queries.
Your task is to take a seed research topic and expand it into a comprehensive search strategy."""

EXPAND_QUERY_USER = """Given the following research topic, expand it into:
1. A refined research question
2. 3-5 related search queries for literature search
3. Key concepts and terms to look for
4. Related research areas to explore

Research Topic: {seed_query}
Paper Type: {paper_type}
Domain: {domain}

Respond in JSON format:
{{
  "refinedQuestion": "...",
  "searchQueries": ["query1", "query2", ...],
  "keyConcepts": ["concept1", "concept2", ...],
  "relatedAreas": ["area1", "area2", ...]
}}"""

# Step 2: Literature Search (used for relevance scoring)
SCORE_PAPER_SYSTEM = """You are a research assistant evaluating paper relevance.
Score how relevant a paper is to a given research query."""

SCORE_PAPER_USER = """Research Query: {query}

Paper Title: {title}
Abstract: {abstract}
Year: {year}

Rate the relevance of this paper to the research query on a scale of 0.0 to 1.0.
Consider:
- Direct relevance to the topic
- Recency and impact
- Methodological relevance

Respond with only a JSON object:
{{"relevance": 0.X, "reason": "brief explanation"}}"""

# Step 3: Novelty Check
NOVELTY_CHECK_SYSTEM = """You are a research novelty evaluator.
Your task is to assess the novelty of potential research directions given existing literature."""

NOVELTY_CHECK_USER = """Research Topic: {seed_query}
Paper Type: {paper_type}

Existing Literature Summary:
{literature_summary}

Based on the existing literature, identify:
1. What has already been done (covered areas)
2. What gaps exist (uncovered areas)
3. Potential novel directions

Respond in JSON format:
{{
  "coveredAreas": ["area1", "area2", ...],
  "gaps": ["gap1", "gap2", ...],
  "novelDirections": ["direction1", "direction2", ...],
  "noveltyAssessment": "overall assessment of novelty potential"
}}"""

# Step 4: Gap Analysis
GAP_ANALYSIS_SYSTEM = """You are a research gap analyst.
Your task is to deeply analyze research gaps and identify promising research opportunities."""

GAP_ANALYSIS_USER = """Research Topic: {seed_query}
Paper Type: {paper_type}

Literature Review:
{literature_summary}

Novelty Assessment:
{novelty_assessment}

Identified Gaps:
{gaps}

For each gap, provide:
1. A detailed description of the gap
2. Why this gap exists (technical challenges, lack of data, etc.)
3. Potential approaches to address it
4. Expected impact if addressed
5. Feasibility assessment

Respond in JSON format:
{{
  "gapAnalysis": [
    {{
      "gap": "description",
      "reason": "why it exists",
      "approaches": ["approach1", "approach2"],
      "expectedImpact": "impact description",
      "feasibility": "high/medium/low"
    }}
  ],
  "prioritizedGaps": ["gap1", "gap2", ...],
  "researchOpportunities": ["opportunity1", "opportunity2", ...]
}}"""

# Step 5: Idea Brainstorm
IDEA_BRAINSTORM_SYSTEM = """You are a creative research idea generator.
Your task is to generate novel, feasible, and impactful research ideas based on identified gaps and opportunities."""

IDEA_BRAINSTORM_USER = """Research Topic: {seed_query}
Paper Type: {paper_type}
Maximum Ideas: {max_candidates}

Gap Analysis:
{gap_analysis}

Research Opportunities:
{opportunities}

Key Literature:
{key_papers}

Generate {max_candidates} distinct research ideas. For each idea, provide:
1. A concise title
2. Problem statement (what problem does this solve?)
3. Key insight (what is the novel contribution?)
4. Proposed approach (high-level methodology)
5. Expected outcomes
6. Required experiments
7. Potential risks and mitigations

Respond in JSON format:
{{
  "ideas": [
    {{
      "title": "...",
      "problem": "...",
      "keyInsight": "...",
      "approach": "...",
      "expectedOutcomes": ["outcome1", "outcome2"],
      "requiredExperiments": [
        {{"name": "...", "description": "...", "metrics": ["metric1"], "datasets": ["dataset1"]}}
      ],
      "risks": [
        {{"risk": "...", "mitigation": "..."}}
      ]
    }}
  ]
}}"""

# Step 6: Rank Candidates (Pairwise Comparison)
RANK_PAIRWISE_SYSTEM = """You are a research idea evaluator.
Your task is to compare two research ideas and determine which is better."""

RANK_PAIRWISE_USER = """Compare these two research ideas and determine which is better overall.

Idea A:
Title: {idea_a_title}
Problem: {idea_a_problem}
Key Insight: {idea_a_insight}

Idea B:
Title: {idea_b_title}
Problem: {idea_b_problem}
Key Insight: {idea_b_insight}

Evaluation Criteria:
1. Novelty: How new and original is the idea?
2. Feasibility: How practical is it to implement?
3. Impact: What is the potential scientific/practical impact?
4. Clarity: How well-defined is the problem and solution?

Which idea is better? Respond in JSON format:
{{
  "winner": "A" or "B",
  "noveltyComparison": "...",
  "feasibilityComparison": "...",
  "impactComparison": "...",
  "overallReasoning": "..."
}}"""

# Step 6: Rank Candidates (Individual Scoring)
RANK_SCORE_SYSTEM = """You are a research idea evaluator.
Your task is to score a research idea on multiple dimensions."""

RANK_SCORE_USER = """Evaluate this research idea on a scale of 0-10 for each criterion.

Title: {title}
Problem: {problem}
Key Insight: {key_insight}
Approach: {approach}

Paper Type: {paper_type}
Research Domain: {domain}

Score the idea on:
1. Novelty (0-10): How new and original is this idea?
2. Feasibility (0-10): How practical is it to implement within reasonable resources?
3. Impact (0-10): What is the potential scientific and practical impact?

Provide detailed rationale for each score.

Respond in JSON format:
{{
  "novelty": X,
  "noveltyRationale": "...",
  "feasibility": X,
  "feasibilityRationale": "...",
  "impact": X,
  "impactRationale": "..."
}}"""

# Utility: Summarize Literature
SUMMARIZE_LITERATURE_SYSTEM = """You are a research literature summarizer.
Your task is to create a concise summary of research papers."""

SUMMARIZE_LITERATURE_USER = """Summarize the following papers for a literature review on: {topic}

Papers:
{papers_text}

Provide:
1. A brief summary of each paper's main contribution
2. Common themes across papers
3. Key methodologies used
4. Open questions and limitations

Respond in JSON format:
{{
  "paperSummaries": [
    {{"title": "...", "contribution": "...", "methodology": "..."}}
  ],
  "commonThemes": ["theme1", "theme2"],
  "keyMethodologies": ["method1", "method2"],
  "openQuestions": ["question1", "question2"]
}}"""
