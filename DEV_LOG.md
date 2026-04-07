# 开发日志

> 新会话接手这个项目时，先读 `PROJECT_MEMORY.md`，再读这份 `DEV_LOG.md`。

## 2026-03-28

### 本次目标

- 降低 `goodjob` 在批量打招呼时对本地 `Ollama` 的依赖。
- 保持 Boss 侧现有页面元素解析逻辑不变，不新增选择器依赖。
- 保持前端脚本与后端接口兼容，尽量只替换匹配逻辑。

### 现状判断

- 现有脚本会从 Boss 职位详情页获取：
  - 岗位标题
  - 薪资范围
  - 职位描述正文
- 前端会把这些内容拼成一段文本，请求后端 `/get-job-score`。
- 原来的后端 `calcJobScore()` 会调用本地 `Ollama` 计算匹配度，再由前端用阈值判断是否投递。
- 用户当前的真实使用场景主要是“批量打招呼”，不依赖复杂回复能力。

### 本次修改

- 修改了 [core.py](C:/Users/czc/Desktop/czc_code/goodjob/core.py)：
  - 保留 `calcJobScore(job, resume)` 接口不变。
  - 去掉岗位匹配度里的大模型计算逻辑。
  - 新增基于文本分段的字段提取逻辑，从请求文本中取出“岗位标题”和“职位描述”。
  - 新增关键词命中函数。
  - 改为：
    - 岗位标题命中关键词，返回 `100`
    - 职位描述命中关键词，返回 `100`
    - 否则返回 `0`
- 修改了 [config.py](C:/Users/czc/Desktop/czc_code/goodjob/config.py)：
  - 新增 `title_keywords`
  - 新增 `detail_keywords`
  - 后续可以直接在这里维护匹配词库

### 设计取舍

- 没有修改 `web_script.js` 的页面解析逻辑。
- 没有新增 Boss 页面元素依赖。
- 没有改变 `/get-job-score` 的接口路径和返回结构。
- 这样前端原有 `score >= OPTIONS.thread` 的投递判断可以继续工作。
- 当前实现本质上已经不是“打分”，而是“命中即通过”。

### 当前行为

- 只要岗位标题命中配置关键词，就会直接进入投递流程。
- 如果标题没命中，但职位描述正文命中配置关键词，也会进入投递流程。
- 如果标题和正文都没命中，则不会投递。

### 当前已知限制

- `getTags`、`getIntroduce`、`reply`、`isNeedResume`、`isNeedWorks` 这些接口仍然保留了大模型依赖。
- 如果后续只保留“批量打招呼”用途，可以继续去掉这些接口对应的模型调用。
- 终端里查看部分中文文件会出现乱码，这是编码显示问题，不等于源码本身损坏。

### 后续建议

- 如果目标只是批量打招呼，可以继续做第二轮精简：
  - 固定搜索关键词，不再依赖 `/tags`
  - 固定打招呼文案，不再依赖 `/get-introduce`
  - 关闭自动聊天回复逻辑
  - 这样可以把本地大模型依赖进一步压缩到接近零
- 需要调整匹配范围时，优先改 [config.py](C:/Users/czc/Desktop/czc_code/goodjob/config.py) 中的关键词列表。

### 本次验证

- 已执行 `py_compile`，`core.py` 与 `config.py` 语法通过。
- 已用英文关键词样例验证：
  - 命中标题关键词时返回 `100`
  - 未命中时返回 `0`

## 2026-03-28 网申跳过修复

### 问题

- Boss 职位列表里混入了国企/校招网申岗位。
- 这类岗位的主按钮不是“立即沟通”，而是“立即网申”之类的入口。
- 原脚本默认所有可投岗位都能进入聊天页，因此遇到网申岗位时会卡在投递链路中，导致整个批量流程停住。

### 修改策略

- 只改 [web_script.js](C:/Users/czc/Desktop/czc_code/goodjob/web_script.js)。
- 不新增 Boss 页面元素依赖，只复用现有的 `STARTCHAT` 按钮元素。
- 采用两层保护：
  - 主动识别：详情页读取按钮文案，不是“立即沟通”就直接标记跳过
  - 超时兜底：详情回传超时或打招呼回执超时，也直接跳过

### 本次修改

- 在 [web_script.js](C:/Users/czc/Desktop/czc_code/goodjob/web_script.js) 的 `OPTIONS` 中新增：
  - `detailTimeout`
  - `greetTimeout`
- 在详情页 `getJobInfo()` 中新增：
  - `actionText`
  - `skip`
  - `skipReason`
- 跳过条件：
  - 找不到开始沟通按钮
  - 按钮文案不是“立即沟通”
  - 缺少聊天链接或加聊天列表链接
- 在搜索页 `getJobInfo()` 中新增详情获取超时处理：
  - 超时后返回 `skip: true`
- 在搜索页主循环中新增：
  - 如果岗位被标记为 `skip`，记录原因并直接进入下一个岗位
- 在搜索页打招呼流程中新增：
  - `pendingGreetTimer`
  - 如果打开聊天页后超过 `greetTimeout` 仍未收到回执，则记录超时并跳过
  - 正常收到打招呼成功/失败回执时清理超时定时器

### 预期效果

- 普通可聊天岗位继续按原流程执行。
- “立即网申”岗位会被直接跳过，不再把脚本卡死。
- 即使 Boss 页面结构或跳转链路偶发异常，也会因超时机制自动恢复到下一个岗位。

### 本次验证

- 已执行 `node --check web_script.js`，语法通过。

## 2026-03-29 后端匹配日志增强

### 问题

- 测试筛选逻辑时，后端终端里只能看到接口被调用，缺少可读的匹配结果日志。
- 用户无法直接判断某个岗位是“命中过滤词后通过”，还是“未命中后跳过”。

### 本次修改

- 修改了 [core.py](C:/Users/czc/Desktop/czc_code/goodjob/core.py)：
  - 新增 `evaluateJobMatch(job)`，返回匹配明细
  - 明细包括：
    - `title`
    - `matched_field`
    - `keyword`
    - `score`
- `calcJobScore()` 改为复用 `evaluateJobMatch()` 的结果，保持原有返回分数逻辑不变
- 修改了 [main.py](C:/Users/czc/Desktop/czc_code/goodjob/main.py)：
  - `/get-job-score` 在返回前会打印结构化终端日志
  - 日志内容包括：
    - 时间
    - 岗位标题
    - 命中位置（岗位名称 / 职位描述 / 未命中）
    - 命中关键词
    - 最终分数

### 终端日志示例

- `[2026-03-29 09:57:21] /get-job-score | title=Java开发 | matched=未命中 | keyword=无 | score=0`
- `[2026-03-29 09:57:30] /get-job-score | title=运维开发 | matched=岗位名称 | keyword=运维 | score=100`

### 本次验证

- 已执行 `py_compile`，`main.py` 与 `core.py` 语法通过。
- 已本地调用 `get_job_score()`，确认终端会打印匹配日志，接口返回结构仍为 `{'score': ...}`。

## 2026-03-29 关键词加权算法替代大模型打分

### 目标

- 不再使用“大模型判断岗位匹配度”。
- 用纯规则算法替代，保留现有 `/get-job-score` 接口和前端阈值判断。
- 让岗位标题成为主判断信号，职位描述只做辅助。
- 尽量贴近 `运维 / 运维开发 / DevOps / SRE / 平台工程` 岗位。

### 新算法

- 第一步：标题负向拦截
  - 标题命中这些词直接 `score = 0`
  - 例如：`java`、`前端`、`后端`、`管培生`、`项目经理`、`数据开发`、`销售`
- 第二步：标题高权重打分
  - `title_strong_keywords`
  - `title_medium_keywords`
  - 只取最高一档，不叠加
- 第三步：职位描述辅助加分
  - `detail_infra_keywords`
  - `detail_support_keywords`
  - 并分别设置封顶，避免正文泛词抬分过高
- 第四步：职位描述负向扣分
  - 例如：`spring boot`、`react`、`vue`、`客户`、`销售`、`光伏`
- 第五步：组合加分
  - 标题命中强关键词且正文命中多个基础设施词，再加分
  - `DevOps/SRE` 与 `k8s/docker/prometheus` 同时出现时，再加分
- 第六步：标题缺失时强制封顶
  - 如果标题没有命中正向关键词，则最终分数最多 `55`
  - 这样正文里的 `python/shell/监控/部署` 不会单独把岗位抬过投递阈值

### 代码变更

- 修改了 [config.py](C:/Users/czc/Desktop/czc_code/goodjob/config.py)
  - 删除原来的简单 `title_keywords` / `detail_keywords`
  - 新增：
    - `title_negative_keywords`
    - `title_strong_keywords`
    - `title_medium_keywords`
    - `detail_infra_keywords`
    - `detail_support_keywords`
    - `detail_negative_keywords`
- 修改了 [core.py](C:/Users/czc/Desktop/czc_code/goodjob/core.py)
  - `evaluateJobMatch()` 现在返回完整打分明细
  - `calcJobScore()` 改为返回这套规则算法的最终分数
- 修改了 [main.py](C:/Users/czc/Desktop/czc_code/goodjob/main.py)
  - 终端日志新增：
    - `title_score`
    - `detail_score`
    - `combo_score`
    - `penalty_score`
    - `reason`

### 预期效果

- `DevOps / SRE / 运维工程师 / 运维开发 / 平台工程` 更容易过线
- `Java开发 / 前端开发 / 管培生 / 项目经理 / 数据开发` 更容易被拦掉
- 正文里偶然出现 `python/shell/监控` 的非目标岗位，不会再轻易被误投

### 本次验证

- 已执行 `py_compile`，`config.py`、`core.py`、`main.py` 语法通过。
- 已本地样例验证：
  - `DevOps / SRE` 返回高分

## 2026-03-31 固定大招呼语更新

### 本次目标

- 将批量打招呼使用的自我介绍固定为新的大招呼语，不再依赖运行时临时生成。
- 保持前端 `web_script.js` 现有调用方式不变，继续通过 `/get-introduce` 获取文案。
- 同时检查已有 `cache.json` 是否需要手动刷新，避免重启前后文案不一致。

### 本次修改

- 修改了 [cache.py](C:/Users/czc/Desktop/czc_code/goodjob/cache.py)
  - 新增 `FIXED_INTRODUCE`
  - `cache.introduce` 改为固定返回该文案
  - 保留 `character`、`tags` 的原有缓存逻辑
  - 启动时如果发现 `cache.json` 中的 `introduce` 不是新文案，会自动回写为最新版本
- 手动更新了 [cache.json](C:/Users/czc/Desktop/czc_code/goodjob/cache.json)
  - 让当前缓存里的 `introduce` 直接切换到新版本
  - 避免未重启前或缓存未重建时继续拿到旧文案

### 当前固定招呼语

- 您好，我有 AI 应用开发、自动化流程、Linux 运维和工程排障经验，也长期使用 Codex、Claude Code 等 Agent 工具辅助开发和解决实际问题。最近一段时间我也在重点研究和使用 OpenClaw（龙虾），已经把它用到技能开发、工作流串联、定时触发和主动执行这类场景里，实际提升了效率和任务闭环能力，想和您进一步沟通一下这个岗位。

### 兼容性说明

- 前端脚本仍然通过 `/get-introduce` 获取文案，无需修改 `web_script.js`。
- 只要后端重启，接口就会稳定返回新的固定招呼语。
- 即使本次未重启，由于 `cache.json` 已手动更新，读取旧缓存时也会拿到新文案。

### 本次验证

- 已执行 `python3 -m py_compile cache.py core.py main.py config.py schema.py`，语法通过。
- 已确认 `web_script.js` 中的打招呼流程依然从 `/get-introduce` 读取文案。
- 当前环境缺少 `ollama` Python 依赖，无法在此直接完整启动后端验证运行态；但从代码路径上看，本次修改不会新增额外依赖。
  - `Java开发 / 项目经理 / 管培生` 返回低分或 `0`
  - `资深后端开发工程师` 即使正文有 `python/shell/监控/部署`，也只会得到较低分数，不会达到投递阈值

## 2026-04-06 项目记忆文件落地

### 本次目标

- 把这个项目的长期背景与开发记录固定到项目目录里。
- 避免后续新会话只靠工作区全局记忆回忆，降低接手成本。
- 保持文件数量克制，不在项目里散着新增一堆说明文件。

### 本次处理

- 确认项目目录里原本已经存在 `DEV_LOG.md`。
- 因此本次没有再新建更多日志文件。
- 新增了 `PROJECT_MEMORY.md`，用于承接长期有效的项目记忆。
- 同时在本文件开头补了一行提示：新会话应先读 `PROJECT_MEMORY.md`，再读 `DEV_LOG.md`。

### 写入 `PROJECT_MEMORY.md` 的核心内容

- 项目路径
- 项目原始定位（AI 找工作 / 依赖 Ollama / 含聊天能力）
- 当前已经明确收缩后的目标：
  - 规则匹配
  - 固定打招呼
  - 收到 Boss 消息后直接发简历
  - 不继续自动聊天
- 当前长期方向：
  - 规则驱动
  - 用户配置驱动
  - 无模型运行时依赖
- 之前已经确认过的关键实现状态：
  - 岗位匹配去大模型化
  - AI 岗位关键词增强
  - 聊天页检测到消息后直接发简历
  - 固定招呼语 / tags 放入缓存层
  - 搜索后先等待 10 秒再开始正式投递
  - `start_backend.bat` 处理过 Ollama 依赖
  - `web_script.js` 的部分预加载参数已抽前配置

### 后续维护规则

- `PROJECT_MEMORY.md`：只写长期有效信息
- `DEV_LOG.md`：持续记录每次开发过程
- 除非老板明确要求，否则不要再为这个项目额外扩散出更多“说明类 Markdown 文件”

### 备注

从这次开始，这两份文件作为这个项目的主记忆入口：
- `PROJECT_MEMORY.md`
- `DEV_LOG.md`

## 2026-04-06 主链去除 Ollama 启动硬依赖 + 前端脚本清理

### 本次目标

- 修复 `web_script.js` 中已确认的明显 bug 与残留脏代码。
- 收口后端对 `ollama` 的启动期硬依赖，确保当前主链可以在未安装 `ollama` 时启动。
- 把本次变更同步写入项目文档，便于后续接手。

### 本次修改

- 修改了 [web_script.js](C:/Users/czc/Desktop/czc_code/goodjob/web_script.js)
  - 将聊天页里计算岗位分数时的 `jobInfo.deatil` 改为 `jobInfo.detail`
  - 删除了 `else (t.indexOf())` 非法残段
  - 保持原有 `needResume = 2` 判定逻辑不变，只去掉无效脏代码

- 修改了 [core.py](C:/Users/czc/Desktop/czc_code/goodjob/core.py)
  - 将 `from ollama import chat, Message` 改为可选导入
  - 新增 `__ensure_ollama_available()`，仅在旧聊天相关接口真正被调用时才检查 `ollama`
  - 保持岗位规则评分 `evaluateJobMatch()` 及其主链调用方式不变
  - 这样即使当前环境未安装 `ollama`，只要走主链：
    - 固定 `tags`
    - 固定 `introduce`
    - 规则打分
    - 收到新消息直接发简历
    也可以正常启动后端

- 修改了 [PROJECT_MEMORY.md](C:/Users/czc/Desktop/czc_code/goodjob/PROJECT_MEMORY.md)
  - 记录“主链启动不应被 `ollama` 安装状态阻塞”这一长期运行规则
  - 记录后端已采用兼容式降级，而非激进删除旧接口

### 本次验证

- 已执行 `python3 -m py_compile cache.py config.py core.py main.py prompts.py schema.py tools.py`，语法通过。
- 已执行 `node --check web_script.js`，脚本语法通过。
- 当前环境缺少 `pydantic`，因此无法直接完成项目完整运行态导入验证；报错为 `ModuleNotFoundError: No module named 'pydantic'`，不是 `ollama` 导致。
- 已通过临时最小 `pydantic` 桩执行定向验证：
  - `PYTHONPATH="/tmp/goodjob_test_stub:$PYTHONPATH" python3 -c "import core; print('core import ok without ollama'); print(core.evaluateJobMatch('AI应用开发\\n8-12K\\n职位描述\\n负责 AI agent、workflow、linux 自动化与部署')['score'])"`
  - 输出为：
    - `core import ok without ollama`
    - `100`
  - 说明 `core.py` 已不再因顶层 `ollama` 导入而阻塞，规则评分主链可在无 `ollama` 条件下正常导入并执行。

### 风险与备注

- `/reply`、`/is-need-resume`、`/is-need-works` 这几条历史聊天接口仍然保留；如果在未安装 `ollama` 的环境里主动调用，当前会抛出明确的运行时错误。
- `requirements.txt` 里仍保留 `ollama` 依赖，当前没有删除，目的是不激进破坏历史安装方式；真正做到“默认安装集也去掉 `ollama`”可后续再单独收口。

## 2026-04-06 旧聊天接口错误语义收口

### 本次目标

- 继续收紧主链与旧聊天链的边界。
- 避免遗留聊天接口在缺少 `ollama` 时直接抛出 500，让前端或调用方更容易判断这是“旧能力暂不可用”，不是主链挂了。

### 本次修改

- 修改了 [main.py](C:/Users/czc/Desktop/czc_code/goodjob/main.py)
  - 为 `/reply`
  - `/is-need-resume`
  - `/is-need-works`
  这三个历史聊天相关接口加了 `RuntimeError -> HTTP 503` 的转换
  - 这样当环境未安装 `ollama` 且误调用这些旧接口时，会返回明确的不可用状态，而不是 500

- 修改了 [core.py](C:/Users/czc/Desktop/czc_code/goodjob/core.py)
  - 新增 `LEGACY_OLLAMA_REQUIRED_MESSAGE`
  - 新增 `isOllamaAvailable()`
  - 统一了旧接口缺少 `ollama` 时的报错信息来源

- 修改了 [PROJECT_MEMORY.md](C:/Users/czc/Desktop/czc_code/goodjob/PROJECT_MEMORY.md)
  - 补充记录：旧接口在缺少 `ollama` 时，应返回明确的 503，而不是模糊 traceback

### 本次验证

- 已执行 `python3 -m py_compile cache.py config.py core.py main.py prompts.py schema.py tools.py`，语法通过。
- 当前环境仍缺少 `pydantic`，因此无法在这里完整启动 FastAPI 运行态做接口响应实测；但从代码路径看，这次只是在既有 `RuntimeError` 外层补了 HTTP 语义转换，不影响主链评分接口。

### 风险与备注

- `web_script.js` 当前主链并不会调用这三条旧聊天接口，所以这次修改主要是为了让遗留能力在误调用时更好诊断。
- 是否彻底移除这些旧接口，后续可以等主链稳定后再决定，不急着现在动刀。

## 2026-04-06 主链运行验证（Windows 实际环境）

### 本次目标

- 不只做语法检查，而是在老板电脑的实际 Python 环境里把后端拉起来。
- 验证当前主链最关键的三个接口是否真的能跑通：
  - `/tags`
  - `/get-introduce`
  - `/get-job-score`

### 本次验证方式

- 使用 Windows 侧 Python：`C:\Users\czc\miniconda3\python.exe`
- 在项目目录直接启动：`main.py`
- 后端成功启动后，用本机 `127.0.0.1:8000` 实际请求接口验证

### 本次验证结果

- 后端已成功启动，`uvicorn` 正常监听 `http://0.0.0.0:8000`
- `GET /tags` 返回正常：
  - `{"tags":["AI应用开发"]}`
- `GET /get-introduce` 返回正常：
  - 固定招呼语已正确返回
- `POST /get-job-score` 返回正常：
  - 使用 AI 应用开发样例岗位请求，返回 `{"score":100}`
- 服务端日志中也打印出了岗位评分日志，说明主链打分路径已实际跑通

### 结论

- 当前 `goodjob` 主链已经不只是“代码看起来对”，而是已经在老板电脑的实际 Python 环境中跑通了一次后端核心链路。
- 至少从后端角度看，当前这几项已经实测可用：
  - 固定 tags
  - 固定 introduce
  - 规则评分接口

### 风险与备注

- 这次验证的是后端核心链路，不包含 Boss 网页端的完整页面联动实测。
- 聊天页“检测新消息后直接发简历”的整链仍需放到真实 Boss 页面里继续验证。

## 2026-04-06 前端真实投递链路实测通过

### 本次结果

- 老板已在真实 Boss 前端页面完成实测。
- 当前前端联动链路已确认没有问题。
- 当前项目已经能够正常投简历。

### 这条验证意味着什么

结合前面的后端主链验证结果，可以认为当前 `goodjob` 已至少完成了这一版核心闭环验证：
- 后端可启动
- 固定 `tags` 正常
- 固定 `introduce` 正常
- 规则评分接口正常
- 前端实际投递链路正常
- 可正常投简历

### 后续建议

- 下一步如果继续收口，应优先考虑整理和裁剪旧聊天相关历史逻辑，而不是再怀疑当前投递主链是否能跑。

## 2026-04-07 手动筛选版自动下一轮 + 预加载轻点岗位卡片

### 本次目标

- 基于当前已验证可用的投递主链，新增“本轮结束后自动开始下一轮”的能力。
- 保留老板现有使用习惯：每轮仍手动选择城市 / 薪资 / 工作经验。
- 在预加载滚动过程中，保守增加“偶尔轻点左侧岗位卡片”的动作，尝试让页面更像人工操作并帮助岗位继续稳定加载。

### 本次修改

- 修改了 [web_script.js](C:/Users/czc/Desktop/czc_code/goodjob/web_script.js)
  - 新增每轮相关配置：
    - `manualFilterWaitMs`
    - `roundRestartDelayMs`
    - `maxEmptyRounds`
  - 新增预加载相关配置：
    - `preloadActivateCardEvery`
    - `preloadActivateCardWaitMs`
  - 搜索页主流程从“一次性单轮执行”改成了“可自动续下一轮”的结构：
    - 抽出 `startRound()`
    - 本轮耗尽后自动进入下一轮
    - 每轮都会重新搜索并再次给老板预留手动筛选时间
  - 新增会话级岗位去重：
    - 同一轮运行里已经处理过的岗位 href，不再重复处理
  - 新增空转保护：
    - 连续多轮没有拿到新岗位时自动停止，避免无限空刷
  - 在预加载流程里新增“轻点左侧岗位卡片”：
    - 每隔若干轮滚动，尝试点击当前可见的一条左侧岗位卡片
    - 如果失败，则自动回退为纯滚动，不打断主流程

### 当前设计结果

- 当前流程已从：
  - 搜索一次
  - 手动筛选一次
  - 投完结束
  改成：
  - 搜索
  - 每轮手动筛选
  - 自动投递
  - 自动进入下一轮
  - 连续空轮后自动停止

### 本次验证

- 已执行 `node --check web_script.js`，语法通过。
- 已执行 `python3 -m py_compile cache.py config.py core.py main.py prompts.py schema.py tools.py`，Python 语法通过（仅有 `tools.py` 老正则写法的 `SyntaxWarning`，非本次新增问题）。

### 风险与备注

- “预加载时轻点左侧岗位卡片”属于保守增强，是否真的能带来更稳定加载或更低风控，还需要老板在真实 Boss 页面继续实测。
- 当前没有实现自动选择全国 / 深圳 / 应届生 / 10-20K / 20-50K；这次仍然保留每轮 10 秒手动筛选。

## 2026-04-07 岗位评分延迟调整

### 本次修改

- 修改了 [config.py](C:/Users/czc/Desktop/czc_code/goodjob/config.py)
  - 先将岗位评分基础延迟从 `5000ms` 下调到 `2000ms`
  - 随后按老板要求回调到 `4000ms`
  - 随机抖动保持为 `500ms`

### 当前效果

- 现在每次岗位匹配度计算的实际等待时间，大致会落在：
  - `3.5s ~ 4.5s`
- 比最早的 5 秒级略快，但比 2 秒档更稳一点，方便继续前端实测。

## 2026-04-07 岗位评分算法二次收敛

### 本次问题

- 实测日志显示，当前标题负向拦截过于一刀切。
- `AI应用全栈工程师`、`AI Agent后端开发工程师` 这类其实可能有价值的岗位，会因为标题里出现 `全栈`、`后端` 被直接打成 `0` 分。
- 但 `算法`、`模型研发`、`管培生` 这类岗位，继续强拦截仍然合理。

### 本次修改

- 修改了 [config.py](C:/Users/czc/Desktop/czc_code/goodjob/config.py)
  - 原 `title_negative_keywords` 拆成两层：
    - `title_block_keywords`：继续直接拦截
    - `title_penalty_keywords`：只扣分，不直接拦截
  - 将下列词改为弱负向扣分：
    - `java`
    - `前端`
    - `后端`
    - `全栈`
  - 保留以下方向为强负向直接拦截：
    - `管培生`
    - `算法`
    - `模型研发`
    - `训练`
    - `微调`
    - `光伏`
    - 等其他明显不对口方向

- 修改了 [core.py](C:/Users/czc/Desktop/czc_code/goodjob/core.py)
  - 标题先检查 `title_block_keywords`
  - 命中强负向时仍直接返回 `0`
  - 弱负向词不再提前终止，而是进入 `title_penalty_score` 扣分逻辑
  - 最终分数改为：
    - `title_score + detail_score + combo_score - title_penalty_score - penalty_score`
  - 返回结构中新增：
    - `title_penalty_score`
    - `title_penalty_matches`

- 修改了 [main.py](C:/Users/czc/Desktop/czc_code/goodjob/main.py)
  - 日志新增输出 `title_penalty_score`
  - 方便区分“被直接拦截”还是“保留机会但被扣分”

### 预期效果

- `AI Agent后端开发工程师` 不会再因为 `后端` 被直接打成 `0`
- `AI应用全栈工程师` 不会再因为 `全栈` 被直接误杀
- `纯前端 / 纯 Java / 纯后端` 岗位仍会因为扣分而维持低分
- `AI算法工程师 / AI大模型研发 / AI管培生` 仍会继续被强拦截

## 2026-04-07 岗位评分算法三次收敛

### 本次问题

- 二次收敛后，`AI工程师`、`AI产品经理`、`Python工程师（AI视频工作流方向）` 等岗位仍较容易直接到 `100`，排序区分度不足。
- `AI技术培训生` 这类岗位仍会拿到偏高分，说明“培训生”类词还没被拦住。
- `人工智能应用工程师` 这类中文标题写法覆盖不足，容易只靠职位描述给低分。

### 本次修改

- 修改了 [config.py](C:/Users/czc/Desktop/czc_code/goodjob/config.py)
  - 在强负向标题词中补充：
    - `培训生`
    - `储备干部`
    - `储干`
  - 将标题强匹配分值从原先过于容易顶满的 `100` 档，整体回调到更有梯度的 `80~88` 区间
  - 补充中文 AI 应用方向标题词：
    - `人工智能应用`
    - `人工智能工程师`
    - `人工智能产品`
    - `AI工作流`
    - `工作流工程师`

### 预期效果

- `AI技术培训生` 这类岗位会被直接压到 `0`
- `人工智能应用工程师` 不会再只靠正文给低分
- `AI工程师`、`AI产品经理`、`AI应用工程师` 之间会拉开一些层次，不再动不动满分
- 真正高分岗位应更多表现为：标题强命中 + 正文也有支撑，而不是只靠标题词直接封顶

## 2026-04-07 开源前清理与用户配置外置化（初版）

### 本次目标

- 为后续上传 GitHub 先做一轮公开化清理。
- 把明显带个人色彩的固定文案、关键词和本机启动路径抽离出去。
- 降低新用户第一次上手时必须改代码的门槛。

### 本次修改

- 修改了 [.gitignore](C:/Users/czc/Desktop/czc_code/goodjob/.gitignore)
  - 新增忽略：
    - `user_config.json`
    - `server.out.log`
    - `server.err.log`
    - `goodjobs.zip`
    - `.codex`
    - `DEV_LOG.md`
    - `PROJECT_MEMORY.md`
  - 继续忽略：
    - `resume.md`
    - `resume-lock.md`
    - `cache.json`

- 新增了 [user_config.example.json](C:/Users/czc/Desktop/czc_code/goodjob/user_config.example.json)
  - 把这些用户定制项抽成模板：
    - `resume_name`
    - `think_model`
    - `chat_model`
    - `introduce`
    - `character`
    - `tags`

- 修改了 [config.py](C:/Users/czc/Desktop/czc_code/goodjob/config.py)
  - 新增 `DEFAULT_USER_CONFIG`
  - 新增 `load_user_config()`
  - 改为优先读取 `user_config.json`
  - 让以下字段不再硬编码在代码里：
    - 简历文件名
    - 模型名
    - 固定打招呼语
    - 固定角色风格
    - 固定搜索关键词
  - 同时移除了带明显个人项目痕迹的 `openclaw` / `龙虾` 评分关键词

- 修改了 [cache.py](C:/Users/czc/Desktop/czc_code/goodjob/cache.py)
  - 不再使用 `FIXED_INTRODUCE` / `FIXED_TAGS` / `FIXED_CHARACTER`
  - 改为统一从 `Config` 读取用户配置

- 重写了 [readme.md](C:/Users/czc/Desktop/czc_code/goodjob/readme.md)
  - 去掉旧仓库地址和原项目说明
  - 改成更适合公开仓库的通用说明

- 重写了 [start_backend.bat](C:/Users/czc/Desktop/czc_code/goodjob/start_backend.bat)
  - 去掉本机硬编码 Python 路径
  - 改为直接使用环境里的 `python`

- 重写了 [resume-example.md](C:/Users/czc/Desktop/czc_code/goodjob/resume-example.md)
  - 改成更完整的通用简历模板

### 当前状态

- 现在适合公开放进仓库的内容，基本都已切到更通用的形态。
- 仍保留在本地但不建议公开提交的内容，已通过 `.gitignore` 隔离：
  - 本人简历
  - 本地缓存
  - 项目内部记忆
  - 运行日志
  - 本地辅助文件

### 下一步建议

- 把 `web_script.js` 里的 `OPTIONS` 再抽成前端配置对象或接口下发配置。
- 把 `config.py` 里的评分关键词继续拆成可切换的 profile 配置文件。
- 让新用户先改配置文件，而不是先改源码。

## 2026-04-07 统一配置文件收口（第一阶段完成）

### 本次目标

- 把用户差异化配置尽量收拢到一个配置文件里。
- 让前端运行参数不再继续只写死在 `web_script.js`。
- 保持现有主链尽量不坏，并保留回退逻辑。

### 本次修改

- 重构了 [config.py](C:/Users/czc/Desktop/czc_code/goodjob/config.py)
  - 将默认配置扩展为完整结构：
    - 顶层基础字段：
      - `resume_name`
      - `think_model`
      - `chat_model`
      - `introduce`
      - `character`
      - `tags`
    - `backend`
      - `job_score_delay_base_ms`
      - `job_score_delay_jitter_ms`
    - `frontend`
      - `serverHost`
      - `resumeIndex`
      - `thread`
      - `timestampTimeout`
      - `onlyGreet`
      - `manualFilterWaitMs`
      - `roundRestartDelayMs`
      - `maxEmptyRounds`
      - `detailTimeout`
      - `greetTimeout`
      - `preloadScrollPixels`
      - `preloadScrollWaitMs`
      - `preloadStableRoundsLimit`
      - `preloadMaxRounds`
      - `preloadActivateCardEvery`
      - `preloadActivateCardWaitMs`
    - `scoring`
      - `title_block_keywords`
      - `title_penalty_keywords`
      - `title_strong_keywords`
      - `title_medium_keywords`
      - `detail_infra_keywords`
      - `detail_support_keywords`
      - `detail_negative_keywords`
  - 新增深合并逻辑 `_deep_merge()`
  - 新增旧字段兼容逻辑 `_apply_legacy_compat()`，避免旧版 `user_config.json` 直接失效
  - 新增 `Config.get_client_config()`，用于统一下发前端配置

- 修改了 [main.py](C:/Users/czc/Desktop/czc_code/goodjob/main.py)
  - 新增接口：
    - `GET /client-config`
  - 用于向前端统一下发：
    - `introduce`
    - `character`
    - `tags`
    - `frontend`

- 修改了 [web_script.js](C:/Users/czc/Desktop/czc_code/goodjob/web_script.js)
  - 新增 `api.getClientConfig()`
  - 启动时优先请求 `/client-config`
  - 若成功：
    - 用返回值覆盖前端 `OPTIONS`
    - 直接读取 `tags`
    - 直接读取 `introduce`
  - 若失败：
    - 回退到旧接口 `/tags` 与 `/get-introduce`
  - 这样做的目的是先打通统一配置主链，同时不把旧流程一次性硬切坏

- 修改了 [user_config.json](C:/Users/czc/Desktop/czc_code/goodjob/user_config.json)
- 修改了 [user_config.example.json](C:/Users/czc/Desktop/czc_code/goodjob/user_config.example.json)
  - 两个文件都补成完整统一配置结构
  - 让新用户后续只改这一个文件，就能覆盖大部分个性化需求

### 本次验证

- 已执行 Python 语法检查：
  - `config.py`
  - `cache.py`
  - `core.py`
  - `main.py`
  - `schema.py`
  - `tools.py`
- 已执行 `web_script.js` 语法检查
- 已执行配置读取验证：
  - `introduce` 可正常读取
  - `tags` 可正常读取
  - `frontend` 参数可正常读取
  - 当前 `thread=50`
  - 当前岗位评分延迟配置为 `4000 / 500`

### 当前结论

- 到这一阶段为止，项目已经完成“统一配置通路打通”。
- 现在用户相关配置已基本可以围绕 `user_config.json` 来改。
- `web_script.js` 中仍保留了一层本地默认值，主要用于首次请求 `/client-config` 的引导与接口失败兜底；这是刻意保留的稳态设计，不是漏改。

## 2026-04-07 工程化收尾（方案 A 第一轮）

### 本次目标

- 清理不会影响主链的基础 warning。
- 补齐 README 里的配置说明。
- 对旧接口采取“保留兼容，不强删”的策略，避免把现有链路硬切坏。

### 本次修改

- 修改了 [tools.py](C:/Users/czc/Desktop/czc_code/goodjob/tools.py)
  - 将正则改成 raw string 写法，消除 `invalid escape sequence` warning
  - `getMatchScore()` 末尾补了显式 `return None`，让返回路径更清晰

- 修改了 [readme.md](C:/Users/czc/Desktop/czc_code/goodjob/readme.md)
  - 新增“配置文件结构说明”章节
  - 明确说明：
    - 顶层字段
    - `frontend`
    - `backend`
    - `scoring`
    四层分别负责什么
  - 同时补充说明：
    - 前端现在优先读 `/client-config`
    - 旧接口仍作为兼容兜底存在

### 本次决策

- 当前不删除 `/tags` 与 `/get-introduce` 旧接口。
- 原因不是忘了删，而是刻意保留兼容回退，先保证主链稳定。
- 后续如果确认 `/client-config` 已稳定覆盖全部前端调用，再考虑是否做第二轮精简。

### 本次验证

- 已重新执行 Python 语法检查
- 已重新执行 `web_script.js` 语法检查
- 旧的 `tools.py` 正则 warning 已不再作为本轮新增问题存在

## 2026-04-07 旧缓存链拆除（resume-lock / cache.json）

### 本次目标

- 清理 ollama 时代遗留的旧缓存链。
- 让当前主链不再依赖 `resume-lock.md` 与 `cache.json`。
- 保留旧聊天接口的最小兼容能力，但不再为了兼容保留无意义缓存文件。

### 本次修改

- 重写了 [cache.py](C:/Users/czc/Desktop/czc_code/goodjob/cache.py)
  - 删除了：
    - `resume-lock.md` 对比逻辑
    - `cache.json` 读写逻辑
  - 当前仅保留三件事：
    - 读取 `Config.introduce`
    - 读取 `Config.character`
    - 读取 `Config.tags`
  - `resume.md` 改为可选读取：
    - 文件存在就读取
    - 文件不存在则返回空字符串

- 修改了 [readme.md](C:/Users/czc/Desktop/czc_code/goodjob/readme.md)
  - 将 `resume.md` 调整为“可选”准备项
  - 明确说明：
    - 当前自动投递主链已不强依赖简历文件
    - 旧聊天接口若要继续启用，简历文件仍可能有用
  - 明确说明当前主链已不再依赖：
    - `resume-lock.md`
    - `cache.json`

### 本次验证

- 已重新执行 Python 语法检查
- 已确认 `cache.py` 在没有 `resume.md` 时也不会直接抛 `FileNotFoundError`
- 已保留旧接口最小兼容能力：
  - 若后续启用旧聊天接口，仍可从 `cache.resume` 取到简历内容（如果存在）

### 当前结论

- `resume-lock.md` 与 `cache.json` 已从当前主链设计中正式退场。
- `resume.md` 不再是后端启动的硬前置条件。
- 当前项目结构比之前更贴近“一个配置文件驱动主链”的目标。

## 2026-04-07 主链彻底摘除 cache.py / resume.md 依赖

### 本次目标

- 让当前主链彻底不再依赖 `cache.py` 与 `resume.md`。
- 把 `main.py` 的主流程返回值直接改为从 `Config` 取。
- 对旧聊天接口保留最小兼容，但不再让它们反向绑住主链结构。

### 本次修改

- 修改了 [main.py](C:/Users/czc/Desktop/czc_code/goodjob/main.py)
  - 删除 `from cache import cache`
  - `/tags` 改为直接返回 `Config.tags`
  - `/get-introduce` 改为直接返回 `Config.introduce`
  - `/reply` 改为使用空字符串 `resume=''` 与 `Config.character` 作为最小兼容输入

- 修改了 [readme.md](C:/Users/czc/Desktop/czc_code/goodjob/readme.md)
  - 明确说明 `cache.py` 已不属于当前主链必要组成部分
  - 明确说明当前主链已完全不依赖：
    - `resume.md`
    - `resume-lock.md`
    - `cache.json`

### 本次验证

- 已重新执行 Python 语法检查
- 已重新执行配置读取检查
- 已确认：
  - `/tags` 直接来自 `Config.tags`
  - `/get-introduce` 直接来自 `Config.introduce`
- 当前主链已经不再经过 `cache.py`

### 当前结论

- 到这一阶段，`cache.py` 已经从当前自动投递主链中退场。
- `resume.md` 也已从当前主链依赖中彻底摘除。
- `cache.py` 若后续保留，也只剩遗留兼容层意义；继续清理时可以直接删除或并入 legacy 区域。

## 2026-04-07 按关键词列表轮换搜索

### 本次目标

- 不再让程序永远只搜岗位关键词列表里的第一个词。
- 结合已完成的“自动下一轮”能力，让每一轮自动切换到下一个岗位关键词。
- 让老板关注的多个方向都能在同一轮持续运行里被轮流覆盖。

### 本次修改

- 修改了 [cache.py](C:/Users/czc/Desktop/czc_code/goodjob/cache.py)
  - 将固定岗位关键词列表更新为：
    - `运维工程师`
    - `运维开发`
    - `SRE`
    - `AI`
    - `AI应用`
    - `AI应用工程师`
    - `AI开发`

- 修改了 [web_script.js](C:/Users/czc/Desktop/czc_code/goodjob/web_script.js)
  - 新增 `currentTagIdx`
  - 新增 `pickNextKeyword()`
  - 每次 `startRound()` 时自动取下一个关键词
  - 日志会明确打印：
    - 当前第几轮
    - 本轮搜索关键词是什么

### 当前效果

- 现在程序不再是：
  - 每轮都重复搜第一个关键词
- 而是改成：
  - 第 1 轮搜第 1 个词
  - 第 2 轮搜第 2 个词
  - 第 3 轮搜第 3 个词
  - ...
  - 到最后一个词后，再回到第 1 个词循环

### 风险与备注

- 关键词切换后，Boss 页面是否继续保留已选的城市 / 薪资 / 工作经验筛选，仍以实际前端行为为准；这部分需要老板继续实测确认。
- 当前仍保留每轮手动筛选窗口；如果后续确认切关键词后筛选条件仍能稳定保留，这个体验会更顺。
