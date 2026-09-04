import base64

import requests

from ..prompts import SYSTEM_PROMPT, build_user_prompt
from ..schema import ProductAnalysis
from .base import AIImage, AIProvider, AIProviderError, ProviderResult


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str, api_base: str = "https://api.openai.com/v1", timeout: int = 90):
        self.api_key = api_key
        self.model = model
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout

    def analyze(self, images: list[AIImage], seller_notes: str | None) -> ProviderResult:
        content = [{"type": "input_text", "text": build_user_prompt(seller_notes)}]
        for image in images:
            encoded = base64.b64encode(image.path.read_bytes()).decode("ascii")
            content.append({"type": "input_image", "image_url": f"data:{image.mime_type};base64,{encoded}", "detail": "high"})

        payload = {
            "model": self.model,
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": SYSTEM_PROMPT}]},
                {"role": "user", "content": content},
            ],
            "text": {"format": {"type": "json_schema", "name": "product_analysis", "schema": ProductAnalysis.model_json_schema(), "strict": True}},
        }
        try:
            response = requests.post(
                f"{self.api_base}/responses",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise AIProviderError(f"AI request failed: {exc}") from exc

        if response.status_code >= 400:
            raise AIProviderError(f"AI provider returned HTTP {response.status_code}: {response.text[:500]}")

        data = response.json()
        raw_text = _extract_output_text(data)
        if not raw_text:
            raise AIProviderError("AI provider response did not contain structured output text.")
        return ProviderResult(raw_json=raw_text, response_payload=data)


def _extract_output_text(data: dict) -> str | None:
    direct = data.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                return content["text"]
    return None
