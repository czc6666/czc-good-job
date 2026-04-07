import re


def getLLMReply(content: str) -> str:
    """
    获取大模型的回复
    """
    return content.split('</think>\n')[-1].strip()


def getMatchScore(text: str) -> int | None:
    """从文本直接获取匹配度数值"""
    # 如果只有数值
    if re.search(r'^\d+$', text):
        return int(text)
    # 分成多行，寻找匹配度
    for i in text.split('\n'):
        if re.search(r'匹配.*?\d+', i):
            return int(re.search(r'\d+', i).group())
    return None
