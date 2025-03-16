# openwebui-hybrid-thinking

A filter function for [open-webui](https://github.com/open-webui/open-webui) to do *hybrid-thinking*: you can use `DeepSeek R1` or `QwQ 32B` for cheap and fast thinking, and use stronger and more expensive models like `claude-3.7-Sonnet` for final summarization output, to achieve a better balance between inference cost and performance.

[Aider LLM Leaderboards](https://aider.chat/docs/leaderboards/) and [DeepClaude](https://github.com/getAsterisk/deepclaude) shows the efficiency of hybrid thinking:
- `deepseek-r1` + `claude-3.5-sonnet` can achieve results very close to `claude-3.7-sonnet-thinking` at 1/3 of the cost.


You can install this filter function by importing https://openwebui.com/f/grayxu/hybrid_thinking