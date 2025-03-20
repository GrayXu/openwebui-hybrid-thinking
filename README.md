# openwebui-hybrid-thinking

A **Pipe** and **Filter** for [open-webui](https://github.com/open-webui/open-webui) to do ***hybrid-thinking***: you can use `DeepSeek R1` or `QwQ 32B` for cheap and fast thinking, and use stronger and more expensive models like `claude-3.7-Sonnet` for final summarization output, to achieve a better balance between inference cost and performance.

[Aider LLM Leaderboards](https://aider.chat/docs/leaderboards/) and [DeepClaude](https://github.com/getAsterisk/deepclaude) shows the efficiency of hybrid thinking: `deepseek-r1` + `claude-3.5-sonnet` can achieve results very close to `claude-3.7-sonnet-thinking` at 1/3 of the cost.

You can install those scripts by importing:
- **Pipe** (recommended): https://openwebui.com/f/grayxu/hybrid_thinking_pipe
- **Filter**: https://openwebui.com/f/grayxu/hybrid_thinking

The filter version can be used with multiple derived models, but it doesn't support streaming the thought process (because filter doesn't support multiple stream requests?).   
The pipe version configures a pipe function corresponding to a hybrid thinking model, but it can support streaming all data.

You can set two booleans, `REASONING_CONTENT_AS_CONTEXT` and `CONTENT_AS_CONTEXT`, to control whether the reasoning and actual output are passed as context to the output model:
- The default behavior is consistent with Deep Claude, where only the reasoning content is used as context. However, be aware that this might confuse the output model.
- In practice, Aider only uses the final output of the reasoning model as context for the output model. If you want the same approach, set `REASONING_CONTENT_AS_CONTEXT=False` and `CONTENT_AS_CONTEXT=True`.

---

ref:
- part of pipe codes from [charleskanp](https://openwebui.com/f/charleskanp/deepclaude_2)