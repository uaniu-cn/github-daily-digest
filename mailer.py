"""
生成 HTML 邮件内容，并通过 Gmail SMTP 发送。
"""
import os
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def build_html(items: list) -> str:
    """
    items: list of dict，每个dict包含 repo信息 + score信息
    """
    today = date.today().strftime("%Y-%m-%d")

    rows = []
    for it in items:
        score = it.get("difficulty_score")
        score_display = f"{score} / 10" if score is not None else "未知"
        rows.append(
            f"""
            <div style="border:1px solid #e0e0e0; border-radius:8px; padding:16px; margin-bottom:14px;">
                <div style="font-size:16px; font-weight:bold; margin-bottom:6px;">
                    <a href="{it['url']}" style="color:#0969da; text-decoration:none;">{it['full_name']}</a>
                    <span style="float:right; background:#f0f0f0; padding:2px 10px; border-radius:12px; font-size:13px; color:#555;">
                        难度 {score_display}
                    </span>
                </div>
                <div style="color:#444; font-size:14px; margin-bottom:8px;">{it.get('description', '')}</div>
                <div style="color:#666; font-size:13px; margin-bottom:4px;">
                    语言: {it.get('language', '-')} | 总Star: {it.get('total_stars', '-')} | 今日新增: {it.get('today_stars', '-')}
                </div>
                <div style="color:#222; font-size:13px; margin-top:8px;">
                    <b>打分理由:</b> {it.get('reason', '-')}
                </div>
                <div style="color:#222; font-size:13px; margin-top:4px;">
                    <b>复刻切入点:</b> {it.get('entry_point', '-')}
                </div>
            </div>
            """
        )

    html = f"""
    <html>
    <body style="font-family: -apple-system, Helvetica, Arial, sans-serif; max-width:680px; margin:0 auto;">
        <h2 style="border-bottom:2px solid #0969da; padding-bottom:8px;">
            🔥 GitHub Trending 每日精选 — {today}
        </h2>
        {''.join(rows) if rows else '<p>今日没有筛选出合适的项目。</p>'}
        <p style="color:#999; font-size:12px; margin-top:24px;">
            本邮件由自动化脚本生成，数据来源 GitHub Trending，难度评分由 Claude 模型生成，仅供参考。
        </p>
    </body>
    </html>
    """
    return html


def send_email(html_content: str, subject: str = None):
    sender = os.environ["GMAIL_ADDRESS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]
    receiver = os.environ.get("RECEIVER_EMAIL", sender)

    if subject is None:
        subject = f"GitHub 每日精选 - {date.today().strftime('%Y-%m-%d')}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, app_password)
        server.sendmail(sender, receiver, msg.as_string())

    print(f"邮件已发送至 {receiver}")
