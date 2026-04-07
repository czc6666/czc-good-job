from pydantic import BaseModel, Field
from typing import Annotated
from enum import Enum


class JobScore(BaseModel):
    score: Annotated[int, Field(description='匹配度分数')]


class InterestValue(BaseModel):
    value: Annotated[bool, Field(description='是否感兴趣')]


class NeedResume(BaseModel):
    need: Annotated[bool, Field(description='是否需要简历')]


class NeedWorks(BaseModel):
    need: Annotated[bool, Field(description='是否需要作品集')]


class MessageRole(str, Enum):
    system = 'system'
    user = 'user'
    assistant = 'assistant'


class Msg(BaseModel):
    role: Annotated[MessageRole, Field(description='消息角色')]
    content: Annotated[str, Field(description='消息内容')]
