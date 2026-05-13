"""
Agent Executor Service

Minimal run executor used by the Runs API.
This version is aligned to the active provider client and avoids the old
standalone llm_client abstraction.
"""

import logging
import hashlib
from datetime import datetime
from typing import Optional

from app.modules.platform.contracts import Run
from app.modules.platform.contracts import Artifact, ArtifactType
from app.modules.platform.storage import get_run_storage
from app.modules.platform.storage import get_artifact_storage
from app.llm.provider_client import get_provider_client, ChatMessage, ProviderError

logger = logging.getLogger(__name__)


class AgentExecutor:
    """Executes a minimal agent workflow for run records."""

    def __init__(self):
        self.run_storage = get_run_storage()
        self.artifact_storage = get_artifact_storage()

    def execute_run(self, run_id: str) -> None:
        logger.info("Starting agent execution for run %s", run_id)

        try:
            run = self.run_storage.get(run_id)
            if not run:
                raise ValueError(f"Run {run_id} not found")

            prompt = self._build_research_prompt(run)
            provider_name = getattr(run.config, 'providerName', None) or 'moonshot'
            model_name = getattr(run.config, 'model', None) or None
            client = get_provider_client(provider_name)
            response = client.chat(
                messages=[
                    ChatMessage(
                        role='system',
                        content='You are an AI research assistant helping to explore research ideas.'
                    ),
                    ChatMessage(role='user', content=prompt),
                ],
                model=model_name,
                temperature=0.7,
                max_tokens=1000,
            )

            llm_result = {
                'content': response.text,
                'model': response.model,
                'duration_ms': response.latency_ms,
                'usage': response.usage,
            }

            artifact_content = self._format_result(run, llm_result)
            artifact = self._create_result_artifact(run_id, artifact_content)

            updated_run = run.model_copy(update={
                'status': 'completed',
                'endedAt': datetime.utcnow(),
                'artifactIds': [artifact.id],
            })
            self.run_storage.update(updated_run)
            logger.info("Run %s completed successfully", run_id)

        except ProviderError as e:
            logger.error("Provider call failed for run %s: %s", run_id, e)
            self._fail_run(run_id, f"Provider call failed: {str(e)}")
        except Exception as e:
            logger.error("Agent execution failed for run %s: %s", run_id, e, exc_info=True)
            self._fail_run(run_id, f"Agent execution failed: {str(e)}")

    def _build_research_prompt(self, run: Run) -> str:
        config = run.config
        paper_type = getattr(config, 'paperType', 'unknown')
        model = getattr(config, 'model', 'unknown')
        research_question = getattr(config, 'researchQuestion', '')

        return f"""I am conducting AI research with the following configuration:

Paper Type: {paper_type}
Model: {model}
Research Question: {research_question}

Please provide:
1. A brief analysis of this research configuration
2. Key considerations for this type of research
3. Suggested next steps or improvements

Keep your response concise and focused on actionable insights."""

    def _format_result(self, run: Run, llm_result: dict) -> str:
        content = f"""# Research Run Result

**Run ID:** {run.id}
**Model:** {run.config.model}
**Timestamp:** {datetime.utcnow().isoformat()}

## LLM Response

{llm_result['content']}

## Execution Metadata

- **LLM Model:** {llm_result['model']}
- **Duration:** {llm_result['duration_ms']}ms
- **Tokens Used:** {llm_result['usage']['total_tokens']} (prompt: {llm_result['usage']['prompt_tokens']}, completion: {llm_result['usage']['completion_tokens']})
"""
        return content

    def _create_result_artifact(self, run_id: str, content: str) -> Artifact:
        import uuid

        artifact_id = f"artifact_{uuid.uuid4().hex[:12]}"
        checksum = f"sha256:{hashlib.sha256(content.encode()).hexdigest()}"
        artifact = Artifact(
            id=artifact_id,
            runId=run_id,
            type=ArtifactType.LOG,
            filename=f"run_{run_id}_result.md",
            size=len(content.encode()),
            storagePath=f"/artifacts/{artifact_id}.md",
            checksum=checksum,
        )
        self.artifact_storage.create(artifact)
        return artifact

    def _fail_run(self, run_id: str, error_message: str) -> None:
        try:
            run = self.run_storage.get(run_id)
            if run:
                updated_run = run.model_copy(update={
                    'status': 'failed',
                    'endedAt': datetime.utcnow(),
                    'errorMessage': error_message,
                })
                self.run_storage.update(updated_run)
        except Exception as e:
            logger.error("Failed to mark run %s as failed: %s", run_id, e)


_executor_instance: Optional[AgentExecutor] = None


def get_agent_executor() -> AgentExecutor:
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = AgentExecutor()
    return _executor_instance
