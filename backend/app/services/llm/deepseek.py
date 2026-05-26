"""
TextGuard DeepSeek 大模型 Provider
调用 DeepSeek API 进行文本校对
"""
import httpx
from typing import Optional, List, Dict
from loguru import logger

from app.services.llm.base import BaseLLMProvider, LLMResponse


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek 大模型 Provider"""

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.deepseek.com",
        model: str = "deepseek-chat",
        timeout: int = 60,
        max_retries: int = 3,
    ):
        super().__init__(api_key, api_base, model, timeout, max_retries)
        self.client = httpx.AsyncClient(
            base_url=api_base,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(timeout, connect=10),
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """调用 DeepSeek Chat API"""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = await self.client.post("/v1/chat/completions", json=payload)
                response.raise_for_status()
                data = response.json()

                choice = data["choices"][0]
                usage = data.get("usage", {})

                return LLMResponse(
                    content=choice["message"]["content"],
                    model=data.get("model", self.model),
                    usage={
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    },
                    finish_reason=choice.get("finish_reason"),
                )

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(
                    f"DeepSeek API 超时 (第{attempt}次): {e}"
                )
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.error(
                    f"DeepSeek API 错误 (第{attempt}次): status={e.response.status_code}, body={e.response.text[:200]}"
                )
                # 4xx 错误不重试
                if 400 <= e.response.status_code < 500:
                    break
            except Exception as e:
                last_error = e
                logger.error(f"DeepSeek API 异常 (第{attempt}次): {e}")

        raise RuntimeError(
            f"DeepSeek API 调用失败（已重试{self.max_retries}次）: {last_error}"
        )

    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()
