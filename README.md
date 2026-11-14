# Moonpull AI · 月之引力

空阔深空主题的个人 AI 商业研究助手，面向一人公司和小团队：查询相关案例、连续追问、生成六部分借鉴报告，并下载中文 PDF 或 Markdown。

## 1. 准备环境

需要 Python 3.11 或更新版本（本次使用 Python 3.12 验证）、可用的网络，以及所选 AI 服务商的 API Key。四个直接依赖已固定为本次验证版本。

进入本项目目录，在终端创建并激活虚拟环境：

macOS / Linux：

```bash
cd moonpull
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Windows PowerShell：

```powershell
cd moonpull
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

如果 Windows 的脚本执行策略阻止激活，无需修改系统策略，直接使用：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 2. 配置 DeepSeek 官方 API

使用文本编辑器打开 `.env`，填写：

```dotenv
OPENAI_API_KEY=你的DeepSeek_API_Key
OPENAI_BASE_URL=https://api.deepseek.com
MODEL_NAME=deepseek-flash
```

默认使用 DeepSeek 官方 API。请在 https://platform.deepseek.com/ 创建可用的 API Key，并确认账号具有所选模型的访问权限和调用额度。虽然变量名叫 `OPENAI_API_KEY`，这里应填入 **DeepSeek 的 Key**。应用通过 OpenAI 兼容 SDK 调用 `https://api.deepseek.com/chat/completions`，模型名称从 `MODEL_NAME` 读取，未设置时使用 `deepseek-flash`。

`deepseek-flash` 按本项目要求作为默认值；如平台提示模型不存在或无权限，请核对 DeepSeek 当前文档和账号可调用的模型名称，再修改 `MODEL_NAME`。若使用 OpenAI，请同步修改这三项：

```dotenv
OPENAI_API_KEY=你的OpenAIKey
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4o-mini
```

使用其他 OpenAI Chat Completions 兼容服务时，填写对应的 Key、接口基础地址和模型名。基础地址不要包含 `/chat/completions`。模型必须支持文本对话和 system 消息；非 Grok 模型还需支持 temperature 参数。Grok 请求使用服务商默认生成参数，不额外指定 temperature。不同服务的模型名称和权限以该服务商文档为准；这不是对所有服务商的兼容性保证。

也可不创建 `.env`，直接在网页右上角“设置”中临时输入这三项。网页配置仅用于当前会话，不写入磁盘。`.env` 按项目目录定位；已有系统环境变量优先于 `.env`，网页填写的配置优先级最高。修改 `.env` 后请重启程序。

从旧版升级时，只需将新版 `app.py`、`.env.example`、`README.md` 复制到原 `moonpull` 目录并替换同名文件，无需重新安装依赖，也不要删除原来的 `.venv`。更新 `.env.example` 不会自动修改你已有的 `.env`，请自行将 `.env` 的三项改为上述 DeepSeek 配置。关闭运行中的 Moonpull 后重新启动，使配置生效。

## 3. 启动并使用

激活虚拟环境后运行：

```bash
streamlit run app.py
```

或使用等效命令：

```bash
python -m streamlit run app.py
```

Windows 未激活虚拟环境时：

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

浏览器通常自动打开；没有自动打开时访问 **http://localhost:8501**。

1. 确认右上角“设置”中已填写 API Key、服务地址和模型名。配置状态仅说明字段已填写，首次提问才会验证连接。
2. 输入具体问题，例如：“我每周有 10 小时，预算 1000 元，想用 AI 做短视频接单。有哪些小团队做法可借鉴？如何获客？”
3. 继续追问成本、交付方式或适配条件。
4. 点击“生成借鉴报告”，再下载 PDF 或 Markdown。生成报告也会调用模型，按服务商规则计费。
5. 新对话产生后，旧报告会提示更新；生成新报告会替换当前报告，已有下载文件不受影响。

终端按 `Ctrl+C` 停止。若 8501 端口已占用，运行 `streamlit run app.py --server.port 8502`，再访问 http://localhost:8502。

## 常见问题

- **没有 streamlit 命令**：检查是否激活了安装依赖的虚拟环境，或使用 `python -m streamlit run app.py`。
- **Key 验证失败**：检查 Key 是否有效，以及是否与服务地址属于同一服务商。
- **限流或额度不足**：检查账号余额、调用配额，稍后重试。
- **连接失败或超时**：确认本机能访问该服务商，检查服务地址；Grok 单次请求超时为 180 秒，其他模型为 60 秒，SDK 最多自动重试一次。
- **模型/请求不受支持**：核对模型名、基础地址和模型对参数的支持。
- **PDF 显示问题**：导出使用 ReportLab 自带的中文 CID 字体定义，不需要 `simsun.ttc`，但字体字形未嵌入文件；若阅读器替代字体不正确，尝试 Adobe Acrobat 等支持中文的阅读器，或使用 Markdown 下载。PDF 保留文本、标题和列表，不完整还原 Markdown 表格或代码块样式。
- **重载网页后对话消失**：本版本只保留当前 Streamlit 会话，不提供跨会话持久化。重要报告请及时下载。

## 信息边界

本版本未接入网页搜索，不会自动验证最新案例和收入数据。提示词要求区分案例、一般做法、当事人自述和推测，并保留来源缺口。生成报告不会把对话中的说法自动升级为事实。

对话会发送给你选择的 AI 服务商。`.env` 已列入 `.gitignore`，不要将真实 Key 放入代码、截图或分享的压缩包。本工具按个人本地使用设计。

## 项目文件

- `assets/`：离线可用的星空背景和界面样式，无需下载外部图片或字体。
- `.streamlit/config.toml`：深色主题设置。
- `app.py`：Streamlit 页面、接口调用、会话管理、错误处理和报告导出。
- `prompts.py`：已优化的日常研究提示词与六部分报告提示词。
- `requirements.txt`：运行依赖。
- `.env.example`：配置示例，复制为 `.env` 后填写真实 Key。
- `.gitignore`：排除真实配置、虚拟环境和缓存。

## 新版界面

品牌显示为 **Moonpull AI · 月之引力**。首页只保留“Moonpull AI”“月之引力”和“设置”文字；中文副标题置于英文名下方、字号更小。深空背景采用已确认的小地球、小月球与细引力轨迹构图，保留大量空阔星空与无占位文案的聊天输入区；设置入口收进右上角，不再占用常驻侧栏。桌面和手机均已检查。下载安装新版即可，无需先安装旧版。

## 本次验证

已验证 Python 语法、Streamlit 启动、浏览器页面，以及使用本地模拟 OpenAI 兼容接口的对话、报告、下载和失败重试流程。未使用你的真实 API Key 调用付费模型；真实服务的连通性、权限和回答质量将在你配置 Key 后验证。
