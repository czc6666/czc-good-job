from config import Config


class Cache:
    """遗留兼容层。

    当前自动投递主链已经不再依赖 cache.py / cache.json。
    这里仅保留最小只读兼容接口，避免旧入口导入时报错。
    """

    def __init__(self):
        self.resume = ''
        self.introduce = Config.introduce
        self.character = Config.character


cache = Cache()
