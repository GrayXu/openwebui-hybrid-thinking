# openwebui-hybrid-thinking

A **Pipe** and **Filter** for [open-webui](https://github.com/open-webui/open-webui) to do ***hybrid-thinking***: you can use `DeepSeek R1` or `QwQ 32B` for cheap and fast thinking, and use stronger and more expensive models like `claude-3.7-Sonnet` for final summarization output, to achieve a better balance between inference cost and performance.

[Aider LLM Leaderboards](https://aider.chat/docs/leaderboards/) and [DeepClaude](https://github.com/getAsterisk/deepclaude) shows the efficiency of hybrid thinking: `deepseek-r1` + `claude-3.5-sonnet` can achieve results very close to `claude-3.7-sonnet-thinking` at 1/3 of the cost.

You can install those scripts by importing:
- **Pipe** (recommended): https://openwebui.com/f/grayxu/hybrid_thinking_pipe
- **Filter**: https://openwebui.com/f/grayxu/hybrid_thinking

The filter version can be used with multiple derived models, but it doesn't support streaming the thought process (because filter doesn't support multiple stream requests?).   
The pipe version configures a pipe function corresponding to a hybrid thinking model, but it can support streaming all data.

You can set two booleans, `REASONING_CONTENT_AS_CONTEXT` and `CONTENT_AS_CONTEXT`, to control whether the reasoning and actual output are passed as context to the output model:
- The default behavior is consistent with Deep Claude, where only the reasoning content is used as context. However, be aware that this might [confuse the output model](https://aider.chat/2025/01/24/r1-sonnet.html#thinking-output).
- In practice, Aider only uses the final output of the reasoning model as context for the output model. If you want the same approach, set `REASONING_CONTENT_AS_CONTEXT=False` and `CONTENT_AS_CONTEXT=True`.

---

一个为 [open-webui](https://github.com/open-webui/open-webui) 提供的 **管道 (Pipe)** 和 **过滤器 (Filter)**，用于实现 ***混合思考 (hybrid-thinking)***：你可以使用 `DeepSeek R1` 或 `QwQ 32B` 进行廉价且快速的思考，然后使用更强大、更昂贵的模型（如 `claude-3.7-Sonnet`）进行最终的总结输出，从而在推理成本和性能之间取得更好的平衡。

[Aider LLM 排行榜](https://aider.chat/docs/leaderboards/) 和 [DeepClaude](https://github.com/getAsterisk/deepclaude) 展示了混合思维的效率：`deepseek-r1` + `claude-3.5-sonnet` 可以以 1/3 的成本实现非常接近 `claude-3.7-sonnet-thinking` 的结果。

你可以通过导入以下脚本来安装它们：
- **管道 (Pipe)** (推荐): https://openwebui.com/f/grayxu/hybrid_thinking_pipe
- **过滤器 (Filter)**: https://openwebui.com/f/grayxu/hybrid_thinking

过滤器版本可以与多个派生模型一起使用，但它不支持流式传输思考过程（因为过滤器不支持多个流请求？）。
管道版本配置一个与混合思维模型对应的管道函数，但它可以支持流式传输所有数据。

你可以设置两个布尔值 `REASONING_CONTENT_AS_CONTEXT` 和 `CONTENT_AS_CONTEXT`，来控制是否将推理内容和实际输出作为上下文传递给输出模型：
- 默认行为与 DeepClaude 一致，仅将推理内容用作上下文。但是，请注意这可能会让[输出模型混乱](https://aider.chat/2025/01/24/r1-sonnet.html#thinking-output)。
- 在实践中，Aider 仅使用推理模型的最终输出作为输出模型的上下文。如果你想要相同的方法，请设置 `REASONING_CONTENT_AS_CONTEXT=False` 和 `CONTENT_AS_CONTEXT=True`。


---

ref:
- part of pipe codes from [charleskanp](https://openwebui.com/f/charleskanp/deepclaude_2)