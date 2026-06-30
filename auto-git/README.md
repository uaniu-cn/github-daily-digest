# GitHub Daily Digest

每天自动抓取 GitHub Trending（daily，不限语言），用 Claude API 对每个项目做"复刻难度"打分，
挑选出最值得关注的 5 个项目，整理成邮件，通过 Gmail 推送到你的邮箱。整个流程跑在
GitHub Actions 上，免费、无需自己维护服务器。

## 工作流程

1. `scraper.py` 抓取 `github.com/trending` 页面，拿到当天所有 trending 项目
2. 对每个项目调用 GitHub API 拉取 README 片段
3. `scorer.py` 调用 Claude API，对项目做难度打分 + 给出复刻切入点建议，并判断是否值得推荐
4. 按"是否有趣"筛选、按今日新增star排序，取前 5 个
5. `mailer.py` 生成 HTML 邮件并通过 Gmail SMTP 发送
6. `main.py` 是入口，串联以上所有步骤
7. `.github/workflows/daily_digest.yml` 让 GitHub Actions 每天定时自动跑一次（默认北京时间早 8 点）

## 部署步骤

### 第一步：在 GitHub 上创建一个新仓库

把这个文件夹的所有文件 push 到一个新的 GitHub 仓库（可以是 private 仓库）。

### 第二步：获取两个密钥

**1. Anthropic API Key**

- 打开 https://console.anthropic.com
- 注册/登录后，进入 API Keys 页面，创建一个新的 Key
- 复制保存好（只会显示一次）

**2. Gmail 应用专用密码**

- 先确保你的 Google 账号已开启"两步验证"（在 Google 账号安全设置里）
- 打开 https://myaccount.google.com/apppasswords
- 选择"应用"为"邮件"，生成一个 16 位的应用专用密码（这不是你的登录密码）
- 复制保存好

### 第三步：在 GitHub 仓库里配置 Secrets

进入你的仓库 → Settings → Secrets and variables → Actions → New repository secret，
依次添加以下 4 个：

| Secret 名称 | 值 |
|---|---|
| `ANTHROPIC_API_KEY` | 第二步获取的 Anthropic API Key |
| `GMAIL_ADDRESS` | 你的 Gmail 地址，例如 `yourname@gmail.com` |
| `GMAIL_APP_PASSWORD` | 第二步获取的 16 位应用专用密码 |
| `RECEIVER_EMAIL` | 收件邮箱，可以和发件邮箱相同，也可以填别的邮箱 |

### 第四步：测试运行

不需要等到第二天，配置好 Secrets 后：

1. 进入仓库的 Actions 标签页
2. 左侧选择 "GitHub Daily Digest" 这个 workflow
3. 点击右侧的 "Run workflow" 按钮，手动触发一次
4. 等待 1-2 分钟，查看运行日志；如果成功，你的邮箱应该会收到一封邮件

### 第五步：之后就是全自动的

配置好之后，GitHub Actions 会按 cron 设定的时间（默认北京时间每天早 8 点）自动运行，
不需要你再做任何操作。

## 可调整的地方

- **推送数量**：修改 `daily_digest.yml` 里的 `TOP_N` 环境变量
- **定时时间**：修改 `daily_digest.yml` 里的 cron 表达式（注意是 UTC 时间）
- **排序逻辑**：默认按"今日新增star"排序，可在 `main.py` 的 `sort_key` 函数里改成按难度分排序
- **打分维度/prompt**：在 `scorer.py` 的 `SYSTEM_PROMPT` 里调整

## 注意事项

- GitHub 未登录访问 Trending API 和 README API 有一定速率限制，如果未来抓取项目变多导致频繁报错，
  可以考虑申请一个 GitHub Personal Access Token 加到请求头里提高限额（当前脚本未使用，正常每天用量足够）。
- Claude API 是按量计费的，每天约 20-25 个项目调用一次打分，单次调用成本很低，但建议关注一下账单。
- 如果某天 GitHub Trending 页面结构发生变化导致抓取失败，需要更新 `scraper.py` 里的 CSS 选择器。
