# goodjob

一个面向 **Boss 直聘** 的轻量自动投递简历项目，基于 **浏览器脚本 + 本地 Python 后端** 的组合使用方式。

> 面向中国用户，围绕 Boss 直聘 的真实投递流程做自动化整理，不追求做成通用招聘平台框架。

## 这项目现在能做什么

当前主链能力：

- 面向 Boss 直聘岗位列表做规则匹配
- 在 Boss 直聘内自动轮换搜索关键词
- 自动发起固定打招呼
- 收到 Boss 新消息后自动发送简历
- 默认不继续自动聊天

## 这项目不是什么

- 不是多招聘平台通用自动化框架
- 不是复杂多轮自动聊天助手
- 不是运行时强依赖大模型的 AI 求职代理
- 不是招聘 SaaS 产品

## 当前状态

当前仓库已经完成一轮开源化整理，主线已经收敛到：

- 尽量把用户差异化配置收口到 `user_config.json`
- 前端优先通过 `/client-config` 读取配置
- 自动投递主链不再依赖 `ollama`
- 旧的简历缓存链已退出主链
- 项目定位明确为 **Boss 直聘自动投递简历脚本**

如果你只是想先把项目跑起来，优先看这几个文件：

- `user_config.example.json`
- `readme.md`
- `web_script.js`
- `main.py`

## 适合什么场景

- 你主要在 **Boss 直聘** 上投递岗位
- 想把 Boss 直聘里的重复投递动作自动化
- 想保留“我自己决定投不投”的基本控制感
- 不想把项目重度绑死在运行时大模型上

## 不适合什么场景

- 想做复杂多轮自动聊天助手
- 想把所有决策都交给运行时大模型
- 想做多招聘平台通用自动化框架
- 想做通用招聘平台 SaaS，而不是一个可自定义脚本

## 当前项目结构

- `main.py`：FastAPI 后端入口
- `core.py`：评分与旧聊天能力主逻辑
- `config.py`：规则评分配置
- `cache.py`：遗留兼容层（当前主链已不依赖，可后续继续清理）
- `web_script.js`：浏览器脚本
- `user_config.example.json`：用户配置模板
- `resume-example.md`：简历模板

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

然后修改这个文件里的用户配置。现在建议只改这一个文件，主要包括：

- 顶层基础字段
  - `introduce`：你的固定打招呼语
  - `character`：你的回复风格
  - `tags`：你想轮换搜索的岗位关键词
  - `resume_name`：遗留聊天接口如仍要读取简历文件时可用
  - `think_model` / `chat_model`：如果你仍要使用旧的聊天相关接口，可在这里切模型
- `frontend`
  - 前端运行参数，例如：
    - `thread`
    - `manualFilterWaitMs`
    - `preloadScrollPixels`
    - `preloadScrollWaitMs`
    - `maxEmptyRounds`
- `backend`
  - 后端参数，例如岗位评分延迟
- `scoring`
  - 岗位评分关键词与分值

也就是说，后续用户定制默认尽量只动 `user_config.json` 这一处。

### 3. （可选）准备简历文件

```bash
cp resume-example.md resume.md
```

把 `resume.md` 改成你自己的 Markdown 简历。

> 当前主链已经完全不依赖这份文件。
> 只有你后续自己想恢复/继续折腾旧聊天式接口时，它才还有意义。

### 4. 启动后端

```bash
python main.py
```

Windows 下也可以直接双击：

```text
start_backend.bat
```

### 5. 部署浏览器脚本

把 `web_script.js` 内容粘贴到 Tampermonkey 中，然后打开 **Boss 直聘** 页面即可。

## 最小使用路径

如果你只想最快跑起来，可以按这个顺序：

1. 复制 `user_config.example.json` 为 `user_config.json`
2. 只修改：
   - `introduce`
   - `tags`
   - `frontend.thread`
3. 启动后端 `python main.py`
4. 浏览器装入 `web_script.js`
5. 打开 Boss 直聘 页面测试

也就是说，大部分用户第一次上手时，不需要先读完整源码。

## 配置文件结构说明

当前推荐把所有用户差异化内容都集中维护在 `user_config.json`。

主要分成四层：

### 1. 顶层基础字段

- `resume_name`
- `think_model`
- `chat_model`
- `introduce`
- `character`
- `tags`

### 2. `frontend`

浏览器端运行参数，例如：

- `thread`
- `manualFilterWaitMs`
- `roundRestartDelayMs`
- `maxEmptyRounds`
- `preloadScrollPixels`
- `preloadScrollWaitMs`

### 3. `backend`

后端运行参数，例如：

- `job_score_delay_base_ms`
- `job_score_delay_jitter_ms`

### 4. `scoring`

岗位评分规则，包括：

- 标题强负向词
- 标题弱负向扣分词
- 标题强匹配词
- 标题中匹配词
- 正文加分词
- 正文扣分词

前端启动时会优先请求后端的 `/client-config`，统一读取：

- `introduce`
- `tags`
- `frontend`

如果这个接口失败，前端当前仍会回退旧接口，作为兼容兜底。

## 关于大模型依赖

当前主链在 **未安装 `ollama`** 的情况下也能运行，覆盖这些能力：

- 固定 `tags`
- 固定 `introduce`
- 规则岗位评分
- 收到新消息后直接发简历

如果你还要继续启用这些旧接口：

- `/reply`
- `/is-need-resume`
- `/is-need-works`

再额外安装 `ollama` 即可。

> 说明：当前自动投递主链已经不再依赖 `resume.md`、`resume-lock.md`、`cache.json` 这类旧链路文件。
> 这些文件现在都不属于主链必要组成部分。

## 仓库说明

- `user_config.json`、`resume.md`、日志文件、压缩包等本地文件默认不进入仓库
- `user_config.example.json` 是公开模板，不建议直接把自己的真实配置提交上来
- `DEV_LOG.md` 保留在仓库里，用来记录这次开源化整理与后续工程演进
- 当前公开仓库优先服务中文用户，因此对外说明默认优先中文

## 开源化方向

这个项目当前已经适合继续往下面两个方向收敛：

1. **用户配置外置化**
   - 把打招呼语、搜索关键词、简历文件名、模型名都抽到配置文件
2. **策略配置外置化**
   - 后续再把岗位评分关键词、阈值、惩罚项继续抽成独立 profile

这样新用户上手时，就不需要每次先改代码。
