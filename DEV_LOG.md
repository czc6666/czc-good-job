# 开发日志

> 这份文件主要记录 `goodjob` 这次开源化整理与后续工程演进过程。新会话接手时，可先读 `PROJECT_MEMORY.md`，再读这份 `DEV_LOG.md`。

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

## 2026-04-14 同账号双方向路由、挂机稳定性与 Chrome 副本排障

### 这次处理的主线

这次围绕 `goodjob` 主要做了三类事情：

1. **把同一个 Boss 账号下的 AI / 运维双方向投递路由真正接起来**
2. **修复挂机时容易中断的几个现实问题**（Boss 当日打招呼上限、Edge 标签页休眠、空轮自动停机）
3. **尝试做 Chrome 独立副本**，用于双浏览器双账号并行；目前该副本仍未稳定，不作为正式主线方案

---

### 一、这次确认下来的稳定主线

当前老板可稳定使用的主线仍然是：

- **Edge 单浏览器**
- **同一个 Boss 账号**
- 同一个后端
- 根据岗位自动路由：
  - `AI` 岗位 → AI 招呼语 + AI 简历索引
  - `运维` 岗位 → 运维招呼语 + 运维简历索引
- 老板若要兼顾第二个账号，当前更稳的方式是：
  - **继续在 Edge 里手动切账号**
  - 例如半天跑大号、半天跑小号

也就是说，当前正式推荐方案不是 Chrome 副本，而是：

**先把 Edge 主线当作生产可用版本，Chrome 线视为实验分支。**

---

### 二、这次查明并验证的关键问题

#### 1. 不是程序坏了，而是 Boss 当日打招呼上限拦截了流程

这次一度出现：
- 高分岗位可以 `greet_queued`
- 但全部立刻 `greet_queue_failed`

后续通过增强动作日志，明确记录到了：
- `addUrl`
- `chatUrl`
- `reason`

新日志显示失败原因为：
- `Error: biz_fail:温馨提示`

老板后续手动确认后发现，Boss 页面实际弹窗提示是：
- 当天已投递/打招呼达到阶段上限
- 需要手动确认一次
- 再点“立即沟通”后，后续打招呼流程又恢复正常

这说明这轮失败不是前端逻辑本身坏掉，而是：

**Boss 页面在达到当日额度后，会在“加入聊天列表 / 发起沟通”之前弹额外确认。**

这类现象后续要优先判断为：
- 页面业务拦截
- 不是代码立刻回归

---

#### 2. Edge 后台挂机时，标签页休眠会影响持续运行

老板在实际挂机过程中发现：
- Edge 后台标签页会变灰，进入休眠
- 一旦休眠，页面脚本容易中断或不再持续推进

因此当前稳定做法应补充为：
- 在 Edge 设置中关闭或放宽睡眠标签页
- 至少将 `zhipin.com` 加入“永不休眠”例外名单
- 必要时到 `edge://discards/` 检查对应标签页是否被自动 discard

这属于挂机场景的**环境配置要求**，不是评分逻辑问题。

---

#### 3. 连续空轮自动停止不适合挂机，现已改成自动切下一个关键词

原逻辑是：
- 连续 `maxEmptyRounds`（默认 3）轮没有新岗位
- 直接自动停止

这在短时测试时合理，但对“挂机省时间”目标不合理。

因此本次已修改原项目 [web_script.js](C:/Users/czc/Desktop/czc_code/goodjob/web_script.js)：
- 当连续空轮达到阈值时
- **不再停止脚本**
- 而是：
  - 记录日志：`连续 X 轮没有新岗位，自动切换到下一个关键词继续挂机`
  - 重置 `emptyRounds`
  - 直接进入下一轮关键词

这条改动属于当前主线的正式稳定性增强。

---

### 三、这次暴露出的配置链问题与修复

#### 问题：搜索关键词顺序改了但不生效

这次明确定位到一个关键坑：

- 顶层 `tags` 虽然已改成运维优先
- 但运行时默认 `ACTIVE_PROFILE = ai`
- `load_user_config()` 会把 `profiles.ai` 覆盖到顶层配置上
- 因此实际前端拿到的仍然是 `profiles.ai.tags`

这导致：
- 老板以为改了搜索顺序
- 实际运行时仍然先搜 AI 关键词

#### 处理结果

后续已将配置链收口为：
- **搜索关键词只认顶层 `tags`**
- `profile` 覆盖继续保留，但不再覆盖 `tags`

这样同账号双方向场景下，才不会再出现：
- 搜索顺序和岗位路由绑死在一起
- 改顶层配置却不生效

这是这轮中非常重要的一条长期经验：

**搜索层的关键词轮换，不应该再和 profile 的 delivery 配置绑死。**

---

### 四、Chrome 副本方案：已尝试，但暂不作为正式方案

这次为了实现：
- Edge 大号
- Chrome 小号
- 两边共存

曾复制出独立副本目录：
- `C:\Users\czc\Desktop\czc_code\goodjob-chrome`

并做了：
- 后端端口切到 `8001`
- `serverHost` 改到 `127.0.0.1:8001`
- 广播 channel / target 改成 chrome 专用前缀

#### 但当前结论是

Chrome 副本目前仍存在前端多标签页协作不稳定问题，主要表现为：

- 预加载完成后切到“处理聊天消息”阶段时容易卡住
- 暂停/继续后能推进一步，但不能自然稳定循环
- 搜索分支和聊天分支里都出现过：
  - `获取职位详情超时`
  - `聊天分支简历路由取详情超时`
- 曾出现 `BroadcastChannel is closed` 相关报错

这说明 Chrome 副本的真正问题更接近：

**详情页 / 聊天页 / 搜索页之间的多标签广播协作链不稳。**

#### 已做过的排障动作

在 `goodjob-chrome` 中已做过：
- 放宽 `timestampTimeout`
- 放宽 `detailTimeout`
- 补聊天页入口判定日志
- 补详情页入口和回传日志
- 给聊天分支取详情补超时兜底
- 给 Broadcast 生命周期和心跳 loop 做收口，减少 `Channel is closed` 报错

#### 当前结论

虽然 Chrome 副本的实验有助于定位问题，但**尚未达到正式可用标准**。

所以当前建议是：
- 不把 Chrome 副本作为主项目路线
- 老板如果要双账号，先继续使用：
  - **Edge 单浏览器手动切账号**

也就是说，Chrome 版目前属于：
- 已探索
- 已补部分诊断
- 暂停继续投入
- 以后如有必要再单独重启

---

### 五、本次对项目认知的更新

这轮之后，更明确的一点是：

`goodjob` 真正稳定可交付的东西，应该优先是：

- 单浏览器
- 单稳定主线
- 明确可解释的规则筛选
- 稳定的打招呼与发简历流程
- 能挂机但不过度依赖多实例并发

而不是一上来把：
- 多浏览器并发
- 多账号并发
- 多标签页复杂广播协作

一起堆上去。

这不是说后者永远不做，而是：

**应该先有一条足够稳的“生产主线”，再做并行副本实验。**

---

### 当前阶段建议

#### 正式推荐老板使用的方案
- `goodjob` 原项目 + Edge
- 关闭 Boss 页面休眠
- 当前空轮自动切关键词继续挂机
- 需要跑第二个账号时，先用手动切账号方式完成

#### 当前不推荐老板继续投入精力的方案
- `goodjob-chrome` Chrome 副本并行跑
- 继续把双浏览器并发当作当前生产方案

#### 以后如果要重启 Chrome 方案
建议单独开一轮“多标签协作链”专项修复，而不是边用边修。

---

## 2026-04-15 虚拟机环境下新页面被浏览器拦截的真实原因确认

### 这次确认的关键事实

老板在虚拟机里再次实际跑自动投简历脚本时，终于定位到了此前“脚本无法正常跳转新页面 / 看起来像打不开详情页或聊天页”的一个真实环境原因：

- 浏览器地址栏右侧出现了“**已阻止脚本启动并打开新页面**”之类的提示
- 手动点击该提示后，选择**允许**
- 之后脚本就可以正常打开新页面并继续流程

这说明此前至少有一类“新页面打不开”的异常，并不是：
- `goodjob` 代码逻辑本身错误
- 端口、广播、页面判定一定有问题

而是：

**浏览器/虚拟机环境把脚本触发的新窗口或新标签页拦截掉了。**

### 这条经验后续必须怎么用

以后如果再次遇到这些现象：
- 点击岗位后看起来没有跳转详情页
- 打招呼流程没有进入聊天页
- 自动投递链路像是“卡在打开新页面”这一步
- 日志上看像是详情页/聊天页没接上，但页面本身并没有明显报错

应先优先检查：
- 地址栏右侧是否有浏览器拦截提示
- 当前浏览器是否禁止脚本打开弹窗/新页面
- 虚拟机里的浏览器策略、弹窗策略、标签页策略是否把新窗口拦掉

而不是第一时间就判断为代码回归。

### 对 Chrome 8001 并行方案的意义

这条发现很重要，因为它说明此前 Chrome/虚拟机场景里，至少一部分“像是多标签协作失灵”的现象，可能混入了**浏览器环境层拦截新页面**这个外部变量。

因此后续如果继续重启 `goodjob-chrome` 的 8001 并行方案，应把下面这条加入启动前检查清单：

1. 确认浏览器已允许站点脚本打开新页面 / 弹窗
2. 确认地址栏右侧没有“已阻止脚本打开页面”的拦截提示
3. 再去判断是不是 Broadcast、时间戳、详情页回传链的问题

否则很容易把环境问题误判成代码问题，浪费大量排障时间。

---

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

## 2026-04-13 动态简历路由（第一阶段：后端决策层）

### 本次目标

- 在不破坏当前“是否投递”评分主链的前提下，为后续“一账号双简历”场景补上独立路由能力。
- 让后端不再只返回 `score`，而是同时返回：
  - `profile`
  - `introduce`
  - `resumeIndex`
- 明确区分：
  - `score` 负责“投不投”
  - `profile` 负责“投哪份简历 / 发哪段招呼语”

### 本次修改

- 修改了 [config.py](C:/Users/czc/Desktop/czc_code/goodjob/config.py)
  - 新增 `deliveryProfiles`
    - `ai -> introduce + resumeIndex=0`
    - `ops -> introduce + resumeIndex=1`
  - 新增 `routing`
    - `defaultProfile`
    - `minMargin`
    - AI / 运维两套独立路由关键词
  - 新增 `Config.get_delivery_profile()`

- 修改了 [core.py](C:/Users/czc/Desktop/czc_code/goodjob/core.py)
  - 保留原有 `evaluateJobMatch()` 作为“是否投递”评分器
  - 新增 `routeJobProfile()` 作为独立路由判定器
  - 新增 `evaluateJobDelivery()`，统一产出：
    - `score`
    - `profile`
    - `introduce`
    - `resumeIndex`
    - `route_scores`
    - `route_reason`

- 修改了 [main.py](C:/Users/czc/Desktop/czc_code/goodjob/main.py)
  - `/get-job-score` 改为调用 `evaluateJobDelivery()`
  - 返回结构从仅 `score` 扩展为：
    - `score`
    - `profile`
    - `introduce`
    - `resumeIndex`
    - `routeReason`
    - `routeScores`
  - 终端日志新增：
    - `profile`
    - `route_ai`
    - `route_ops`
    - `route_reason`

- 修改了 [user_config.json](C:/Users/czc/Desktop/czc_code/goodjob/user_config.json)
- 修改了 [user_config.example.json](C:/Users/czc/Desktop/czc_code/goodjob/user_config.example.json)
  - 同步补入 `deliveryProfiles` 与 `routing` 结构

### 本次验证

- 已执行 Python 语法检查：
  - `config.py`
  - `core.py`
  - `main.py`
- 已用 Windows 侧 Miniconda Python 直接执行核心函数验证
  - `AI应用工程师 -> profile=ai -> resumeIndex=0`
  - `运维开发工程师 -> profile=ops -> resumeIndex=1`
  - `SRE -> profile=ops -> resumeIndex=1`
  - `AI Agent后端开发工程师 -> profile=ai -> resumeIndex=0`
- 已直接执行 `main.py` 中 `/get-job-score` 对应逻辑验证接口返回结构
  - 能返回 `score + profile + introduce + resumeIndex + routeScores`

### 当前结论

- 第一阶段后端决策层已完成并验证通过。
- 当前仓库已经具备“同一岗位 -> 后端给出完整投递决策”的能力。
- 但浏览器前端此时尚未真正消费这些新字段，仍需要第二阶段把 `web_script.js` 接上。

## 2026-04-13 动态简历路由（第二阶段：前端接入层）

### 本次目标

- 在不推翻现有 Boss 页面自动化主链的前提下，把后端返回的投递决策真正接入前端执行层。
- 让前端在搜索页和聊天页都能按岗位方向切换：
  - 打招呼文案
  - 简历索引

### 本次修改

- 修改了 [web_script.js](C:/Users/czc/Desktop/czc_code/goodjob/web_script.js)
  - `Api.getJobScore()` 不再只提取 `score`，而是直接返回完整决策对象
  - 搜索页打招呼前：
    - 记录当前岗位的 `decision`
    - 日志新增 `profile / resumeIndex`
    - `SAY_HI` 广播返回改为优先使用当前岗位对应的 `introduce`
  - 聊天页首次打招呼：
    - 改为按后端返回的 `decision.introduce` 发送，而不是固定使用一个全局文案
  - `sendResume()` 改为支持 `sendResume(resumeIndex)`
  - 聊天页检测到新消息且尚未发简历时：
    - 重新拉取当前岗位详情
    - 重新请求后端决策
    - 按 `decision.resumeIndex` 发送对应简历

### 本次验证

- 已执行 `web_script.js` 语法检查（`node --check`）
- 已重新执行 Python 语法检查，确认本轮前端接入未破坏后端代码可加载性
- 已重新执行 Windows 侧接口验证，确认 `/get-job-score` 仍能稳定返回：
  - `ai -> resumeIndex=0`
  - `ops -> resumeIndex=1`

### 当前结论

- 第二阶段代码接入已完成。
- 现阶段已经形成完整链路：
  - 后端产出 `score + profile + introduce + resumeIndex`
  - 前端按岗位方向切不同招呼语与简历索引
- 当前剩余的真实风险不在语法与接口，而在 Boss 页面实际运行环境：
  - 多简历场景下是否总是弹“大窗选择简历”而不是“小窗默认发送”
  - 招聘方先发消息 / 我先打招呼 / 已聊过再补发简历这几种时序下，页面元素是否始终稳定
  - 这些需要老板继续在真实 Boss 页面中实测

## 2026-04-13 启动脚本收尾（移除旧的 1/2 手动选方向）

### 本次目标

- 让 `start_backend.bat` 与当前“统一后端 + 动态路由”的主逻辑保持一致。
- 去掉已经过时的 `1 - AI / 2 - OPS` 人工选择步骤，避免老板误以为仍需手动切整个后端方向。

### 本次修改

- 修改了 [start_backend.bat](C:/Users/czc/Desktop/czc_code/goodjob/start_backend.bat)
  - 删除了旧的 `1 / 2` 方向选择菜单
  - 删除了 `GOODJOB_PROFILE` / `GOODJOB_PROFILE_LABEL` 相关分支
  - 恢复为统一后端直接启动：
    - 固定使用 `C:\Users\czc\miniconda3\python.exe`
    - 直接执行 `main.py`

### 当前结论

- 现在双击 `start_backend.bat` 后，将直接启动统一后端。
- 岗位属于 AI 还是运维，不再由启动时人工选择，而是完全交给后端 routing + 前端执行层动态决定。

## 2026-04-13 统一关键词池收尾（修复 `/client-config.tags` 仍走单 profile 残留）

### 问题复盘

- 在完成“统一后端 + 动态路由”后，老板指出搜索关键词轮转仍未真正把 AI / 运维两套关键词揉在一起。
- 重新排查后确认：
  - `web_script.js` 的关键词轮转确实优先读取 `/client-config.tags`
  - 但 `config.py` 中 `get_client_config()` 仍直接返回 `Config.tags`
  - 而 `Config.tags` 仍受旧的单 profile 加载路径影响，只会落到一侧标签
- 这说明当时虽然完成了“投递路由”改造，但没有把“搜索关键词来源”这个同层架构点一起闭环收尾。

### 本次修改

- 修改了 [config.py](C:/Users/czc/Desktop/czc_code/goodjob/config.py)
  - 新增 `_load_raw_user_config()` 与 `RAW_USER_CONFIG`
    - 单独保留原始 `user_config.json` 结构，避免被 `load_user_config()` 抹平后丢失 `profiles` 层信息
  - 新增 `Config.get_merged_tags()`
    - 合并：
      - 当前基础 `tags`
      - `profiles.ai.tags`
      - `profiles.ops.tags`
    - 自动去重并保留顺序
  - 新增 `Config.get_default_introduce()` 作为统一后端场景下的兜底文案来源
  - `Config.get_client_config()` 改为返回：
    - `profile='mixed'`
    - `tags=Config.get_merged_tags()`
    - `introduce=Config.get_default_introduce()`

- 修改了 [main.py](C:/Users/czc/Desktop/czc_code/goodjob/main.py)
  - `/tags` 改为返回 `Config.get_merged_tags()`
  - `/get-introduce` 改为返回 `Config.get_default_introduce()`

### 本次验证

- 已重新执行 Python 语法检查：
  - `config.py`
  - `main.py`
- 已用 Windows 侧 Miniconda Python 直接执行接口验证：
  - `/client-config.tags` 已包含 AI + 运维两套关键词
  - `/tags` 旧接口回退路径也已返回混合关键词池
  - `/get-introduce` 返回统一后端场景下的默认兜底文案

### 当前结论

- 当前关键词轮转来源已修正为“统一混合关键词池”，不再只落到单一 profile。
- 至此，统一后端场景下的三层关键入口已基本对齐：
  - 搜索关键词来源
  - 投不投评分
  - 投递路由（文案 / 简历索引）

## 2026-04-19 修复打招呼消息未写入聊天框

### 二次补强

- 老板反馈首轮修复后仍不生效，说明问题不只是普通 `innerText`/事件触发不够，而更可能是 Boss 当前输入框挂了框架层受控状态。
- 因此继续补强了两点：
  - `tools.inputText()` 改为优先走原生 `HTMLInputElement/HTMLTextAreaElement.value` setter，而不是直接改实例属性，避免 React/Vue 一类受控输入组件不认值变更。
  - 聊天页 `sendMsg()` 改为同时兼容：
    - 原生 `value setter`
    - `contenteditable` 文本区
    - `execCommand('insertText')` 兜底
    - 补发 `keyup` 事件，尝试唤起页面自己的“输入后启用发送按钮”逻辑
- 同时新增更严格判定：如果写入后草稿内容仍为空，直接报 `输入框内容为空`，不再误以为已经写进去了。


### 问题现象

- 当前脚本主链可以正常筛岗、进入聊天页。
- 但在打招呼阶段，页面表现为：
  - 能打开聊天界面
  - 不会自动发送打招呼语
  - 甚至不会把文案写进聊天输入框
- 这说明问题不在岗位评分或聊天页跳转，而更像是 Boss 当前聊天输入框的前端写入/触发机制变了。

### 本次定位

- 排查 [web_script.js](C:/Users/czc/Desktop/czc_code/goodjob/web_script.js) 后确认，原 `sendMsg()` 只做了：
  - `ipt.innerText = text`
  - 等待
  - 直接点击发送按钮
- 这种写法在早期页面上可能够用，但对现在 Boss 聊天输入区不够稳：
  - 有些输入组件不只认 `innerText`
  - 还依赖 `value / textContent / input 事件 / focus 状态`
  - 否则按钮不会真正进入可发送状态

### 本次修改

- 修改了 [web_script.js](C:/Users/czc/Desktop/czc_code/goodjob/web_script.js)
  - 重写聊天页 `sendMsg()`：
    - 先 `focus()` 输入框
    - 同时写入：
      - `value`
      - `textContent`
      - `innerText`
    - 主动派发：
      - `InputEvent('input')`
      - `change`
    - 如果发送按钮仍不可用，再补一次 `execCommand('insertText')` 兜底
    - 最后再次检查发送按钮是否可用，不可用则直接抛错，避免表面点了其实没发出去

### 本次验证

- 已执行 `node --check web_script.js`，语法通过。
- 这次修复属于典型的“实际运行时 DOM 写入链”问题，不应只看能否进入聊天页；后续验证标准应明确改为：
  - 文案是否真的出现在输入框里
  - 发送按钮是否被激活
  - 消息是否真的发出

## 2026-04-13 本地决策日志落盘（便于回顾与调参）

### 本次目标

- 给“每次岗位计算 / 每次投递决策”补上本地留痕，方便老板后续回顾：
  - 岗位标题
  - 岗位原始信息
  - 匹配分数
  - 路由方向
  - 对应简历索引
  - 具体命中原因
- 避免后续优化算法时只能凭印象说“好像哪里判错了”。

### 本次修改

- 修改了 [main.py](C:/Users/czc/Desktop/czc_code/goodjob/main.py)
  - 新增 `job_decisions.jsonl` 本地日志文件
  - 新增 `append_job_decision_log()`
  - 每次 `/get-job-score` 计算完成后，都会追加写入一条 JSONL 记录

### 当前落盘字段

每条日志当前包含：
- `loggedAt`
- `title`
- `detail`
- `matchedField`
- `keyword`
- `score`
- `profile`
- `introduce`
- `resumeIndex`
- `routeReason`
- `routeScores`
- `titleScore`
- `detailScore`
- `comboScore`
- `titlePenaltyScore`
- `penaltyScore`
- `reason`
- `delayMs`
- `rawJob`

### 本次验证

- 已重新执行 `main.py` Python 语法检查

### 当前结论

- 现在每次岗位评分与路由决策，都会在项目目录本地追加一条记录到 `job_decisions.jsonl`。
- 这份日志后续可直接拿来做：
  - 判错回放
  - 规则调优
  - 典型岗位案例归类
