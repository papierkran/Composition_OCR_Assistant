# Composition OCR Assistant 项目说明书

## 1. 项目概述

**Composition OCR Assistant**（作文修改助手）是一款面向中小学作文图片批量处理的 PySide6 桌面工具。它能扫描作文文件夹中的图片，调用讯飞手写 OCR 识别文字，生成 Word 文档，并可接入 DeepSeek / OpenAI 等 OpenAI-compatible API 做错别字修正和作文改写。

适用场景：教师批改、教辅资料整理、学生作文数字化归档。

---

## 2. 系统架构

```
┌──────────────────────────────────────────────────────────────┐
│                     Composition OCR Assistant                │
├──────────────────────────────────────────────────────────────┤
│  GUI 层（ocr_gui.py + config_editor_ui.py）                  │
│  ├── 页面一：图片转作文（OCR → Word → AI修正/改写）           │
│  ├── 页面二：文档作文处理（已有 DOCX 后处理流水线）           │
│  └── 页面三：文档 AI 识别处理（纯 AI 分析 DOCX）             │
├──────────────────────────────────────────────────────────────┤
│  核心处理层（ocr_main.py）                                   │
│  ├── 讯飞手写 OCR 识别                                       │
│  ├── 百度图片矫正（可选）                                    │
│  ├── python-docx 文档生成/修改                               │
│  └── LLM 调用（typo_fix / editor）                          │
├──────────────────────────────────────────────────────────────┤
│  客户端层                                                    │
│  ├── llm_client.py（OpenAI-compatible LLM 客户端）          │
│  └── baidu_image_corrector.py（百度文档矫正 API 客户端）    │
├──────────────────────────────────────────────────────────────┤
│  配置层                                                      │
│  ├── config_migrate.py（旧版→新版配置迁移）                  │
│  └── presson.json / config.json                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. 文件结构

```
Composition_OCR_Assistant/
├── ocr_gui.py                  # PySide6 GUI 主程序（主入口）
├── ocr_main.py                 # OCR 与 Word/AI 处理核心逻辑
├── llm_client.py               # OpenAI-compatible LLM 客户端封装
├── config_editor_ui.py         # 配置编辑器 GUI
├── config_migrate.py           # 配置迁移工具（旧版→新版 schema）
├── baidu_image_corrector.py    # 百度文档矫正增强 API 客户端
├── config.json                 # 本地配置文件（空/优先级低于 presson.json）
├── app.ico                     # 应用图标
├── ocr_gui.spec                # PyInstaller 打包配置（GUI）
├── ocr_main.spec               # PyInstaller 打包配置（CLI）
├── LICENSE                     # GPLv3 许可证
│
├── 新文件统一docx格式.py        # 独立工具：DOCX 格式化/批处理/AI修正
├── paddle处理.py               # 基于 PaddleOCR 的离线替代方案
│
├── dist/                       # PyInstaller 打包输出（ocr_gui.exe）
├── build/                      # PyInstaller 构建中间文件
├── 旧版CTK/                    # 旧版 CustomTkinter 代码备份
└── 图片转文档一键处理/          # 独立子项目（UVDoc 深度学习图片矫正）
```

---

## 4. 功能模块详解

### 4.1 页面一：图片转作文（Page OCR）

**用途**：将作文图片批量识别为文字，生成 Word 文档，可选 AI 修正/改写。

#### 流程图

```
┌─────────────┐
│  选择/拖入   │
│  作文文件夹  │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│  扫描路径下子文件 │
│  夹，加载到任务队 │
│  列（只含图片的） │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  点击"开始处理"  │
│  自动读取路径下   │
│  未完成任务       │
└──────┬───────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│         多线程并发处理（默认 3 个）            │
│                                              │
│  ┌─────────────────────────────────────────┐ │
│  │ Step 1: 百度图片矫正（可选）             │ │
│  │  ├── 备份原图到 "旧/" 文件夹            │ │
│  │  ├── 调用百度 doc_crop_enhance API      │ │
│  │  └── 矫正后图片覆盖原图                 │ │
│  └───────────────┬─────────────────────────┘ │
│                  │                           │
│                  ▼                           │
│  ┌─────────────────────────────────────────┐ │
│  │ Step 2: 讯飞手写 OCR 识别               │ │
│  │  ├── 逐张图片发送 base64 到讯飞 API     │ │
│  │  ├── 提取文字行，智能合并自然段          │ │
│  │  └── 生成 Word 文档框架                 │ │
│  └───────────────┬─────────────────────────┘ │
│                  │                           │
│                  ▼                           │
│  ┌─────────────────────────────────────────┐ │
│  │ Step 3: AI 错别字修正（可选）            │ │
│  │  ├── 读取 "修改前" 区域正文              │ │
│  │  ├── 发送到 LLM（typo_fix 任务）        │ │
│  │  ├── 解析返回的 JSON（含元数据+正文）   │ │
│  │  ├── 更新表格：标题/作者/字数/年级等    │ │
│  │  └── 替换 "修改前" 区域内容             │ │
│  └───────────────┬─────────────────────────┘ │
│                  │                           │
│                  ▼                           │
│  ┌─────────────────────────────────────────┐ │
│  │ Step 4: AI 作文改写（可选）              │ │
│  │  ├── 读取修正后正文                      │ │
│  │  ├── 发送到 LLM（editor 任务）          │ │
│  │  ├── 字数监督：自动重试（最多 4 次）    │ │
│  │  └── 写入 "修改后" 区域                 │ │
│  └───────────────┬─────────────────────────┘ │
│                  │                           │
│                  ▼                           │
│  ┌─────────────────────────────────────────┐ │
│  │  任务状态更新到表格                      │ │
│  │  ├── 已完成 → 绿色背景                  │ │
│  │  ├── 失败 → 红色背景                    │ │
│  │  └── 已完成任务跳过，失败任务重新处理    │ │
│  └─────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

#### 配置项

| 配置路径 | 类型 | 说明 | 默认值 |
|---------|------|------|--------|
| `OCR.XFYUN.URL` | string | 讯飞 OCR 接口地址 | `http://webapi.xfyun.cn/v1/service/v1/ocr/handwriting` |
| `OCR.XFYUN.APPID` | string | 讯飞 APPID | - |
| `OCR.XFYUN.API_KEY` | string（密码模式） | 讯飞 API Key | - |
| `OCR.XFYUN.LANGUAGE` | string | 识别语言 | `cn\|en` |
| `OCR.XFYUN.LOCATION` | string | 是否返回位置信息 | `false` |
| `OCR.BAIDU_CORRECTION.ENABLED` | bool | 是否启用百度图片矫正 | `false` |
| `OCR.BAIDU_CORRECTION.API_KEY` | string | 百度 API Key | - |
| `OCR.BAIDU_CORRECTION.SECRET_KEY` | string（密码模式） | 百度 Secret Key | - |
| `LLM.PROVIDERS.{name}.API_KEY` | string（密码模式） | AI Provider API Key | - |
| `LLM.PROVIDERS.{name}.BASE_URL` | string | AI Provider Base URL | - |
| `LLM.PROVIDERS.{name}.MODEL` | string | 模型名称 | `deepseek-chat` |
| `LLM.TASKS.typo_fix.ENABLED` | bool | 启用 AI 错别字修正 | `false` |
| `LLM.TASKS.typo_fix.PROVIDER` | string | 使用的 Provider | `deepseek` |
| `LLM.TASKS.typo_fix.PROMPT` | string | 错别字修正提示词 | 见内置默认 |
| `LLM.TASKS.editor.ENABLED` | bool | 启用 AI 作文改写 | `false` |
| `LLM.TASKS.editor.PROVIDER` | string | 使用的 Provider | `deepseek` |
| `LLM.TASKS.editor.PROMPT` | string | 作文改写提示词 | 见内置默认 |
| `LLM.TASKS.editor.COUNT_MIN` | int\|null | 目标字数下限 | 自动（700-820） |
| `LLM.TASKS.editor.COUNT_MAX` | int\|null | 目标字数上限 | 自动（700-850） |
| `APP.ROOT_DIR` | string | 默认作文文件夹路径 | - |
| `APP.DEBUG` | bool | 调试模式 | `false` |

#### 任务队列表格列

| 列 | 说明 |
|----|------|
| 序号 | 任务编号 |
| 学生姓名 | 从文件夹名解析 |
| 文件路径 | 完整路径 |
| 作文名称 | 从 AI 返回的元数据获取 |
| 修改前字数 | AI 识别的原始字数 |
| 年级 | AI 识别的年级 |
| 线上/线下 | AI 识别的来源 |
| 修改后字数 | AI 改写后的字数 |
| 状态 | 待完成/处理中/已完成/失败 |
| 实时日志 | 当前步骤或处理日志 |

---

### 4.2 页面二：文档作文处理（Page AI）

**用途**：对已有 DOCX 文件执行后处理流水线，支持多步骤组合。

#### 流程图

```
┌─────────────┐
│  选择文件夹  │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│  复制原始文件      │
│  原文件 → "改 xxx" │
└──────┬───────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  按勾选顺序执行以下步骤（可拖动排序）     │
│                                          │
│  ┌────────────────────────────────────┐  │
│  │ 步骤 6: DOC → DOCX 转换           │  │
│  │  调用 LibreOffice soffice 命令行   │  │
│  └────────────────────────────────────┘  │
│                  │                       │
│                  ▼                       │
│  ┌────────────────────────────────────┐  │
│  │ 步骤 1: 清除空格                   │  │
│  │  遍历所有段落 run.text.strip()     │  │
│  └────────────────────────────────────┘  │
│                  │                       │
│                  ▼                       │
│  ┌────────────────────────────────────┐  │
│  │ 步骤 AI: AI 改作文                 │  │
│  │  ├── 读取 DOCX 全文               │  │
│  │  ├── 发送到 LLM                   │  │
│  │  ├── 字数监督重试（最多 4 次）    │  │
│  │  └── 在末尾添加分页 + "修改后"    │  │
│  └────────────────────────────────────┘  │
│                  │                       │
│                  ▼                       │
│  ┌────────────────────────────────────┐  │
│  │ 步骤 2: 添加"修改前/后"标签       │  │
│  │  在文档首行插入"修改前："          │  │
│  │  在末尾添加分页 + "修改后："      │  │
│  └────────────────────────────────────┘  │
│                  │                       │
│                  ▼                       │
│  ┌────────────────────────────────────┐  │
│  │ 步骤 3: 格式化字体段落             │  │
│  │  字体：宋体 12pt                   │  │
│  │  行距：固定值 12pt                 │  │
│  │  首行缩进：0.74cm                  │  │
│  │  段前/段后：0pt                    │  │
│  └────────────────────────────────────┘  │
│                  │                       │
│                  ▼                       │
│  ┌────────────────────────────────────┐  │
│  │ 步骤 5: 修改作者                   │  │
│  │  doc.core_properties.author =      │  │
│  │  "思睿教育_美丽可爱的尹老师"       │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

#### 配置项

| 配置路径 | 类型 | 说明 | 默认值 |
|---------|------|------|--------|
| `LLM.PROVIDERS.{name}.API_KEY` | string（密码模式） | AI Provider API Key | - |
| `LLM.PROVIDERS.{name}.BASE_URL` | string | AI Provider Base URL | - |
| `LLM.PROVIDERS.{name}.MODEL` | string | 模型名称 | `deepseek-chat` |
| `LLM.TASKS.editor.PROMPT` | string | AI 改写提示词 | 见内置默认 |
| `LLM.TASKS.editor.COUNT_MIN` | int\|null | 目标字数下限 | 自动 |
| `LLM.TASKS.editor.COUNT_MAX` | int\|null | 目标字数上限 | 自动 |

**可勾选步骤**（按顺序执行，支持拖动排序）：

| 步骤 ID | 名称 | 功能 |
|---------|------|------|
| 6 | DOC→DOCX 转换 | 调用 LibreOffice 转换旧版 .doc 文件 |
| 1 | 清除空格 | 清除所有段落 run 两端空格 |
| AI | AI 改作文 | 调用 LLM 改写，字数监督重试 |
| 2 | 添加标签 | 添加"修改前："和"修改后："分页标签 |
| 3 | 格式化 | 宋体12pt、固定行距12pt、首行缩进0.74cm |
| 5 | 修改作者 | 设置文档作者为固定值 |

---

### 4.3 页面三：文档 AI 识别处理（Page Doc AI）

**用途**：直接对已有 `.docx` 文件进行 AI 分析、元数据提取和内容改写。

#### 流程图

```
┌─────────────┐
│  选择文件夹  │
│  (含 .docx) │
└──────┬──────┘
       │
       ▼
┌──────────────────────┐
│  递归扫描 .docx 文件  │
│  (排除 "修改后" 文件夹)│
└──────┬───────────────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│         多线程并发处理（默认 3 个）            │
│                                              │
│  ┌─────────────────────────────────────────┐ │
│  │ Step 1: 读取 DOCX 内容                  │ │
│  │  doc.paragraphs → full_text             │ │
│  └───────────────┬─────────────────────────┘ │
│                  │                           │
│                  ▼                           │
│  ┌─────────────────────────────────────────┐ │
│  │ Step 2: AI 识别元数据                    │ │
│  │  ├── 作文标题                            │ │
│  │  ├── 作者                                │ │
│  │  ├── 原文字数                            │ │
│  │  ├── 修改后字数                          │ │
│  │  ├── 年级                                │ │
│  │  ├── 第几次                              │ │
│  │  ├── 线上或线下                          │ │
│  │  ├── 有修改后内容（bool）               │ │
│  │  ├── 修改前正文（纯正文）               │ │
│  │  └── 修改后正文（纯正文）               │ │
│  │  返回 JSON 格式                         │ │
│  └───────────────┬─────────────────────────┘ │
│                  │                           │
│                  ▼                           │
│  ┌─────────────────────────────────────────┐ │
│  │ Step 3: 判断是否有修改后内容             │ │
│  │  ├── 有 → 直接使用 AI 提取的修改后正文  │ │
│  │  └── 无 → 调用 AI 修改作文              │ │
│  │          （支持自定义提示词+字数限制）   │ │
│  └───────────────┬─────────────────────────┘ │
│                  │                           │
│                  ▼                           │
│  ┌─────────────────────────────────────────┐ │
│  │ Step 4: 生成新文档                       │ │
│  │  ├── 格式：修改前（分页）修改后          │ │
│  │  ├── 宋体12pt、固定行距12pt             │ │
│  │  ├── 标题/作者居中                      │ │
│  │  ├── 正文首行缩进0.74cm                 │ │
│  │  └── 保存到 "修改后/" 子文件夹          │ │
│  │     文件名: 改 [标题]——[作者][年级]...  │ │
│  └───────────────┬─────────────────────────┘ │
│                  │                           │
│                  ▼                           │
│  ┌─────────────────────────────────────────┐ │
│  │  更新表格：标题/作者/字数/年级/是否合格 │ │
│  │  字数合格范围：780-930 字               │ │
│  └─────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

#### 配置项

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| Provider | 下拉选择 | AI Provider（deepseek/openai/custom） | `deepseek` |
| API Key | string（密码模式） | Provider API Key | 从配置读取 |
| Base URL | string | API 地址 | 从配置读取 |
| Model | string | 模型名称 | `deepseek-chat` |
| AI 修改提示词 | string | 自定义修改作文的提示词 | 见内置默认 |
| 并发数 | int | 同时处理文件数 | `3` |
| 最少字数 | int | 修改后字数下限 | `780` |
| 最多字数 | int | 修改后字数上限 | `930` |

#### 任务队列表格列

| 列 | 说明 |
|----|------|
| 序号 | 任务编号 |
| 文件路径 | 完整路径 |
| 作文标题 | AI 识别的标题 |
| 作者 | AI 识别的作者 |
| 原文字数 | AI 识别的原始字数 |
| 修改后字数 | AI 改写后的字数 |
| 年级 | AI 识别的年级 |
| 线上/线下 | AI 识别的来源 |
| 是否合格 | 合格(780-930)/不合格/未知 |
| 状态 | 待处理/处理中/完成/失败/跳过 |

---

## 5. 配置系统

### 5.1 配置加载优先级

```
1. D:\person_data\ocer助手\presson.json （个人配置，最高优先级）
2. <exe_dir>/config.json 或 <脚本目录>/config.json
3. 内置默认 DEFAULT_CONFIG
```

- GUI：三级优先，默认返回内置 `DEFAULT_CONFIG`（不会报错）
- CLI（ocr_main.py）：两级优先，找不到有效配置会 `raise RuntimeError`
- 空文件（0字节）的 `config.json` 不会被加载

### 5.2 配置保存优先级

```
1. 如果 presson.json 的父目录存在 → 保存到 presson.json
2. 否则 → 保存到 config.json
```

### 5.3 配置迁移

`config_migrate.py` 中的 `ensure_new_schema()` 负责将旧版配置自动映射到新版结构：

| 旧版字段 | 新版字段 |
|---------|---------|
| `OCR.URL` | `OCR.XFYUN.URL` |
| `OCR.APPID` | `OCR.XFYUN.APPID` |
| `OCR.API_KEY` | `OCR.XFYUN.API_KEY` |
| `DEEPSEEK.API_KEY` | `LLM.PROVIDERS.deepseek.API_KEY` |
| `DEEPSEEK.MODEL` | `LLM.PROVIDERS.deepseek.MODEL` |
| `DEEPSEEK.ENABLED` | `LLM.TASKS.typo_fix.ENABLED` |
| `DEEPSEEK.PROMPT` | `LLM.TASKS.typo_fix.PROMPT` |
| `EDITOR.ENABLED` | `LLM.TASKS.editor.ENABLED` |
| `EDITOR.PROMPT` | `LLM.TASKS.editor.PROMPT` |

迁移只在内存中进行，不会自动覆写磁盘文件。

---

## 6. LLM 客户端

### 6.1 Provider 机制

`llm_client.py` 封装了 OpenAI-compatible 客户端的创建和管理：

```python
ProviderConfig:
  name: str          # Provider 名称（如 deepseek、openai、xai）
  base_url: str      # API 基础地址
  api_key: str       # 认证密钥
  model: str         # 模型名称
  base_urls: list    # 多节点容错列表（可选）
```

### 6.2 任务机制

```python
TaskConfig:
  name: str          # 任务名（typo_fix / editor）
  enabled: bool      # 是否启用
  provider: str      # 使用的 Provider 名称
  prompt: str        # 提示词模板（含 {text} 占位符）
```

### 6.3 容错机制

- `resolve_task_clients()` 返回 `[(base_url, client), ...]` 列表
- 按顺序尝试每个节点，直到成功
- 所有节点失败后抛出最后一个异常

---

## 7. API Key 安全

- 所有 API Key 输入框默认使用 **Password echo mode**（`QLineEdit.Password`）
- 每个 Key 输入框旁都有 **👁 眼睛按钮**，点击可切换显示/隐藏
- 共涉及 7 个密码字段：
  1. 讯飞 OCR API_KEY（页面一）
  2. 百度 API Key（页面一）
  3. 百度 Secret Key（页面一）
  4. AI 错别字修正 API Key（页面一）
  5. AI 修改作文 API Key（页面一）
  6. AI Provider API Key（页面二）
  7. AI Provider API Key（页面三）

---

## 8. 拖放支持

程序支持拖放以下内容：

| 拖入内容 | 行为 |
|---------|------|
| 文件夹 | 切换到"文档AI识别处理"页面，设置路径 |
| `.docx` 文件 | 切换到"文档AI识别处理"页面，直接开始处理 |
| `.png/.jpg/.jpeg/.bmp` 图片 | 切换到"图片转作文"页面，显示提示 |

- 拖入的 `.docx` 文件会自动排除 `~$` 临时文件和 "修改后" 文件夹下的文件

---

## 9. 字数监督机制

AI 作文改写（editor 任务）具有自动字数监督：

```
字数规则：
  原文 ≥ 850 字 → 目标范围：(原文-30, 原文+30)
  原文 ≥ 800 字 → 目标范围：(820, 850)
  原文 < 800 字 → 目标范围：(700, 820)

重试逻辑：
  ├── 第 1 次：正常调用 LLM
  ├── 第 2-4 次：追加字数不符提示，重新调用
  └── 超过 4 次仍不符合 → 抛出 RuntimeError
```

---

## 10. 并发与线程

- **页面一（OCR）**：使用 `ThreadPoolExecutor`，默认 `max_workers=3`
- **页面二（AI）**：顺序执行步骤，步骤内（如 AI 改作文）多文件并发
- **页面三（Doc AI）**：使用 `ThreadPoolExecutor`，默认 `max_workers=3`
- 所有 GUI 更新通过 `Signal` 回到主线程

---

## 11. 输出格式

### 页面一 / 页面三输出

任务文件夹下生成 `修改后/` 子文件夹：

```
任务文件夹/
├── 1.jpg
├── 2.jpg
├── 旧/                    ← 百度矫正备份的原图
├── 任务文件夹名.docx       ← 页面一生成
└── 修改后/
    └── 改 作文标题——作者年级第几次线上线下.docx
```

### Word 文档结构

```
修改前：
  [作文标题]              （居中）
  ——[作者姓名]            （居中）
  [正文段落...]           （首行缩进0.74cm）

————— 分页符 —————

修改后：
  [作文标题]              （居中）
  ——[作者姓名]            （居中）
  [AI修正/改写后的正文...]
```

---

## 12. 独立工具

### 12.1 新文件统一docx格式.py

交互式命令行工具，提供 8 种 DOCX 批处理功能：

```bash
python 新文件统一docx格式.py
```

### 12.2 paddle处理.py

基于 PaddleOCR 的离线 OCR 替代方案，无需联网：

```bash
python paddle处理.py
```

### 12.3 图片转文档一键处理/

使用 UVDoc 深度学习模型进行文档图片矫正的独立子项目。

---

## 13. 运行与打包

### 13.1 安装依赖

```bash
pip install PySide6 python-docx requests openai Pillow
```

可选依赖：

```bash
pip install paddleocr opencv-python torch
```

### 13.2 运行

```bash
python ocr_gui.py
```

### 13.3 命令行模式

```bash
python ocr_main.py <作文文件夹路径>
python ocr_main.py <作文文件夹路径> --config config.json
python ocr_main.py <作文文件夹路径> --no-deepseek
python ocr_main.py <作文文件夹路径> --no-editor
python ocr_main.py <作文文件夹路径> --debug
```

### 13.4 打包为 EXE

```bash
pyinstaller --clean ocr_gui.spec
```

生成文件：`dist/ocr_gui.exe`（约 90MB）

---

## 14. 注意事项

- 讯飞手写 OCR 单张图片大小不要超过接口限制，建议图片清晰、方向正确
- 启用百度图片矫正会改变图片处理流程，建议先用少量样本验证效果
- 启用 AI 错别字修正或作文改写会明显增加处理时间，并消耗对应 API 额度
- 多线程默认并发数为 3；如 API 限流频繁，可在代码中调整 `self.max_parallel_tasks`
- 任务队列状态以 GUI 运行期间为准；重启程序后不会恢复上次队列状态
- 窗口固定 1100×800，不支持动态缩放（适配 4K 屏幕）
- 已完成任务标记为绿色，重新开始时自动跳过；删除任务时清除完成标记
- 所有可折叠区域（百度矫正、OCR配置、运行日志）默认收起
- 任务列表兼具实时日志功能，日志内容直接显示在对应任务行中

---

## 15. License

本项目采用 [GNU General Public License v3 (GPLv3)](LICENSE) 许可证。

仅供学习和教育用途，禁止商业或非法用途。OCR 和 AI API 使用请遵守对应服务商协议。
