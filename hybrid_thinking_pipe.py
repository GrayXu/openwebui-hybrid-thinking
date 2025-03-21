"""
title: Hybrid Thinking Pipe
author: GrayXu
description: You can use DeepSeek R1 or QwQ 32B for cheap and fast thinking, and use stronger and more expensive models like Claude 3.7 Sonnet for final summarization output, to achieve a better balance between inference cost and performance.
author_url: https://github.com/GrayXu
funding_url: https://github.com/GrayXu/openwebui-hybrid-thinking
version: 0.3.1
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
                if line.startswith(DATA_PREFIX):
                    json_str = line[len(DATA_PREFIX):]
                    try:
                        data = json.loads(json_str)
                        choices = data.get("choices", [])
                        if len(choices) == 0:
                            continue
                        if choices[0].get("finish_reason", "") == "stop":  # early stop
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
        REASONING_CONTENT_AS_CONTEXT: bool = Field(
            default=True,
            description="use reasoning content as context"
        )
        CONTENT_AS_CONTEXT: bool = Field(
            default=False,
            description="use normal content as context"
        )
        GUIDING_PROMPT: str = Field(
            default="You are a helpful AI assistant who excels at reasoning. For code snippets, you wrap them in Markdown codeblocks with it's language specified.", # from DeepClaude
            description="guiding prompt (the lang you use may affect the lang of the output)"
        )

    def __init__(self):
        self.valves = self.Valves()
        self.data_prefix = DATA_PREFIX
        self.emitter = None
        self.thinking_content = ""
        self.output_content = ""
        self.think_flag = False

    def pipes(self):
        return [{"id": "Hybrid Thinking", "name": "Hybrid Thinking"}]

    async def _emit(self, content: str) -> AsyncGenerator[str, None]:
        while content:
            yield content[0]
            content = content[1:]
    
    async def think_data_handler(self, data) -> AsyncGenerator[str, None]:
        if "error" in data:
            async for chunk in self._emit(data["error"]):
                yield chunk
            return

        choice = data.get("choices", [{}])[0]
        delta = choice.get("delta", {})
        finish_reason = choice.get("finish_reason", "")

        # DeepSeek style thinking
        if content := delta.get("reasoning_content"):
            if not self.think_flag:
                self.thinking_content += "<think>\n"
                self.think_flag = True
                yield "<think>\n"
            self.thinking_content += content
            yield content
        
        # Tag style thinking
        elif content := delta.get("content"):
            if "<think>" in content:
                self.think_flag = True
            if "</think>" in content:
                content = content.replace("</think>", "") # rm think end tag
                self.thinking_content += content
                self.think_flag = False
            if self.think_flag:
                self.thinking_content += content
                yield content
            else:  # data content
                if self.valves.CONTENT_AS_CONTEXT:
                    self.output_content += content
                    yield content
                else:
                    yield None  # early quit
                    return
        # stop
        if finish_reason == "stop":
            yield None
    
    async def pipe(
        self,
        body: dict,
        __event_emitter__: Callable[[dict], Awaitable[None]] = None,
    ) -> AsyncGenerator[str, None]:
        self.emitter = __event_emitter__

        if not self.valves.THINKING_API_KEY:
            yield json.dumps({"error": "Missing api key"}, ensure_ascii=False)
            return
        ###################  thinking  ##################
        thinking_model = self.valves.THINKING_MODEL

        guiding_prompt = {
            "role": "user",  # DeepSeek R1's official documentation recommends using "user".
            "content": self.valves.GUIDING_PROMPT
        }
        messages = body.get("messages", [])
        messages.insert(0, guiding_prompt)
        parameters = {
            "model": thinking_model,
            "messages": messages,
            **{k: v for k, v in body.items() if k not in ["model", "messages"]},  # other params
        }

        self.thinking_content = ""
        self.output_content = ""
        self.think_flag = False
        # thinking model
        async for data in openai_api_call(
            payload=parameters,
            API_URL=self.valves.THINKING_API_URL,
            api_key=self.valves.THINKING_API_KEY,
        ):
            async for chunk in self.think_data_handler(data):
                if chunk is None:
                    break
                yield chunk
            
        # output think end tag
        async for chunk in self._emit("</think>"):
            yield chunk

        # context
        context = (
            ("<think>\n" if self.valves.CONTENT_AS_CONTEXT and not self.valves.REASONING_CONTENT_AS_CONTEXT else "")
            + (self.thinking_content if self.valves.REASONING_CONTENT_AS_CONTEXT else "")
            + (self.output_content if self.valves.CONTENT_AS_CONTEXT else "")
            + "</think>"
        )
        
        ###################  output  ##################
        # as a new assistant message (from DeepClaude)
        messages = body.get("messages", []) + [{
            "role": "assistant",
            "content": context
        }]
        
        parameters = {
            "model": self.valves.OUTPUT_MODEL,
            "messages": messages,
            **{k: v for k, v in body.items() if k not in ["model", "messages"]},  # other params
        }
        
        # output model
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
                    
            if choice.get("finish_reason","") == "stop":
                return