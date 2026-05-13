// ============================================================================
// Category Taxonomy - Single Source of Truth
// ============================================================================

export type CategoryGroup = 'post-training' | 'inference'

export interface Direction {
  id: string
  title: string
  shortDesc: string
  longDesc: string
  tags: string[]
  exampleTasks: string[]
  recommendedTemplates: string[]
  riskNotes?: string
  group: CategoryGroup
  subgroup: string
}

// ============================================================================
// Post-Training Directions
// ============================================================================

const postTrainingDirections: Direction[] = [
  {
    id: 'sft_instruction_tuning',
    title: 'SFT & Instruction Tuning',
    shortDesc: 'Fine-tune models on instruction-response pairs for task-specific behavior',
    longDesc: 'Supervised Fine-Tuning (SFT) adapts pre-trained models to follow instructions by training on curated datasets of prompts and desired responses. This is the foundation for building instruction-following models and task-specific assistants.',
    tags: ['sft', 'instruction', 'fine-tuning', 'supervised'],
    exampleTasks: [
      'Train a model to answer domain-specific questions',
      'Adapt a base model for code generation tasks',
      'Fine-tune for multi-turn conversation abilities',
      'Create a specialized assistant for technical documentation'
    ],
    recommendedTemplates: ['sft_basic', 'sft_lora'],
    group: 'post-training',
    subgroup: 'alignment_and_post_train'
  },
  {
    id: 'preference_optimization_dpo_ipo',
    title: 'Preference Optimization (DPO/IPO)',
    shortDesc: 'Align models with human preferences using direct optimization methods',
    longDesc: 'Direct Preference Optimization (DPO) and Iterative Preference Optimization (IPO) train models to prefer certain outputs over others without requiring a separate reward model. These methods are more stable and efficient than traditional RLHF for alignment.',
    tags: ['dpo', 'ipo', 'preference', 'alignment', 'rlhf-alternative'],
    exampleTasks: [
      'Align model outputs with human quality judgments',
      'Reduce harmful or biased responses',
      'Improve response helpfulness and coherence',
      'Fine-tune based on comparative feedback'
    ],
    recommendedTemplates: ['dpo_standard', 'ipo_iterative'],
    riskNotes: 'Requires high-quality preference data; may overfit to specific preference patterns',
    group: 'post-training',
    subgroup: 'alignment_and_post_train'
  },
  {
    id: 'rlhf_rlaif',
    title: 'RLHF & RLAIF',
    shortDesc: 'Reinforcement learning from human or AI feedback for alignment',
    longDesc: 'Reinforcement Learning from Human Feedback (RLHF) and from AI Feedback (RLAIF) use reward models to guide policy optimization. RLHF uses human preferences while RLAIF leverages AI systems for scalable feedback generation.',
    tags: ['rlhf', 'rlaif', 'reinforcement', 'reward-model', 'ppo'],
    exampleTasks: [
      'Train models to maximize helpfulness and safety',
      'Iteratively improve response quality with feedback',
      'Scale alignment with AI-generated preferences',
      'Optimize for complex multi-objective rewards'
    ],
    recommendedTemplates: ['rlhf_ppo', 'rlaif_constitutional'],
    riskNotes: 'Complex training dynamics; reward hacking risks; requires careful hyperparameter tuning',
    group: 'post-training',
    subgroup: 'alignment_and_post_train'
  },
  {
    id: 'tool_use_function_calling',
    title: 'Tool Use & Function Calling',
    shortDesc: 'Train models to interact with external tools and APIs',
    longDesc: 'Function calling training enables models to understand when and how to invoke external tools, APIs, or code interpreters. This extends model capabilities beyond pure text generation to include structured actions and real-world interactions.',
    tags: ['tools', 'function-calling', 'api', 'agents', 'actions'],
    exampleTasks: [
      'Train models to call weather APIs when asked about weather',
      'Enable calculator usage for mathematical queries',
      'Teach database query generation and execution',
      'Build agents that can browse the web and use search'
    ],
    recommendedTemplates: ['tool_basic', 'tool_multi_step'],
    group: 'post-training',
    subgroup: 'alignment_and_post_train'
  },
  {
    id: 'reasoning_post_train_reflection',
    title: 'Reasoning & Reflection',
    shortDesc: 'Post-training for improved reasoning, planning, and self-correction',
    longDesc: 'Specialized training to enhance model reasoning capabilities through techniques like chain-of-thought distillation, reflection, and self-critique. Models learn to break down problems, verify their work, and correct mistakes.',
    tags: ['reasoning', 'reflection', 'cot', 'planning', 'self-correction'],
    exampleTasks: [
      'Train models to show step-by-step mathematical reasoning',
      'Enable self-verification and error correction',
      'Improve multi-step planning and problem decomposition',
      'Distill reasoning patterns from stronger models'
    ],
    recommendedTemplates: ['reasoning_cot', 'reflection_self_critique'],
    group: 'post-training',
    subgroup: 'alignment_and_post_train'
  }
]

// ============================================================================
// Inference-Time Directions
// ============================================================================

const inferenceDirections: Direction[] = [
  {
    id: 'prompting_cot_scaffold',
    title: 'Prompting & CoT Scaffolding',
    shortDesc: 'Structured prompting techniques to elicit better reasoning',
    longDesc: 'Chain-of-Thought (CoT) prompting and scaffolding techniques guide models to produce intermediate reasoning steps. This includes few-shot examples, structured templates, and decomposition strategies that improve output quality without model changes.',
    tags: ['prompting', 'cot', 'few-shot', 'scaffolding', 'zero-shot'],
    exampleTasks: [
      'Design optimal prompt templates for complex tasks',
      'Implement few-shot learning with strategic examples',
      'Create chain-of-thought prompts for math problems',
      'Build prompt libraries for consistent outputs'
    ],
    recommendedTemplates: ['prompt_cot', 'prompt_few_shot'],
    group: 'inference',
    subgroup: 'inference_time_strategies'
  },
  {
    id: 'self_consistency_rerank',
    title: 'Self-Consistency & Reranking',
    shortDesc: 'Generate multiple outputs and select the best via voting or reranking',
    longDesc: 'Self-consistency samples multiple reasoning paths and selects the most common answer. Reranking uses a separate model or heuristic to score and select the best output from multiple candidates, improving reliability.',
    tags: ['self-consistency', 'reranking', 'voting', 'sampling', 'best-of-n'],
    exampleTasks: [
      'Sample 10 solutions and pick the most common answer',
      'Use a reward model to rerank candidate outputs',
      'Implement majority voting for classification',
      'Score outputs by confidence or verifiability'
    ],
    recommendedTemplates: ['self_consistency', 'rerank_reward'],
    group: 'inference',
    subgroup: 'inference_time_strategies'
  },
  {
    id: 'retrieval_rag_grounding',
    title: 'Retrieval & RAG Grounding',
    shortDesc: 'Augment generation with retrieved documents and external knowledge',
    longDesc: 'Retrieval-Augmented Generation (RAG) combines language models with information retrieval systems. Models are grounded in retrieved documents, reducing hallucinations and enabling access to up-to-date or specialized knowledge bases.',
    tags: ['rag', 'retrieval', 'grounding', 'vector-search', 'knowledge-base'],
    exampleTasks: [
      'Build Q&A systems over private document collections',
      'Ground model responses in retrieved evidence',
      'Implement semantic search with embedding models',
      'Create citation-backed generation pipelines'
    ],
    recommendedTemplates: ['rag_basic', 'rag_hybrid_search'],
    group: 'inference',
    subgroup: 'inference_time_strategies'
  },
  {
    id: 'multi_agent_debate_critic',
    title: 'Multi-Agent Debate & Critique',
    shortDesc: 'Use multiple model instances to debate, critique, and refine outputs',
    longDesc: 'Multi-agent systems employ multiple LLM instances with different roles (proposer, critic, judge) to iteratively improve outputs through debate and critique. This leverages diverse perspectives and catches errors through adversarial review.',
    tags: ['multi-agent', 'debate', 'critique', 'consensus', 'adversarial'],
    exampleTasks: [
      'Implement proposer-critic loops for code generation',
      'Use debate between models to reach better answers',
      'Build judge systems to evaluate competing solutions',
      'Create multi-perspective analysis pipelines'
    ],
    recommendedTemplates: ['debate_two_agent', 'critique_loop'],
    riskNotes: 'Higher inference cost; may not converge; requires careful orchestration',
    group: 'inference',
    subgroup: 'inference_time_strategies'
  },
  {
    id: 'verification_unit_tests',
    title: 'Verification & Unit Tests',
    shortDesc: 'Validate outputs with automated tests, formal verification, or execution',
    longDesc: 'Verification strategies use automated testing, code execution, or formal methods to validate model outputs. This is especially powerful for code generation, mathematics, and structured tasks where correctness can be objectively checked.',
    tags: ['verification', 'testing', 'execution', 'validation', 'formal-methods'],
    exampleTasks: [
      'Generate code and verify with unit tests',
      'Execute mathematical solutions to check correctness',
      'Use formal verification for logical proofs',
      'Implement test-driven generation workflows'
    ],
    recommendedTemplates: ['verify_execute', 'verify_unit_test'],
    group: 'inference',
    subgroup: 'inference_time_strategies'
  }
]

// ============================================================================
// Exported Data and Helper Functions
// ============================================================================

export const allDirections: Direction[] = [
  ...postTrainingDirections,
  ...inferenceDirections
]

export const categoryGroups = {
  'post-training': {
    label: 'Post-Training',
    subgroup: 'alignment_and_post_train',
    subgroupLabel: 'Alignment & Post-Training',
    description: 'Methods that modify model weights through training'
  },
  'inference': {
    label: 'Inference-Time',
    subgroup: 'inference_time_strategies',
    subgroupLabel: 'Inference-Time Strategies',
    description: 'Techniques applied during generation without weight updates'
  }
} as const

/**
 * Flatten all directions into a single array
 */
export function flattenDirections(): Direction[] {
  return allDirections
}

/**
 * Get a direction by its ID
 */
export function getDirectionById(id: string): Direction | undefined {
  return allDirections.find(d => d.id === id)
}

/**
 * Get all directions for a specific group
 */
export function getDirectionsByGroup(group: CategoryGroup): Direction[] {
  return allDirections.filter(d => d.group === group)
}

/**
 * Format a category label for display (handles legacy format)
 * @param category - Can be direction ID or legacy category string
 */
export function formatCategoryLabel(category: string): string {
  // Try to find as direction ID first
  const direction = getDirectionById(category)
  if (direction) {
    return `${categoryGroups[direction.group].label} / ${direction.title}`
  }

  // Legacy format fallback
  return category.split('_').map(word =>
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ')
}

/**
 * Search directions by query string (searches title, tags, descriptions)
 */
export function searchDirections(query: string): Direction[] {
  if (!query.trim()) return allDirections

  const lowerQuery = query.toLowerCase()
  return allDirections.filter(d =>
    d.title.toLowerCase().includes(lowerQuery) ||
    d.shortDesc.toLowerCase().includes(lowerQuery) ||
    d.longDesc.toLowerCase().includes(lowerQuery) ||
    d.tags.some(tag => tag.toLowerCase().includes(lowerQuery))
  )
}

/**
 * Get directions that have recommended templates
 */
export function getDirectionsWithTemplates(): Direction[] {
  return allDirections.filter(d => d.recommendedTemplates.length > 0)
}

/**
 * Normalize run category for display
 * Handles both legacy category strings and new taxonomy-based fields
 */
export function getRunCategoryInfo(run: {
  config: {
    category?: string
    categoryGroup?: CategoryGroup
    categoryDirectionId?: string
  }
}): {
  group: CategoryGroup | null
  direction: Direction | null
  label: string
} {
  // Try new taxonomy fields first
  if (run.config.categoryGroup && run.config.categoryDirectionId) {
    const direction = getDirectionById(run.config.categoryDirectionId)
    return {
      group: run.config.categoryGroup,
      direction: direction || null,
      label: direction
        ? `${categoryGroups[run.config.categoryGroup].label} / ${direction.title}`
        : run.config.categoryGroup
    }
  }

  // Fallback to legacy category field
  if (run.config.category) {
    return {
      group: null,
      direction: null,
      label: formatCategoryLabel(run.config.category)
    }
  }

  // No category info
  return {
    group: null,
    direction: null,
    label: 'Uncategorized'
  }
}
