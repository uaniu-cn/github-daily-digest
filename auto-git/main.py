"""
主流程：
1. 抓取 GitHub Trending（不限语言）
2. 对每个项目调用 Claude API 拉取README并打分
3. 筛选 is_interesting=True 的项目，按 (是否有趣, 综合排序) 取前 N 个
4. 生成 HTML 邮件并发送
"""
import os
import time

from scraper import fetch_trending, fetch_readme
from scorer import score_repo
from mailer import build_html, send_email

TOP_N = int(os.environ.get("TOP_N", "5"))


def main():
    print("开始抓取 GitHub Trending ...")
    repos = fetch_trending(since="daily")
    print(f"共抓取到 {len(repos)} 个项目")

    scored_items = []
    for repo in repos:
        try:
            readme = fetch_readme(repo["full_name"])
        except Exception as e:
            print(f"获取README失败: {repo['full_name']} - {e}")
            readme = ""

        try:
            score_result = score_repo(repo, readme)
        except Exception as e:
            print(f"打分失败: {repo['full_name']} - {e}")
            score_result = {
                "difficulty_score": None,
                "reason": "打分调用失败",
                "entry_point": "",
                "is_interesting": False,
            }

        merged = {**repo, **score_result}
        scored_items.append(merged)

        # 避免触发API速率限制
        time.sleep(1)

    # 筛选有趣的项目
    interesting = [it for it in scored_items if it.get("is_interesting", True)]

    # 按"今日新增star"排序（也可以改成按难度分排序）
    def sort_key(it):
        try:
            return int(it.get("today_stars", "0").replace(",", "") or 0)
        except ValueError:
            return 0

    interesting.sort(key=sort_key, reverse=True)

    top_items = interesting[:TOP_N]

    print(f"筛选出 {len(top_items)} 个项目用于推送")

    html = build_html(top_items)
    send_email(html)


if __name__ == "__main__":
    main()
