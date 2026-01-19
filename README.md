# 163 News Summarizer (网易新闻热点摘要器)

一个可直接上传 GitHub 的 Python 项目：  
**爬取网易主页 Top10 热点新闻 → 抓取标题/原文 → 调用本地轻量 LLM（Ollama + DeepSeek）生成要点总结 → 输出到 TXT 文件**。

---

## ✨ 功能特性

- 自动从 **网易主页** 抓取 **10 条热点新闻链接**
- 进入每篇新闻页面，提取：
  - 标题
  - 原文正文（由多个 `<p>` 组成）
- 调用本地 LLM（例如 **DeepSeek**）自动生成 **3~5 条要点总结**
- 将结果写入本地 `txt` 文件，格式严格规范为：

```text
一、【标题】
【链接】
【要点总结】
<模型输出>

二、【标题】
【链接】
【要点总结】
<模型输出>
...
```

- 自动按日期命名输出文件，例如：

```text
2026年1月19日网易新闻要点.txt
```

---

## ✅ 环境要求

- Python **3.10+**（建议 3.11）
- Windows / macOS / Linux 均可
- 已部署本地 LLM（推荐 Ollama）

---

## 📦 安装依赖

建议使用虚拟环境：

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

`requirements.txt` 示例：

```txt
requests
beautifulsoup4
lxml
```

---

## 🧠 部署本地 LLM（推荐 Ollama + DeepSeek）

> 本项目默认使用 Ollama 本地 API，并以 DeepSeek 作为示例模型。

### 1) 安装 Ollama

请前往 Ollama 官网下载安装（Windows/macOS/Linux 均支持）。

### 2) 下载模型（示例：DeepSeek 1.5B）

```bash
ollama pull deepseek-r1:1.5b
```

你也可以换成更大模型（例如 7B/14B），但速度和硬件要求会更高。

### 3) 验证 Ollama 服务是否正常

在终端执行：

```bash
curl http://localhost:11434/api/tags
```

如果能返回本地模型列表 JSON，说明服务正常。

---

## 🚀 快速运行

直接运行主程序：

```bash
python main.py
```

程序将会：

1. 从网易主页抓取 10 条热点新闻链接
2. 逐条抓取正文
3. 逐条调用本地 LLM 生成摘要
4. 写入输出文件（默认生成在 `main.py` 同目录）

运行完成后你会看到类似输出：

```text
✅ 实际写入路径： C:\...\2026年1月19日网易新闻要点.txt
✅ 已写入总结文件：2026年1月19日网易新闻要点.txt
```

---

## ⚙️ 配置说明

你可以在 `main.py` 内修改模型与地址：

```python
summary = summarize_with_ollama_api_chat(
    title=title,
    content=content,
    model="deepseek-r1:1.5b",
    base_url="http://localhost:11434"
)
```

如果你的 Ollama 不在默认端口，请修改 `base_url`。

---

## 🗂️ 参考项目结构

推荐结构如下：

```text
.
├─ main.py              # 主入口：抓热点 → 总结 → 写入txt
├─ crawler.py           # 爬虫：主页热点链接 + 文章标题/正文提取
├─ llm.py               # 本地LLM调用（Ollama /api/chat）
├─ requirements.txt
└─ README.md
```

---

## 🧩 核心实现思路

### 1) 抓取网易主页 10 条热点新闻

- 访问 `https://www.163.com`
- 解析所有 `<a href="...">`
- 过滤符合格式的文章链接，例如：

```html
<a href="https://www.163.com/dy/article/KJKK81TM05346RC6.html">
  增长5%！2025年中国GDP跨越140万亿元关口
</a>
```

- 去重后取前 10 条。

### 2) 抓取新闻标题与正文

- 标题通常在 `<h1>`
- 正文一般由大量 `<p>` 组成（项目会拼接成原文）
- 对脚本、样式等标签做清理，减少噪声。

### 3) 调用本地 LLM 生成摘要

项目调用 Ollama 的 `/api/chat` 接口，并关闭流式输出（`stream: false`）：
- 更适合“结构化输出”和“写文件场景”
- 返回一次性 JSON，代码更好处理

### 4) 将结果写入 TXT（严格格式）

程序端统一控制输出格式，**不依赖模型输出标题/标签**，从而保证 TXT 结构永远规范。

---

## 🛠️ 常见问题（FAQ）

### Q1：Windows `curl` 报错（405 / `-d` 不是命令）

原因：Windows **CMD** 不支持 `\` 作为换行符，换行要用 `^` 或者直接写成一行。

正确写法（CMD 一行）：

```bat
curl -X POST http://localhost:11434/api/chat -H "Content-Type: application/json" -d "{\"model\":\"deepseek-r1:1.5b\",\"messages\":[{\"role\":\"user\",\"content\":\"Hello\"}],\"stream\":false}"
```

### Q2：TXT 输出标题/链接为空

请检查 `results.append(...)` 是否包含 `title/url/summary` 三个字段：

```python
results.append({
    "title": title,
    "url": url,
    "summary": summary
})
```

同时建议把写文件路径固定到 `main.py` 所在目录，避免 PyCharm 运行目录不同导致打开错文件。

### Q3：正文太长导致模型很慢/失败

项目默认会做截断（保留前后重点），你也可以调整阈值：

```python
if len(content) > 8000:
    content = content[:6000] + "\n...\n" + content[-1500:]
```

---

## ⚠️ 免责声明 / 合规建议

本项目仅用于 **学习与研究**：
- 请遵守目标网站的使用条款与 robots 协议
- 不要进行高频、大规模抓取
- 产生的数据请勿用于商业用途或非法用途

---

## 📄 License

MIT License（你也可以改为 Apache-2.0 / GPL 等）

---

## ⭐️ Roadmap（可选升级方向）

- [ ] 批量爬取更多频道（财经/体育/科技等）
- [ ] 输出为 `Markdown/JSON` 报告
- [ ] 提供命令行参数（`argparse`）
- [ ] 增加代理、重试、并发抓取优化
- [ ] 用 FastAPI 提供 HTTP 服务接口
