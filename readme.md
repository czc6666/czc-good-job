# goodjob

一个面向 Boss 直聘的轻量自动投递简历项目，采用“浏览器脚本 + 本地 Python 后端”的组合方式。

当前主线已经收敛为：
- 单简历
- 单方向投递
- 规则筛选岗位
- 固定打招呼
- 收到 Boss 新消息后直接发送简历
- 默认不继续自动聊天

它不是多招聘平台框架，不是复杂多轮自动聊天助手，也不是招聘 SaaS。

## 适合什么方向

当前仓库模板默认更适合这些岗位：
- AI 产品工程师
- AI 应用工程师
- AI Agent / 智能体
- 工作流工程师
- AI Native / Vibe Coding / 大模型应用落地类岗位

当前评分逻辑的核心偏好：
- 标题只做弱信号
- JD 正文里的真实技术要求、工具链、工作流是强信号
- 更关注 Claude Code、Cursor、Codex、Agent、Workflow、Prompt，以及需求到调试部署上线的闭环能力

不适合作为主目标方向的岗位：
- 传统算法训练 / 模型研发
- 传统运维 / SRE / DevOps
- 销售 / 运营
- 纯 C/C++/Go 底层岗

## 现在能做什么

当前主链能力：
- 在 Boss 直聘岗位列表里轮换搜索关键词
- 对岗位做规则打分
- 达到阈值后自动打招呼
- 收到 Boss 新消息后直接发送指定简历
- 连续多轮没有新岗位时自动切换关键词继续挂机
- 遇到超时、详情异常、打招呼异常时自动恢复

## 项目结构

- `main.py`：FastAPI 后端入口
- `core.py`：规则评分主逻辑 + 遗留聊天能力
- `config.py`：配置加载与岗位评分配置
- `web_script.js`：Boss 页面 Tampermonkey 脚本
- `user_config.example.json`：用户配置模板
- `resume-example.md`：简历模板
- `PROJECT_MEMORY.md`：长期项目背景与关键决策
- `DEV_LOG.md`：开发演进记录

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 准备用户配置

```bash
cp user_config.example.json user_config.json
```

首次最少只需要改这些字段：
- `introduce`：固定打招呼语
- `tags`：搜索关键词列表
- `frontend.resumeIndex`：发第几份简历，从 0 开始
- `frontend.thread`：投递阈值

### 3. （可选）准备简历文件

```bash
cp resume-example.md resume.md
```

说明：
- 当前自动投递主链并不依赖 `resume.md` 做岗位打分
- 它主要用于你自己管理简历内容，或保留给遗留接口扩展使用

### 4. 启动后端

```bash
python main.py
```

Windows 下也可以直接双击：

```text
start_backend.bat
```

### 5. 部署浏览器脚本

把 `web_script.js` 内容粘贴到 Tampermonkey 中，然后打开 Boss 直聘页面即可。

## 最小使用路径

1. 复制 `user_config.example.json` 为 `user_config.json`
2. 修改：
   - `introduce`
   - `tags`
   - `frontend.resumeIndex`
   - `frontend.thread`
3. 启动后端 `python main.py`
4. 浏览器装入 `web_script.js`
5. 打开 Boss 直聘页面测试

## 配置说明

当前推荐把所有用户差异化内容集中维护在 `user_config.json`。

普通用户主要改：
- `introduce`
- `tags`
- `frontend.resumeIndex`
- `frontend.thread`

更细的岗位评分规则默认由项目维护者在 `scoring` 中调整，不要求普通用户自己从零设计。

### 顶层字段
- `resume_name`
- `think_model`
- `chat_model`
- `introduce`
- `character`
- `tags`

### `frontend`
浏览器端运行参数，例如：
- `resumeIndex`
- `thread`
- `manualFilterWaitMs`
- `roundRestartDelayMs`
- `maxEmptyRounds`
- `detailTimeout`
- `greetTimeout`
- `preloadScrollPixels`
- `preloadScrollWaitMs`

### `backend`
后端运行参数，例如：
- `job_score_delay_base_ms`
- `job_score_delay_jitter_ms`

### `scoring`
岗位评分规则主要分成：
- 标题强负向词
- 标题弱负向扣分词
- 标题强匹配词
- 标题中匹配词
- 正文强正向词
- 正文辅助正向词
- 正文负向扣分词

当前推荐理解方式：
- 标题只做快速筛选
- JD 正文里的真实技术要求才是主要判断依据

前端启动时会优先请求后端 `/client-config`，统一读取：
- `introduce`
- `tags`
- `frontend`

## 关于大模型依赖

当前主链在未安装 `ollama` 的情况下也能运行，覆盖这些能力：
- 固定 `tags`
- 固定 `introduce`
- 规则岗位评分
- 收到新消息后直接发简历

如果你还要继续启用这些遗留接口：
- `/reply`
- `/is-need-resume`
- `/is-need-works`

再额外安装 `ollama` 即可。

也就是说：
- `ollama` 现在属于遗留能力
- 不是主链运行前提

## 仓库说明

- `user_config.json`、`resume.md`、日志文件等本地文件默认不进入仓库
- `user_config.example.json` 是公开模板，不建议直接提交真实配置
- 当前公开仓库优先服务中文用户，因此默认中文说明

## 历史说明

这个项目在个人使用阶段曾演化出一版“双简历 / 双方向自动路由”的复杂版本。

那版代码已经单独归档到分支：
- `archive/double-routing-chaos`

该分支仅供历史参考，不推荐新用户直接从那里开始。

## 后续方向

当前更合理的继续方向是：
- 保持用户配置外置化
- 保持岗位规则可调
- 继续优先保证 Boss 自动化链路稳定
- 不把主线重新做回复杂双路由或重度模型依赖版本
- 继续让评分更贴近 JD 正文真实技术要求，而不是岗位名字字面词
