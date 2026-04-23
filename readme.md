# goodjob

一个面向 Boss 直聘的轻量自动投递简历项目，采用“浏览器脚本 + 本地 Python 后端”的组合方式。

这个仓库当前主线已经收敛为：
- 单简历
- 单方向投递
- 规则筛选岗位
- 固定打招呼
- 收到 Boss 新消息后直接发送简历
- 默认不继续自动聊天

也就是说，它不是通用招聘平台框架，也不是复杂的 AI 求职代理，更不是一个招聘 SaaS。

## 现在能做什么

当前主链能力：
- 在 Boss 直聘岗位列表里轮换搜索关键词
- 对岗位做规则打分
- 达到阈值后自动打招呼
- 收到 Boss 新消息后直接发送指定简历
- 连续多轮没有新岗位时自动切换关键词继续挂机
- 遇到超时、详情异常、打招呼异常时自动恢复

## 不是什么

- 不是多招聘平台通用框架
- 不是复杂多轮自动聊天助手
- 不是运行时强依赖大模型的 AI 求职代理
- 不是招聘 SaaS 产品

## 当前主线定位

当前公开主线优先服务一个更清晰的目标：

“让用户只维护一套岗位关键词、一套打招呼文案、一份简历，然后稳定地在 Boss 直聘上自动投递。”

也就是说：
- 重点不是聊天像不像人
- 重点是筛选、打招呼、发简历这条链路是否稳定
- 主链默认不依赖 ollama 才能运行

## 项目结构

- `main.py`：FastAPI 后端入口
- `core.py`：规则评分与旧聊天能力主逻辑
- `config.py`：配置加载与岗位评分配置
- `web_script.js`：Boss 页面 Tampermonkey 脚本
- `user_config.example.json`：用户配置模板
- `resume-example.md`：简历模板
- `DEV_LOG.md`：开发演进记录

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 准备用户配置

复制模板：

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

把 `resume.md` 改成你自己的 Markdown 简历。

说明：
- 当前自动投递主链并不依赖它做岗位打分
- 它主要用于你自己管理简历内容，或保留给旧接口扩展使用

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

如果你只想最快跑起来，可以按这个顺序：

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

主要包括：

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
岗位评分规则，包括：
- 标题强负向词
- 标题弱负向扣分词
- 标题强匹配词
- 标题中匹配词
- 正文基础设施加分词
- 正文辅助加分词
- 正文负向扣分词

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

如果你还要继续启用这些旧接口：
- `/reply`
- `/is-need-resume`
- `/is-need-works`

再额外安装 `ollama` 即可。

也就是说：
- `ollama` 现在属于 legacy 能力
- 不是主链运行前提

## 仓库说明

- `user_config.json`、`resume.md`、日志文件、压缩包等本地文件默认不进入仓库
- `user_config.example.json` 是公开模板，不建议直接提交真实配置
- `DEV_LOG.md` 用来记录工程演进
- 当前公开仓库优先服务中文用户，因此默认中文说明

## 历史说明

这个项目在个人使用阶段曾经演化出一版“双简历 / 双方向自动路由”的复杂版本。

那版代码已经单独归档到分支：
- `archive/double-routing-chaos`

这个归档分支仅供历史参考：
- 能用
- 但配置复杂、耦合较高
- 不推荐新用户直接从那个分支开始使用

如果你只是想正常上手，请优先使用当前主线的单简历版本。

## 后续方向

当前更合理的继续方向是：
- 保持用户配置外置化
- 保持岗位规则可调
- 继续优先保证 Boss 自动化链路稳定
- 不把主线重新做回复杂双路由或重度模型依赖版本
