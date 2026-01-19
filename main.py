# main.py
import time
from datetime import datetime
from pathlib import Path

from crawler import fetch_news, fetch_home_hot_links
from llm import summarize_with_ollama_api_chat


def _num_to_cn(n: int) -> str:
    """1~10 数字转中文序号：一、二、三...十"""
    mapping = {
        1: "一", 2: "二", 3: "三", 4: "四", 5: "五",
        6: "六", 7: "七", 8: "八", 9: "九", 10: "十"
    }
    return mapping.get(n, str(n))


def save_to_txt(items: list[dict], out_dir: str = ".") -> str:
    """
    items 格式：
    [
      {"title": "...", "url": "...", "summary": "..."},
      ...
    ]
    输出 txt 文件名：x年x月x日网易新闻要点.txt
    内容格式严格为：
    一、【标题】
    【链接】
    【要点总结】
    """
    now = datetime.now()
    filename = f"{now.year}年{now.month}月{now.day}日网易新闻要点.txt"
    out_path = Path(out_dir) / filename

    with open(out_path, "w", encoding="utf-8") as f:
        for idx, it in enumerate(items, 1):
            title = (it.get("title") or "").replace("\n", " ").strip()
            url = (it.get("url") or "").replace("\n", " ").strip()
            summary = (it.get("summary") or "").strip()
            cn_idx = _num_to_cn(idx)
            f.write(f"{cn_idx}、")
            f.write(f"{title}\n")
            f.write(f"{url}\n")
            f.write("【要点总结】\n")
            f.write(summary + "\n")
            # 每条之间空一行
            if idx != len(items):
                f.write("\n")
    return str(out_path)


def main():
    # 1) 从网易主页提取 10 个热点新闻链接
    hot_list = fetch_home_hot_links(limit=10)
    if not hot_list:
        print("未从主页提取到热点新闻链接（可能是页面结构变化/网络被拦截）")
        return

    print("\n========== 网易主页热点 Top10 ==========")
    for i, item in enumerate(hot_list, 1):
        print(f"{i:02d}. {item['text']}")
        print(f"    {item['url']}")

    # 2) 逐条抓正文 + LLM 总结，并收集结果
    results = []
    print("\n========== 开始逐条总结 ==========")

    for i, item in enumerate(hot_list, 1):
        url = item["url"]
        print(f"\n----- [{i:02d}/10] 抓取文章 -----")
        print("链接：", url)

        try:
            news = fetch_news(url)
        except Exception as e:
            print("抓取失败：", repr(e))
            continue

        # 如果文章页标题抓不到，就用主页 a 标签文字兜底
        title = (news.get("title") or "").strip()
        if not title or "未找到标题" in title:
            title = (item.get("text") or "").strip()

        content = (news.get("content") or "").strip()

        print("标题：", title)
        print("正文长度：", len(content))

        # 3) 超长截断：避免模型输入过大导致慢/失败
        if len(content) > 8000:
            content = content[:6000] + "\n...\n" + content[-1500:]

        print("正在调用本地LLM总结...")

        try:
            summary = summarize_with_ollama_api_chat(
                title=title,          # ✅ 传兜底后的标题
                content=content,
                model="deepseek-r1:1.5b",
                base_url="http://localhost:11434"
            )
        except Exception as e:
            print("LLM总结失败：", repr(e))
            continue

        print("\n【总结结果】")
        print(summary)

        # 注意：这里必须写入 title/url/summary，写文件才能拿到
        results.append({
            "title": title,
            "url": url,
            "summary": summary
        })

        time.sleep(0.5)

    # 4) 写入 txt 文件
    if results:
        txt_path = save_to_txt(results, out_dir=".")
        print(f"\n✅ 已写入总结文件：{txt_path}")
    else:
        print("\n没有成功总结任何新闻，因此未生成 txt。")


if __name__ == "__main__":
    main()
