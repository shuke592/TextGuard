"""
TextGuard 通用 OpenAI 兼容 Provider
支持所有兼容 OpenAI Chat Completions API 的大模型供应商：
  - OpenAI (ChatGPT / GPT-4o)
  - DeepSeek
  - LiteLLM
  - Azure OpenAI
  - 通义千问（兼容模式）
  - 文心一言（兼容模式）
  - 其他自建/转发网关
"""
import httpx
from typing import Optional, List, Dict
from loguru import logger

from app.services.llm.base import BaseLLMProvider, LLMResponse


class OpenAICompatProvider(BaseLLMProvider):
    """
    通用 OpenAI 兼容 Provider
    所有使用 /v1/chat/completions 接口格式的大模型均可使用此 Provider
    """

    def __init__(
        self,
        api_key: str,
        api_base: str,
        model: str,
        timeout: int = 60,
        max_retries: int = 3,
        provider_name: str = "OpenAI-Compatible",
    ):
        super().__init__(api_key, api_base, model, timeout, max_retries)
        self.provider_name = provider_name

        # 规范化 api_base：去掉末尾斜杠
        self.api_base = api_base.rstrip("/")

        # 智能确定 endpoint 顺序：避免重复 /v1 路径
        # 若用户填写的 api_base 已包含 /v1（如 LiteLLM 的 http://x:4000/v1），
        # 则优先使用 /chat/completions，避免每次都先 404 再 fallback 浪费时间
        if self.api_base.endswith("/v1"):
            self._endpoints = ["/chat/completions", "/v1/chat/completions"]
        else:
            self._endpoints = ["/v1/chat/completions", "/chat/completions"]
        # 已确认成功的 endpoint，后续直接复用，避免每次都试探
        self._verified_endpoint: Optional[str] = None

        self.client = httpx.AsyncClient(
            base_url=self.api_base,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(timeout, connect=15),
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """调用 Chat Completions API"""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        # 若已验证过 endpoint，则直接复用，避免每次都试探
        endpoints = (
            [self._verified_endpoint] if self._verified_endpoint else self._endpoints
        )

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            for endpoint in endpoints:
                try:
                    response = await self.client.post(endpoint, json=payload)
                    response.raise_for_status()
                    data = response.json()

                    # 记忆已验证的 endpoint，后续调用直接复用
                    self._verified_endpoint = endpoint

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

                except httpx.HTTPStatusError as e:
                    # 404 说明路径不对，尝试下一个 endpoint
                    if e.response.status_code == 404 and endpoint != endpoints[-1]:
                        continue
                    last_error = e
                    logger.error(
                        f"[{self.provider_name}] API 错误 (第{attempt}次, {endpoint}): "
                        f"status={e.response.status_code}, body={e.response.text[:300]}"
                    )
                    # 4xx 错误（非 404）不重试
                    if 400 <= e.response.status_code < 500 and e.response.status_code != 404:
                        raise RuntimeError(
                            f"[{self.provider_name}] API 返回 {e.response.status_code}: {e.response.text[:300]}"
                        )
                    break  # 非 404 的服务器错误，跳出 endpoint 循环进入重试

                except httpx.TimeoutException as e:
                    last_error = e
                    logger.warning(f"[{self.provider_name}] API 超时 (第{attempt}次): {e}")
                    break  # 超时跳出 endpoint 循环进入重试

                except Exception as e:
                    last_error = e
                    logger.error(f"[{self.provider_name}] API 异常 (第{attempt}次): {e}")
                    break

        raise RuntimeError(
            f"[{self.provider_name}] API 调用失败（已重试{self.max_retries}次）: {last_error}"
        )

    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()

    async def test_connection(self) -> Dict:
        """
        测试连接是否正常
        返回: {"success": bool, "model": str, "message": str, "usage": dict}
        """
        try:
            response = await self.chat(
                messages=[
                    {"role": "user", "content": "请回复'连接正常'四个字，不要有其他内容。"}
                ],
                temperature=0,
                max_tokens=20,
            )
            return {
                "success": True,
                "model": response.model,
                "message": response.content.strip(),
                "usage": response.usage,
            }
        except Exception as e:
            return {
                "success": False,
                "model": self.model,
                "message": str(e),
                "usage": {},
            }
