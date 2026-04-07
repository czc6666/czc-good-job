from config import Config


class Cache:
    def __init__(self):
        self.resume = self._load_resume()
        self.introduce = Config.introduce
        self.character = Config.character
        self.tags = Config.tags

    @staticmethod
    def _load_resume() -> str:
        resume_path = Config.resume_name
        try:
            with open(resume_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return ''


cache = Cache()
