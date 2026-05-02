# TokTrans 小红书推广帖

这份文案是 README 风格的发布稿，可以直接改成小红书图文笔记。建议配 4 张图：

1. README 首屏截图
2. tokenizer 对比实验图
3. CodeMixBench Pass@1 图
4. TokTrans workflow 图或 Claude/Codex 双平台安装截图

## 标题备选

- 中文写 prompt，AI 编程助手真的会变笨吗？
- Codex / Claude Code 非英文体验差？可能不是你的 prompt 问题
- 我做了一个给 AI 编程助手用的翻译层：TokTrans
- 非英文开发者的 AI 编程助手补丁：TokTrans

## 正文

最近我做了一个开源小工具：**TokTrans**。

它解决的是一个很具体的问题：

你有没有感觉过，自己用中文/日文/其他非英文写任务时，Codex 或 Claude Code 好像没有英文时聪明？

或者同样一段需求，非英文输入时 token 消耗更快，额度掉得更明显？

这不一定是错觉。

已有一些实验显示，不同语言在 tokenizer 里的成本差异很大。Aran Komatsuzaki 的 tokenizer 对比实验里，以英文为 1x baseline，一些非英文语言会消耗更多 token。TestingCatalog 的总结里提到，在 Claude 3.7 Sonnet 上，中文、日文、印地语可能比英文多消耗 44% 到 65% token。

能力侧也有类似现象。2025 年的 CodeMixBench 发现，在代码生成任务中，code-mixed prompts 相比原始英文 prompts 往往会降低 Pass@1。另一篇 EMNLP Findings 2025 的论文 When Models Reason in Your Language 也展示了一个很有意思的 trade-off：强行让模型用用户语言思考，可以提高 thinking trace 的语言匹配率，但平均准确率会下降。

所以 TokTrans 的思路不是“让你必须用英文”，而是：

```text
你用自己的语言描述任务
-> TokTrans 把自然语言部分翻译成 agent 更容易处理的形式
-> 保留代码、路径、命令、日志、JSON/YAML/TOML 等技术 token
-> Codex / Claude Code 正常完成任务
-> 最终回答再翻译回你的语言
```

目前支持：

- Codex skill：`$token-trans ...`
- Claude Code skill：`$token-trans ...`
- Codex CLI wrapper：`codex-ts`

安装 Codex skill：

```bash
curl -fsSL https://raw.githubusercontent.com/lyymuwu/TokTrans/main/scripts/bootstrap.sh | bash -s -- --skill-only
```

安装 Claude Code skill：

```bash
git clone https://github.com/lyymuwu/TokTrans.git
cd TokTrans
bash scripts/install-claude-code.sh
```

使用方式很简单：

```text
$token-trans 帮我检查这个项目为什么测试失败
```

它不会替换官方 `codex` 或 `claude`，也不会把仓库文件、历史记录、密钥传给翻译子 agent。翻译子 agent 只拿到需要翻译的那段文本。

这个项目不是魔法，也不是说所有任务都应该翻译。短问题、纯代码、路径和日志为主的任务，直接用原 agent 就很好。

但如果你经常用中文做复杂代码 review、debug、服务器排查、实验规划，它可能能减少一些“明明我说清楚了，但 agent 没接住”的情况。

GitHub：

https://github.com/lyymuwu/TokTrans

如果你也是非英文 AI 编程用户，欢迎试一下。觉得有帮助的话，给个 star，让更多多语言开发者看到它。

## 评论区置顶备选

TokTrans 的核心不是“省 token 神器”，而是给 Codex / Claude Code 加一个显式翻译层：保留技术 token，把自然语言任务翻译成 agent 更容易处理的形式，最后再翻译答案。

## 标签

#AI编程 #Codex #ClaudeCode #开源项目 #程序员工具 #AI工具 #GitHub开源 #Prompt工程 #开发效率 #多语言
