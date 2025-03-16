"""
title: Hybrid Thinking Pipe
author: GrayXu
description: You can use DeepSeek R1 or QwQ 32B for cheap and fast thinking, and use stronger and more expensive models like Claude 3.7 Sonnet for final summarization output, to achieve a better balance between inference cost and performance.
author_url: https://github.com/GrayXu
funding_url: https://github.com/GrayXu/openwebui-hybrid-thinking
version: 0.1.0
"""

import json
import httpx
from typing import AsyncGenerator, Callable, Awaitable
from pydantic import BaseModel, Field

DATA_PREFIX = "data: "

def format_error(status_code, error) -> str:
    try:
        err_msg = json.loads(error).get("message", error.decode(errors="ignore"))[:200]
    except Exception:
        err_msg = error.decode(errors="ignore")[:200]
    return json.dumps({"error": f"HTTP {status_code}: {err_msg}"}, ensure_ascii=False)

async def openai_api_call(
    payload: dict, API_URL: str, api_key: str
) -> AsyncGenerator[dict, None]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(http2=True) as client:
        async with client.stream(
            "POST",
            f"{API_URL}/chat/completions",
            json=payload,
            headers=headers,
            timeout=300,
        ) as response:
            if response.status_code != 200:
                error = await response.aread()
                yield {"error": format_error(response.status_code, error)}
                return
            async for line in response.aiter_lines():
                if not line.startswith(DATA_PREFIX):
                    continue
                json_str = line[len(DATA_PREFIX):]
                try:
                    data = json.loads(json_str)
                    choices = data.get("choices", [{}])
                    if choices and choices[0].get("finish_reason", "") == "stop":  # early stop
                        yield {"choices": [{"delta": {'content': '', 'reasoning_content': ''}, "finish_reason": "stop"}]}
                        return
                except json.JSONDecodeError as e:
                    error_detail = f"ERROR - Content：{json_str}，Reason：{e}"
                    yield {"error": format_error("JSONDecodeError", error_detail)}
                    return
                yield data


class Pipe:
    class Valves(BaseModel):
        THINKING_API_URL: str = Field(
            default="https://openrouter.ai/api/v1",
            description="thinking model api url",
        )
        THINKING_API_KEY: str = Field(
            default="",
            description="thinking model api key"
        )
        THINKING_MODEL: str = Field(
            default="deepseek-r1",
            description="thinking model name",
        )
        OUTPUT_API_KEY: str = Field(
            default="",
            description="output model api key",
        )
        OUTPUT_API_URL: str = Field(
            default="https://openrouter.ai/api/v1",
            description="output model api url",
        )
        OUTPUT_MODEL: str = Field(
            default="claude-3-5-sonnet-latest",
            description="output model name",
        )

    def __init__(self):
        self.valves = self.Valves()
        self.data_prefix = DATA_PREFIX
        self.emitter = None

    def pipes(self):
        return [{"id": "Hybrid Thinking", "name": "Hybrid Thinking"}]

    async def _emit(self, content: str) -> AsyncGenerator[str, None]:
        while content:
            yield content[0]
            content = content[1:]

    async def pipe(
        self,
        body: dict,
        __event_emitter__: Callable[[dict], Awaitable[None]] = None,
    ) -> AsyncGenerator[str, None]:
        self.emitter = __event_emitter__

        if not self.valves.THINKING_API_KEY:
            yield json.dumps({"error": "Missing api key"}, ensure_ascii=False)
            return

        thinking_model = self.valves.THINKING_MODEL
        thinking_content = ""
        parameters = {**body, "model": thinking_model}
        
        # add a think start tag
        async for chunk in self._emit("<think>\n"):
            yield chunk

        async for data in openai_api_call(
            payload=parameters,
            API_URL=self.valves.THINKING_API_URL,
            api_key=self.valves.THINKING_API_KEY,
        ):
            if "error" in data:
                async for chunk in self._emit(data["error"]):
                    yield chunk
                return

            choice = data.get("choices", [{}])[0]
            delta = choice.get("delta", {})

            if content := delta.get("reasoning_content"):
                async for chunk in self._emit(content):
                    thinking_content += chunk
                    yield chunk
            # if choice.get("finish_reason","") == "stop":
            #     break

        # as a new assistant message
        messages = body.get("messages", []) + [
            {"role": "assistant", "content": "<think>" + thinking_content + "</think>"}
        ]
        # append to the last message
        # body.get("messages")[-1]["content"] = body.get("messages")[-1]["content"] + "\n<think>" + deepseek_response + "\n</think>"
        # claude_messages = body.get("messages")
        
        parameters = {
            "model": self.valves.OUTPUT_MODEL,
            "messages": messages,
            **{k: v for k, v in body.items() if k not in ["model", "messages"]},  # other params
        }
        
        # add a think end tag
        async for chunk in self._emit("</think>"):
            yield chunk

        async for data in openai_api_call(
            payload=parameters,
            API_URL=self.valves.OUTPUT_API_URL,
            api_key=self.valves.OUTPUT_API_KEY,
        ):
            if "error" in data:
                async for chunk in self._emit(data["error"]):
                    yield chunk
                return
            
            choice = data.get("choices", [{}])[0]
            delta = choice.get("delta", {})
            
            if content := delta.get("content"):
                async for chunk in self._emit(content):
                    yield chunk
            # if choice.get("finish_reason","") == "stop":
            #     break