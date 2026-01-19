# src/llm.py
import re
import requests

def _clean_deepseek_output(text: str) -> str:
    """
    DeepSeek-R1 有时会带 <think>...</think>（思维链）
    这里简单清理掉，避免输出太长
    """
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    return text.strip()


def summarize_with_ollama_api_chat(
    title: str,
    content: str,
    model: str = "deepseek-r1:1.5b",
    base_url: str = "http://localhost:11434",
    timeout: int = 120,
) -> str:

    url = f"{base_url}/api/chat"

    prompt = f"""你是新闻摘要助手。请只输出【要点总结】内容，不要输出标题，不要输出链接，不要输出任何【】标签，不要输出多余说明。
    要求：
    1）输出若干条要点，每条以“1.”“2.”编号开头
    2）总字数<=200，客观精炼，包含关键数据
    3）不要出现空行，不要出现Markdown，不要重复任何字段
    正文：
    {content}
    """

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    r = requests.post(url, json=payload, timeout=timeout)
    r.raise_for_status()
    data = r.json()

    # /api/chat 返回结构里一般是 data["message"]["content"]（官方示例就是 messages 对话形式）:contentReference[oaicite:3]{index=3}
    summary = data.get("message", {}).get("content", "")
    return _clean_deepseek_output(summary)
