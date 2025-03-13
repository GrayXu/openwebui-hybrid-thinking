"""
title: Hybrid Thinking (e.g. Use DeepSeek R1 for thinking, and use Claude 3.5 Sonnet for final output, to achieve better balance between reasoning price and performance.)
author: GrayXu
author_url: https://github.com/GrayXu
funding_url: https://github.com/GrayXu/openwebui-hybrid-thinking-func
version: 0.1.0
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

    def __init__(self):
        self.valves = self.Valves()
        self.client = httpx.Client(timeout=30)  # Synchronous HTTP client

    def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        """Request entry: Call the thinking model and inject context"""
        if not self.valves.THINKING_API_KEY:
            return body  # Skip if not configured
        
        # Clone messages to avoid contaminating original data
        messages = [msg.copy() for msg in body.get("messages", [])]
        
        try:
            # Call the thinking model to get reasoning content
            self.thinking_content = self._get_thinking_content(messages)
            if self.thinking_content:
                # Inject thinking content by role
                new_message = {
                    "role": 'user',
                    "content": f"Output should refer to this thinking record, record as follows:\n<thinking_content>{self.thinking_content}</thinking_content>"
                }
                messages.append(new_message)
                
                body["messages"] = messages  # Update message list
        
        except Exception as e:
            # Error handling (can log)
            pass
        
        return body

    def _get_thinking_content(self, messages: list) -> str:
        """Synchronous call to the thinking model API"""
        guiding_prompt = {
            "role": "system",
            "content": "Please focus on reasoning and minimize actual output."
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
        
        # Prefer extracting reasoning_content, then content
        message = data["choices"][0].get("message", {})
        return message.get("reasoning_content") or message.get("content", "")

    # def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
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