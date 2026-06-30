"""
抓取 GitHub Trending (daily, 不限语言) 页面，解析出项目列表。
"""
import requests
from bs4 import BeautifulSoup


TRENDING_URL = "https://github.com/trending"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def fetch_trending(since="daily"):
    """
    抓取 GitHub Trending 页面，返回项目信息列表。
    since: daily / weekly / monthly
    """
    params = {"since": since}
    resp = requests.get(TRENDING_URL, headers=HEADERS, params=params, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    repos = []
    articles = soup.select("article.Box-row")

    for article in articles:
        # 项目名 + 链接
        title_tag = article.select_one("h2 a")
        if not title_tag:
            continue
        href = title_tag.get("href", "").strip("/")
        full_name = href  # e.g. "owner/repo"
        url = f"https://github.com/{href}"

        # 简介
        desc_tag = article.select_one("p")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        # 主语言
        lang_tag = article.select_one("span[itemprop='programmingLanguage']")
        language = lang_tag.get_text(strip=True) if lang_tag else "Unknown"

        # 总star数
        star_tag = article.select_one("a[href$='/stargazers']")
        total_stars = star_tag.get_text(strip=True).replace(",", "") if star_tag else "0"

        # 今日新增star
        today_stars_tag = article.select_one("span.d-inline-block.float-sm-right")
        today_stars = "0"
        if today_stars_tag:
            text = today_stars_tag.get_text(strip=True)
            today_stars = text.split()[0].replace(",", "")

        repos.append(
            {
                "full_name": full_name,
                "url": url,
                "description": description,
                "language": language,
                "total_stars": total_stars,
                "today_stars": today_stars,
            }
        )

    return repos


def fetch_readme(full_name):
    """
    通过 GitHub API 拉取仓库 README 原始文本（不需要 token，但有速率限制）。
    """
    api_url = f"https://api.github.com/repos/{full_name}/readme"
    try:
        resp = requests.get(
            api_url,
            headers={**HEADERS, "Accept": "application/vnd.github.v3.raw"},
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.text[:4000]  # 截断，避免prompt过长
    except requests.RequestException:
        pass
    return ""


if __name__ == "__main__":
    items = fetch_trending()
    print(f"共抓取到 {len(items)} 个项目")
    for r in items[:5]:
        print(r)
