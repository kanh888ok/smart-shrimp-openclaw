from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class LLMProvider:
    """可选 LLM Provider。

    默认不调用外部服务。只有 OPENAI_API_KEY 存在且 use_openai=True 时才启用。
    MVP 的核心逻辑不依赖大模型，便于本地和现场稳定演示。
    """

    def __init__(self, use_openai: bool = False, model: Optional[str] = None):
        self.use_openai = use_openai and bool(os.getenv("OPENAI_API_KEY"))
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._client = None
        if self.use_openai:
            from openai import OpenAI
            self._client = OpenAI()

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        if not self.use_openai:
            return ""
        assert self._client is not None
        input_payload = []
        if system:
            input_payload.append({"role": "system", "content": system})
        input_payload.append({"role": "user", "content": prompt})
        response = self._client.responses.create(model=self.model, input=input_payload)
        return getattr(response, "output_text", "") or ""
