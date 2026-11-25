# 投稿文章

每篇文章使用一个 Markdown 文件，文件顶部填写 YAML 元数据。构建脚本自动生成文章页面与 `data/articles.json`。

```yaml
---
author: 昵称
campus: hk
year: "2022"
term: fall
degree: BSc
field: Computer Science
category: further-studies
destination: 示例项目
contact:
  - type: Email
    value: hello@example.com
published_at: '2026-11-25T00:00:00Z'
---
这里写 Markdown 正文。
```

业务字段和枚举以 `data/schema.json` 为准。入学季 `term` 必须选择 `fall` 或 `spring`，两种界面均显示 Fall / Spring，年份仍指实际入学的公历年份。只有联系方式选填：类型和值均自由填写，双空忽略、单空拒绝。`year` 必须是四位入学年份字符串，不能由毕业年份推算。联系方式公开显示于详情页，排除站内搜索和文章索引。
标题由「author · destination」生成；背景显示「campus · year · degree」，专业/研究方向单列。摘要从正文提取。`published_at` 为系统记录的首次审核发布时间，`source_issue` 为原投稿编号；无需投稿者填写。不要提交未经许可的个人信息，不接受可执行 HTML。

## 演示文章

演示文章使用 `demo: true`，统一存放在 `content/demo/`。真实投稿增加后可以直接删除此目录，构建会自动清理对应页面与索引。演示不代表真实经历。

演示库覆盖五个方向，每个方向一篇虚构示例。前台只显示简洁的「演示」标识，不暗示文章为真人投稿；删除 `content/demo/` 即可全部移除。

投稿表单的 `data/demo-submission.md` 是独立的纯正文写作示例。

## Markdown 渲染约定

正文在投稿编辑器预览与正式文章中使用相同的 `.article-body` 视觉样式。
浏览器通过 Marked + DOMPurify 生成即时预览，静态构建由
`scripts/markdown_render.py` 使用 Python-Markdown + Bleach 完成。
两条路径采用相同的安全策略：把作者输入的原始 HTML 转为纯文本，
保留 Markdown 的结构字符（尤其是引用语法 `>`），最终禁止可执行 HTML。

支持标题、引用、加粗、删除线、列表、任务列表、链接、表格及围栏代码块。
由于客户端和构建端使用不同解析器，复杂的非标准 Markdown 扩展不属于
严格等价性承诺；受支持语法的结构和样式由 Python 单元测试和浏览器回归测试共同约束。

维护渲染规则时，应同时核对 `assets/js/submit.js`、
`scripts/markdown_render.py` 与 `assets/css/site.css`，不要只在单侧增加特殊样式。
