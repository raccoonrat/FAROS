from app.faros.models.provider import ProviderResult, ProviderTask
from app.faros.providers.base import BaseProvider
from app.llm.provider_client import ChatMessage, get_provider_client


class LLMProvider(BaseProvider):
    """LLM-backed provider adapter over the existing provider client."""

    provider_type = "llm"

    def invoke(self, task: ProviderTask) -> ProviderResult:
        client = get_provider_client(task.provider)
        response = client.chat(
            messages=[
                ChatMessage(role=message["role"], content=message["content"])
                for message in task.messages
            ],
            model=task.model,
            **task.options,
        )
        return ProviderResult(
            ok=True,
            provider=response.raw_provider,
            model=response.model,
            text=response.text,
            usage=response.usage,
            latency_ms=response.latency_ms,
        )
