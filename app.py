"""Moonpull — 个人 AI 商业研究助手。运行：streamlit run app.py"""

import base64
import os
import re
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import openai
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from prompts import REPORT_PROMPT, SYSTEM_PROMPT


ROOT = Path(__file__).resolve().parent
DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-flash"
# 与启动命令所在目录无关；已有系统环境变量优先于 .env。
load_dotenv(ROOT / ".env")


def chat(messages, api_key, base_url, model):
    """使用 OpenAI 兼容接口；不将密钥或原始接口错误写入页面。"""
    is_grok = model.strip().lower().startswith("grok-")
    request = {"model": model, "messages": messages}
    # Grok 使用服务商默认生成参数，减少不同模型参数支持差异的影响。
    if not is_grok:
        request["temperature"] = 0.3
    with OpenAI(
        api_key=api_key, base_url=base_url,
        timeout=180.0 if is_grok else 60.0, max_retries=1,
    ) as client:
        response = client.chat.completions.create(**request)
    if not response.choices:
        raise ValueError("模型没有返回回答，请重试或检查模型配置。")
    choice = response.choices[0]
    content = choice.message.content
    if not content or not content.strip():
        raise ValueError("模型返回了空内容，请重试或更换模型。")
    if choice.finish_reason == "length":
        raise ValueError("回答超过模型输出上限，请缩小问题范围或更换模型后重试。")
    return content.strip()


def friendly_error(error):
    if isinstance(error, openai.AuthenticationError):
        return "API Key 验证失败，请确认密钥与服务地址属于同一服务商。"
    if isinstance(error, openai.PermissionDeniedError):
        return "当前账号没有调用权限，请检查模型权限或服务商设置。"
    if isinstance(error, openai.RateLimitError):
        return "接口限流或额度不足，请检查余额并稍后重试。"
    if isinstance(error, openai.APITimeoutError):
        return "请求超时，请稍后重试或缩小问题范围。"
    if isinstance(error, openai.APIConnectionError):
        return "无法连接 AI 服务，请检查网络和服务地址。"
    if isinstance(error, (openai.NotFoundError, openai.BadRequestError)):
        return "接口地址、模型名称或请求不受支持，请核对 OPENAI_BASE_URL、MODEL_NAME，并确认账号有对应模型权限。"
    if isinstance(error, openai.APIStatusError):
        return "AI 服务暂时不可用，请稍后重试。"
    if isinstance(error, ValueError):
        return str(error)
    return "请求未能完成，请检查配置后重试。已有对话和报告已保留。"


def generate_pdf(text):
    """内置中文 CID 字体，不依赖电脑上存在 simsun.ttc。"""
    font = "STSong-Light"
    if font not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(UnicodeCIDFont(font))
    body = ParagraphStyle(
        "ChineseBody", fontName=font, fontSize=10.5, leading=17,
        wordWrap="CJK", textColor=colors.HexColor("#253047"),
    )
    headings = {
        level: ParagraphStyle(
            f"Heading{level}", parent=body, fontSize=19 if level == 1 else 13,
            leading=25 if level == 1 else 20, spaceBefore=12, spaceAfter=8,
            keepWithNext=True,
        )
        for level in (1, 2, 3)
    }
    story = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            story.append(Spacer(1, 5))
            continue
        match = re.match(r"^(#{1,3})\s+(.+)$", line)
        style = headings[len(match[1])] if match else body
        line = match[2] if match else line
        # 保留链接目标；模型输出作为文本处理，避免 <、& 导致 PDF 解析失败。
        line = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", line)
        line = line.replace("**", "").replace("`", "")
        story.append(Paragraph(escape(line), style))
        story.append(Spacer(1, 4))
    if not any(isinstance(item, Paragraph) for item in story):
        raise ValueError("报告内容为空。")
    buffer = BytesIO()
    SimpleDocTemplate(
        buffer, pagesize=A4, title="Moonpull AI · 月之引力 · 商业借鉴报告", author="Moonpull AI",
        rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm,
    ).build(story)
    return buffer.getvalue()



def render_theme():
   background = base64.b64encode((ROOT / "deep-space.png").read_bytes()).decode("ascii")
css = (ROOT / "style.css").read_text(encoding="utf-8")
    st.markdown(
        '<style>:root{--moonpull-space:url("data:image/png;base64,'
        + background + '");}' + css + '</style>', unsafe_allow_html=True,
    )


def render_welcome():
    st.markdown(
        '<section class="mp-hero" aria-label="Moonpull AI 月之引力">'
        '<h1>Moonpull AI</h1><p class="mp-title-cn">月之引力</p>'
        '</section>', unsafe_allow_html=True,
    )


def main():
    st.set_page_config(page_title="Moonpull AI · 月之引力", page_icon="🌘", initial_sidebar_state="collapsed")
    render_theme()
    for key, default in {
        "messages": [], "report": "", "report_pdf": None,
        "report_message_count": 0, "failed_prompt": "", "last_error": "", "pdf_failed": False,
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default

    with st.container(key="topbar"):
        brand, settings = st.columns([5, 1])
    with brand:
        st.markdown(
            '<div class="mp-brand"><span class="mp-mark" aria-hidden="true"></span>'
            + ('Moonpull AI · 月之引力' if st.session_state.messages else '')
            + '</div>', unsafe_allow_html=True,
        )
    with settings, st.popover("设置", icon=":material/tune:"):
        st.subheader("连接你的 AI")
        st.caption("默认读取项目目录中的 .env，也可在下方临时配置。")
        api_key = st.text_input(
            "API Key（临时使用，不保存到磁盘）", type="password",
            help="留空时使用环境变量或 .env 中的 OPENAI_API_KEY。",
        ).strip() or os.getenv("OPENAI_API_KEY", "").strip()
        base_url = st.text_input(
            "API 服务地址",
            value=os.getenv("OPENAI_BASE_URL", "").strip() or DEFAULT_BASE_URL,
        ).strip()
        model = st.text_input(
            "模型名称", value=os.getenv("MODEL_NAME", "").strip() or DEFAULT_MODEL,
        ).strip()
        if api_key:
            st.success("API Key 已配置；连接将在首次提问时验证。")
        else:
            st.info("请先配置 API Key。")
        st.divider()
        st.markdown("**使用步骤**\n1. 描述你的目标与资源\n2. 对话了解案例和做法\n3. 生成报告并下载 PDF 或 Markdown")
        st.caption("未接入实时联网检索；案例和数字请核实来源。对话将发送给所选 AI 服务商。")
        st.caption("对话仅保存在当前会话中，未写入数据库；重要内容请下载。")
        if st.button("清空对话与报告", use_container_width=True):
            for key in ("messages", "report", "report_pdf", "report_message_count", "failed_prompt", "last_error", "pdf_failed"):
                del st.session_state[key]
            st.rerun()

    configured = bool(api_key and base_url and model)
    if not st.session_state.messages:
        render_welcome()
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if st.session_state.last_error:
        st.error(st.session_state.last_error)

    prompt = st.chat_input("输入消息", disabled=not configured)
    retry = False
    if st.session_state.failed_prompt:
        st.warning("上次提问未完成，可重试或输入新的问题。")
        st.caption(st.session_state.failed_prompt)
        retry = st.button("重试上次提问", disabled=not configured)
    if prompt or retry:
        question = prompt if prompt else st.session_state.failed_prompt
        with st.chat_message("user"):
            st.markdown(question)
        with st.spinner("Moonpull AI 正在分析…"):
            try:
                reply = chat(
                    [{"role": "system", "content": SYSTEM_PROMPT},
                     *st.session_state.messages, {"role": "user", "content": question}],
                    api_key, base_url, model,
                )
            except Exception as error:
                st.session_state.failed_prompt = question
                st.session_state.last_error = friendly_error(error)
                st.rerun()
            else:
                st.session_state.messages.extend([
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": reply},
                ])
                st.session_state.failed_prompt = ""
                st.session_state.last_error = ""
                st.rerun()

    if st.session_state.messages:
        st.divider()
        if st.button("生成借鉴报告", type="primary", disabled=not configured):
            with st.spinner("正在整理案例与行动建议…"):
                try:
                    report = chat(
                        [{"role": "system", "content": SYSTEM_PROMPT},
                         *st.session_state.messages, {"role": "user", "content": REPORT_PROMPT}],
                        api_key, base_url, model,
                    )
                except Exception as error:
                    st.error(friendly_error(error))
                else:
                    st.session_state.report = report
                    st.session_state.report_message_count = len(st.session_state.messages)
                    st.session_state.report_pdf = None
                    st.session_state.pdf_failed = False
                    try:
                        st.session_state.report_pdf = generate_pdf(report)
                    except Exception:
                        st.session_state.pdf_failed = True
                    st.success("报告已生成。")

    # 独立于生成按钮渲染，下载和其他页面交互不会让报告消失。
    if st.session_state.report:
        st.subheader("Moonpull AI · 借鉴报告")
        if st.session_state.report_message_count != len(st.session_state.messages):
            st.info("这份报告基于较早的对话。可点击“生成借鉴报告”更新。")
        st.markdown(st.session_state.report)
        if st.session_state.pdf_failed:
            st.warning("PDF 导出失败，报告已保留，请先下载 Markdown。")
        col1, col2 = st.columns(2)
        if st.session_state.report_pdf:
            col1.download_button(
                "下载 PDF 报告", data=st.session_state.report_pdf,
                file_name="Moonpull_AI商业借鉴报告.pdf", mime="application/pdf",
                on_click="ignore", use_container_width=True,
            )
        col2.download_button(
            "下载 Markdown 报告", data=st.session_state.report.encode("utf-8"),
            file_name="Moonpull_AI商业借鉴报告.md", mime="text/markdown",
            on_click="ignore", use_container_width=True,
        )


if __name__ == "__main__":
    main()
