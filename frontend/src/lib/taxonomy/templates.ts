// ============================================================================
// Research Templates - Starter Configurations
// ============================================================================

export interface ResearchTemplate {
  id: string
  name: string
  directionId: string
  description: string
  config: {
    model: string
    temperature: number
    maxTokens: number
    budget?: number
  }
  workflowSteps?: string[]
  expectedArtifacts: string[]
  estimatedDuration?: string
}

// ============================================================================
// Post-Training Templates
// ============================================================================

export const postTrainingTemplates: ResearchTemplate[] = [
  {
    id: 'sft_basic',
    name: 'Basic SFT',
    directionId: 'sft_instruction_tuning',
    description: 'Standard supervised fine-tuning setup with balanced parameters',
    config: {
      model: 'gpt-4o-2024-08-06',
      temperature: 0.7,
      maxTokens: 2048,
      budget: 50
    },
    workflowSteps: [
      'Load base model and tokenizer',
      'Prepare instruction-response dataset',
      'Configure training hyperparameters',
      'Run fine-tuning loop with validation',
      'Evaluate on held-out test set',
      'Generate comparison report'
    ],
    expectedArtifacts: ['model_checkpoint', 'training_logs', 'evaluation_metrics', 'comparison_paper'],
    estimatedDuration: '2-4 hours'
  },
  {
    id: 'sft_lora',
    name: 'LoRA SFT',
    directionId: 'sft_instruction_tuning',
    description: 'Memory-efficient fine-tuning using Low-Rank Adaptation',
    config: {
      model: 'gpt-4o-mini',
      temperature: 0.7,
      maxTokens: 2048,
      budget: 25
    },
    workflowSteps: [
      'Initialize LoRA adapters',
      'Freeze base model weights',
      'Train only adapter parameters',
      'Merge adapters with base model',
      'Evaluate and compare to full fine-tuning'
    ],
    expectedArtifacts: ['lora_adapters', 'training_logs', 'merged_model', 'efficiency_report'],
    estimatedDuration: '1-2 hours'
  },
  {
    id: 'dpo_standard',
    name: 'Standard DPO',
    directionId: 'preference_optimization_dpo_ipo',
    description: 'Direct Preference Optimization with curated preference pairs',
    config: {
      model: 'gpt-4o-2024-08-06',
      temperature: 0.8,
      maxTokens: 2048,
      budget: 75
    },
    workflowSteps: [
      'Prepare preference dataset (chosen/rejected pairs)',
      'Initialize policy and reference models',
      'Compute DPO loss and optimize',
      'Validate on preference test set',
      'Generate quality comparison samples'
    ],
    expectedArtifacts: ['aligned_model', 'preference_metrics', 'sample_outputs', 'alignment_paper'],
    estimatedDuration: '3-5 hours'
  },
  {
    id: 'rlhf_ppo',
    name: 'RLHF with PPO',
    directionId: 'rlhf_rlaif',
    description: 'Full RLHF pipeline with reward model and PPO training',
    config: {
      model: 'gpt-4o-2024-08-06',
      temperature: 0.9,
      maxTokens: 2048,
      budget: 100
    },
    workflowSteps: [
      'Train reward model on human preferences',
      'Initialize policy and value networks',
      'Run PPO optimization loop',
      'Monitor KL divergence and reward',
      'Evaluate alignment metrics'
    ],
    expectedArtifacts: ['reward_model', 'aligned_policy', 'training_curves', 'safety_eval', 'research_paper'],
    estimatedDuration: '6-10 hours'
  },
  {
    id: 'tool_basic',
    name: 'Basic Tool Use',
    directionId: 'tool_use_function_calling',
    description: 'Train models to recognize and call simple functions',
    config: {
      model: 'gpt-4o-2024-08-06',
      temperature: 0.6,
      maxTokens: 1024,
      budget: 40
    },
    workflowSteps: [
      'Define function schemas and examples',
      'Create tool-use training dataset',
      'Fine-tune on function calling patterns',
      'Test with real API integrations',
      'Measure tool-use accuracy'
    ],
    expectedArtifacts: ['tool_model', 'function_schemas', 'test_results', 'integration_guide'],
    estimatedDuration: '2-3 hours'
  },
  {
    id: 'reasoning_cot',
    name: 'CoT Reasoning',
    directionId: 'reasoning_post_train_reflection',
    description: 'Distill chain-of-thought reasoning into model weights',
    config: {
      model: 'gpt-4o-2024-08-06',
      temperature: 0.7,
      maxTokens: 3072,
      budget: 60
    },
    workflowSteps: [
      'Generate CoT examples from teacher model',
      'Create reasoning dataset with intermediate steps',
      'Fine-tune student model on reasoning traces',
      'Evaluate on math and logic benchmarks',
      'Compare to baseline without CoT'
    ],
    expectedArtifacts: ['reasoning_model', 'cot_dataset', 'benchmark_scores', 'analysis_paper'],
    estimatedDuration: '3-4 hours'
  }
]

// ============================================================================
// Inference-Time Templates
// ============================================================================

export const inferenceTemplates: ResearchTemplate[] = [
  {
    id: 'prompt_cot',
    name: 'CoT Prompting',
    directionId: 'prompting_cot_scaffold',
    description: 'Structured prompts with chain-of-thought examples',
    config: {
      model: 'gpt-4o-2024-08-06',
      temperature: 0.7,
      maxTokens: 2048,
      budget: 20
    },
    workflowSteps: [
      'Design prompt template with reasoning structure',
      'Select few-shot examples',
      'Test on diverse problem types',
      'Optimize example selection',
      'Measure accuracy improvements'
    ],
    expectedArtifacts: ['prompt_templates', 'example_library', 'test_results', 'prompt_guide'],
    estimatedDuration: '1-2 hours'
  },
  {
    id: 'self_consistency',
    name: 'Self-Consistency',
    directionId: 'self_consistency_rerank',
    description: 'Sample multiple solutions and select by majority vote',
    config: {
      model: 'gpt-4o-2024-08-06',
      temperature: 0.9,
      maxTokens: 2048,
      budget: 30
    },
    workflowSteps: [
      'Generate N diverse reasoning paths',
      'Extract final answers from each path',
      'Implement majority voting logic',
      'Compare to single-sample baseline',
      'Analyze failure modes'
    ],
    expectedArtifacts: ['voting_results', 'sample_diversity_metrics', 'accuracy_comparison', 'analysis_report'],
    estimatedDuration: '1-2 hours'
  },
  {
    id: 'rag_basic',
    name: 'Basic RAG',
    directionId: 'retrieval_rag_grounding',
    description: 'Simple retrieval-augmented generation pipeline',
    config: {
      model: 'gpt-4o-2024-08-06',
      temperature: 0.6,
      maxTokens: 2048,
      budget: 35
    },
    workflowSteps: [
      'Index document collection with embeddings',
      'Implement semantic search retrieval',
      'Format retrieved context for prompt',
      'Generate grounded responses',
      'Evaluate factuality and citation accuracy'
    ],
    expectedArtifacts: ['vector_index', 'retrieval_metrics', 'grounded_outputs', 'rag_pipeline_code'],
    estimatedDuration: '2-3 hours'
  },
  {
    id: 'debate_two_agent',
    name: 'Two-Agent Debate',
    directionId: 'multi_agent_debate_critic',
    description: 'Two models debate to reach better conclusions',
    config: {
      model: 'gpt-4o-2024-08-06',
      temperature: 0.8,
      maxTokens: 2048,
      budget: 50
    },
    workflowSteps: [
      'Initialize two agent instances with different roles',
      'Implement debate protocol (propose, critique, refine)',
      'Run multi-round debate loop',
      'Aggregate final consensus',
      'Compare to single-agent baseline'
    ],
    expectedArtifacts: ['debate_transcripts', 'consensus_outputs', 'quality_metrics', 'debate_framework'],
    estimatedDuration: '2-3 hours'
  },
  {
    id: 'verify_execute',
    name: 'Execute & Verify',
    directionId: 'verification_unit_tests',
    description: 'Generate code and verify with execution',
    config: {
      model: 'gpt-4o-2024-08-06',
      temperature: 0.7,
      maxTokens: 2048,
      budget: 40
    },
    workflowSteps: [
      'Generate candidate code solutions',
      'Create test cases for verification',
      'Execute code in sandboxed environment',
      'Filter by test pass rate',
      'Analyze common failure patterns'
    ],
    expectedArtifacts: ['verified_code', 'test_suite', 'execution_logs', 'verification_report'],
    estimatedDuration: '2-3 hours'
  }
]

// ============================================================================
// Exported Data and Helper Functions
// ============================================================================

export const allTemplates: ResearchTemplate[] = [
  ...postTrainingTemplates,
  ...inferenceTemplates
]

/**
 * Get a template by its ID
 */
export function getTemplateById(id: string): ResearchTemplate | undefined {
  return allTemplates.find(t => t.id === id)
}

/**
 * Get all templates for a specific direction
 */
export function getTemplatesByDirection(directionId: string): ResearchTemplate[] {
  return allTemplates.filter(t => t.directionId === directionId)
}

/**
 * Get template count by direction
 */
export function getTemplateCountByDirection(directionId: string): number {
  return getTemplatesByDirection(directionId).length
}

/**
 * Check if a direction has templates
 */
export function hasTemplates(directionId: string): boolean {
  return getTemplateCountByDirection(directionId) > 0
}
