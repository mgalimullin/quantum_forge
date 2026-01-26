import requests
from typing import List, Optional

from langchain_core.language_models.llms import LLM
from pydantic import Field


class YandexGPT5Lite(LLM):
    """
    LangChain-compatible wrapper for YandexGPT 5 Lite.
    """

    api_key: str = Field(...)
    folder_id: str = Field(...)
    temperature: float = 0.0
    max_tokens: int = 512

    @property
    def _llm_type(self) -> str:
        return "yandex-gpt-5-lite"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
    ) -> str:
        response = requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
            headers={
                "Authorization": f"Api-Key {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "modelUri": (
                    f"gpt://{self.folder_id}/yandexgpt-lite/latest"
                ),
                "completionOptions": {
                    "temperature": self.temperature,
                    "maxTokens": self.max_tokens,
                },
                "messages": [
                    {
                        "role": "user",
                        "text": prompt,
                    }
                ],
            },
            timeout=30,
        )

        response.raise_for_status()

        return response.json()["result"]["alternatives"][0][
            "message"
        ]["text"]
