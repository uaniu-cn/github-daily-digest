"""
调用 DeepSeek API（OpenAI兼容接口），对每个 GitHub 项目做"复刻难度"打分。
"""
import json
import os
import requests

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"

SYSTEM_PROMPT = """你是一个资深全栈工程师 + 硬件极客，负责评估开源项目"复刻难度"，并判断是否值得推荐。
给定项目的名称、语言、简介、README片段，请输出一个JSON对象，格式严格如下，不要输出任何其他文字、不要使用markdown代码块：

{
  "summary": "<1句话，用简单直白的中文说明这个项目是做什么的、解决什么问题，让人一眼就能判断要不要细看>",
  "difficulty_score": <1到10的整数，1最简单，10最难>,
  "reason": "<1-2句话，说明打分理由>",
  "entry_point": "<1句话，建议从哪个角度/模块切入复刻，给出实操建议>",
  "is_interesting": <true或false，是否值得推荐>
}

"is_interesting" 判断标准（重要，按优先级）：
1. 【最优先】基于嵌入式硬件/单片机的项目优先判定为true，包括但不限于：ESP32/ESP8266、树莓派(Raspberry Pi)、Arduino、STM32等芯片平台的开发项目；机器人、RC车/无人车、无人机、智能家居硬件、传感器/物联网设备、3D打印机固件、CNC控制等软硬件结合项目。
2. 其次，有实际使用场景、设计巧妙、代码量适中、能学到东西的软件项目也可以判定为true（不限于硬件类）。
3. 以下情况判定为false：纯教程/笔记/awesome-list/资源汇总类仓库；没有实际功能只是文档的仓库；过于简单的demo或玩具项目；与个人简历/作品集类无技术含量的仓库。

打分维度参考（difficulty_score）：
- 技术栈复杂度（用到的框架、语言特性，硬件项目要考虑驱动/协议/电路设计难度）
- 是否依赖特殊基础设施、付费API/服务，或特殊硬件设备
- 代码规模（粗略估计）
- 核心算法/架构难点
"""


def score_repo(repo: dict, readme: str = "") -> dict:
    api_key = os.environ["DEEPSEEK_API_KEY"]

    user_content = f"""项目名: {repo['full_name']}
链接: {repo['url']}
主要语言: {repo['language']}
简介: {repo['description']}
Star总数: {repo['total_stars']}
今日新增Star: {repo['today_stars']}

README片段:
{readme[:3000] if readme else "(无README或获取失败)"}
"""

    resp = requests.post(
        DEEPSEEK_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "max_tokens": 600,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "response_format": {"type": "json_object"},
        },
        timeout=60,
    )
    if resp.status_code != 200:
        # 打印详细错误体，方便定位问题（不会泄露API Key）
        print(f"API错误详情 [{resp.status_code}]: {resp.text[:500]}")
    resp.raise_for_status()
    data = resp.json()

    text = data["choices"][0]["message"]["content"].strip()

    # 去除可能出现的代码块包裹
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        result = {
            "summary": "",
            "difficulty_score": None,
            "reason": "LLM输出解析失败，原始内容: " + text[:200],
            "entry_point": "",
            "is_interesting": True,
        }

    return result
