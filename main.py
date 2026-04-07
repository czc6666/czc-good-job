from datetime import datetime
import asyncio
import random
from fastapi import FastAPI, Body, HTTPException
from core import replyMsg, isNeedResume, isNeedWorks, evaluateJobMatch
from schema import Msg
from config import Config


app = FastAPI()


@app.get("/tags", summary="获取职位标签")
async def get_tags():
    return {
        'tags': Config.tags
    }


@app.get("/get-introduce", summary="获取自我介绍")
async def get_introduce():
    return {
        'introduce': Config.introduce
    }


@app.get("/client-config", summary="获取前端运行配置")
async def get_client_config():
    return Config.get_client_config()


@app.post("/get-job-score", summary="获取职位匹配度")
async def get_job_score(job: str = Body(..., description="职位信息")):
    result = evaluateJobMatch(job)
    delay_ms = max(0, Config.job_score_delay_base_ms + random.randint(
        -Config.job_score_delay_jitter_ms,
        Config.job_score_delay_jitter_ms,
    ))
    time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    title = result['title'] or '未识别标题'
    keyword = result['keyword'] or '无'
    matched_field_map = {
        'title': '岗位名称',
        'detail': '职位描述',
        'none': '未命中',
        'title_negative': '标题负向拦截',
    }
    print(
        f"[{time_str}] /get-job-score | "
        f"title={title} | "
        f"matched={matched_field_map.get(result['matched_field'], result['matched_field'])} | "
        f"keyword={keyword} | "
        f"title_score={result['title_score']} | "
        f"detail_score={result['detail_score']} | "
        f"combo_score={result['combo_score']} | "
        f"title_penalty_score={result.get('title_penalty_score', 0)} | "
        f"penalty_score={result['penalty_score']} | "
        f"delay_ms={delay_ms} | "
        f"score={result['score']} | "
        f"reason={result['reason']}",
        flush=True
    )
    await asyncio.sleep(delay_ms / 1000)
    return {
        'score': result['score']
    }


@app.post("/reply", summary="回复消息")
async def reply(msgs: list[Msg] = Body(..., description="消息列表")):
    try:
        return replyMsg(msgs, '', Config.character)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


@app.post("/is-need-resume", summary="是否需要简历")
async def is_need_resume(msgs: list[Msg] = Body(..., description="消息列表")):
    try:
        return {
            'need': isNeedResume(msgs)
        }
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


@app.post("/is-need-works", summary="是否需要作品集")
async def is_need_works(msgs: list[Msg] = Body(..., description="消息列表")):
    try:
        return {
            'need': isNeedWorks(msgs)
        }
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
