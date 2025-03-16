"""
title: Hybrid Thinking
description: You can use DeepSeek R1 or QwQ 32B for cheap and fast thinking, and use stronger and more expensive models like Claude 3.7 Sonnet for final summarization output, to achieve a better balance between inference cost and performance.
author: GrayXu
author_url: https://github.com/GrayXu
funding_url: https://github.com/GrayXu/openwebui-hybrid-thinking
version: 0.1.2
"""

from pydantic import BaseModel, Field
from typing import Optional
import httpx

class Filter:
    thinking_content = ""
    output_thinking = False
    
    class Valves(BaseModel):
        THINKING_API_URL: str = Field(
            default="https://api.deepseek.com/v1/chat/completions",
            description="thinking model api url"
        )
        THINKING_API_KEY: str = Field(
            default="",
            description="thinking model api key"
        )
        THINKING_MODEL: str = Field(
            default="deepseek-r1",
            description="thinking model name"
        )
        REASONING_CONTENT_AS_CONTEXT: bool = Field(
            default=True,
            description="use reasoning content as context"
        )
        CONTENT_AS_CONTEXT: bool = Field(
            default=False,
            description="use normal content as context"
        )

    def __init__(self):
        self.valves = self.Valves()
        self.client = httpx.Client(timeout=30)  # Synchronous HTTP client

    def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        self.output_thinking = False
        """Request entry: Call the thinking model and inject context"""
        if not self.valves.THINKING_API_KEY:
            return body  # Skip if not configured
        
        # Clone messages to avoid contaminating original data
        messages = [msg.copy() for msg in body.get("messages", [])]
        
        # Call the thinking model to get reasoning content
        if self.valves.REASONING_CONTENT_AS_CONTEXT or self.valves.CONTENT_AS_CONTEXT:
            self.thinking_content = self._get_thinking_content(messages)
        
        if self.thinking_content:
            new_message = {
                "role": 'assistant',
                "content": f"<think>\n\"{self.thinking_content}\"</think>"  # from DeepClaude
            }
            messages.append(new_message)
            
            body["messages"] = messages  # Update message list
        
        return body

    def _get_thinking_content(self, messages: list) -> str:
        guiding_prompt = {
            "role": "user",
            "content": "You are a helpful AI assistant who excels at reasoning and responds in Markdown format. For code snippets, you wrap them in Markdown codeblocks with it's language specified."  # from DeepClaude
        }
        messages.insert(0, guiding_prompt)
        
        # This parameter is optimized for DeepSeek R1
        payload = {
            "model": self.valves.THINKING_MODEL,
            "messages": messages,
            "max_tokens": 16384,
            "temperature": 0.6,
            "stream": False
        }
        headers = {
            "Authorization": f"Bearer {self.valves.THINKING_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = self.client.post(
            self.valves.THINKING_API_URL,
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        
        data = response.json()
        if not data.get("choices"):
            return ""
        
        message = data["choices"][0].get("message", {})
        
        thinking_content = ""
        
        if self.valves.REASONING_CONTENT_AS_CONTEXT:
            if 'reasoning_content' in message:  # deepseek style
                thinking_content += message.get("reasoning_content")
            else:  # default style
                thinking_content += message.get("content", "").split("<think>")[1].split("</think>")[0]

        if self.valves.CONTENT_AS_CONTEXT:
            thinking_content += message.get("content", "").split("</think>")[1]
        
        return thinking_content
    
    # def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
    #     body['messages'][-1]['content'] = "<think>" + self.thinking_content + "</think>\n" + body['messages'][-1]['content']
    #     return body
    
    def stream(self, event: dict) -> dict:
        event_id = event.get("id")
        
        if not self.output_thinking:
            for choice in event.get("choices", []):
                delta = choice.get("delta")
                value = delta.get("content", None)
                delta['content'] = "<think>\n"+ self.thinking_content + "</think>\n" + value
                self.output_thinking = True
                break
    
        return event