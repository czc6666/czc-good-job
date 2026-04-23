import copy
import json
import os


PROFILE_ENV_KEY = 'GOODJOB_PROFILE'
DEFAULT_PROFILE_NAME = 'ai'
PROFILE_ALIASES = {
    '1': 'ai',
    '2': 'ops',
    'ai': 'ai',
    'ops': 'ops',
    'op': 'ops',
    'devops': 'ops',
}


DEFAULT_USER_CONFIG = {
    'resume_name': 'resume.md',
    'think_model': 'qwen3:0.6b',
    'chat_model': 'qwen3:0.6b',
    'introduce': '您好，我是一名对 AI 应用开发、自动化流程和工程落地感兴趣的求职者，想进一步了解这个岗位。',
    'character': '简洁 直接 礼貌',
    'tags': ['运维开发', 'SRE', 'DevOps', '运维工程师', '平台工程师', 'AI应用', 'AI应用工程师', 'AI开发', 'AI产品经理'],
    'backend': {
        'job_score_delay_base_ms': 2000,
        'job_score_delay_jitter_ms': 500,
    },
    'deliveryProfiles': {
        'ai': {
            'introduce': '您好，我是江西理工大学网络与信息安全硕士，做过 AI 工具站开发上线、科研数据链路构建和 Linux 服务器运维。近期持续使用 Codex、Claude Code 等工具辅助开发，也将 OpenClaw 接入信息整理、知识库联动和自动化工作流，具备把 AI 能力落到真实业务场景中的工程实现经验。',
            'resumeIndex': 0,
        },
        'ops': {
            'introduce': '您好，我是江西理工大学网络与信息安全硕士，长期参与实验室 Linux 服务器环境搭建、运维和科研数据链路支撑，做过环境部署、故障排查、自动化脚本开发和稳定性保障。近期也持续使用 Codex、Claude Code 等工具辅助开发，并将 OpenClaw 接入自动化处理与日常工作流。',
            'resumeIndex': 1,
        },
    },
    'routing': {
        'defaultProfile': 'ai',
        'minMargin': 4,
        'ai': {
            'title_strong_keywords': {
                'ai应用': 10,
                '人工智能应用': 10,
                '人工智能工程师': 10,
                'ai研发工程师': 10,
                'code agent': 10,
                'ai开发': 9,
                'ai agent': 10,
                '智能体': 10,
                '大模型应用': 9,
                'llm应用': 9,
                '工作流工程师': 8,
                'ai产品经理': 7,
            },
            'title_medium_keywords': {
                'ai': 6,
                'agent': 6,
                'workflow': 5,
                '工作流': 5,
                'prompt': 4,
                '提示词': 4,
                'rag': 5,
                'mcp': 4,
                '知识库': 4,
            },
            'detail_keywords': {
                'ai agent': 4,
                '智能体': 4,
                'llm': 4,
                '大模型': 4,
                '工作流': 3,
                'workflow': 3,
                'rag': 3,
                '知识库': 3,
                'prompt': 2,
                '提示词': 2,
                'embedding': 2,
                'rerank': 2,
                '知识召回': 2,
            },
        },
        'ops': {
            'title_strong_keywords': {
                '运维开发工程师': 10,
                '运维开发': 10,
                '运维工程师': 10,
                'sre': 10,
                'devops': 10,
                'linux运维': 9,
                '平台工程师': 9,
                '站点可靠性工程师': 10,
                '可靠性工程师': 9,
                '自动化运维': 9,
            },
            'title_medium_keywords': {
                '运维': 6,
                'linux': 5,
                '云平台': 5,
                '基础架构': 5,
                '发布工程师': 5,
                '平台工程': 5,
            },
            'detail_keywords': {
                'linux': 3,
                '服务器': 3,
                '监控': 3,
                'prometheus': 3,
                'grafana': 3,
                'docker': 3,
                'k8s': 3,
                'kubernetes': 3,
                '故障处理': 3,
                '高可用': 3,
                '部署': 2,
                '发布': 2,
                'shell': 2,
                '日志': 2,
                '自动化运维': 3,
            },
        },
    },
    'frontend': {
        'serverHost': 'http://127.0.0.1:8000',
        'resumeIndex': 0,
        'thread': 50,
        'timestampTimeout': 3000,
        'onlyGreet': False,
        'manualFilterWaitMs': 10000,
        'roundRestartDelayMs': 2000,
        'maxEmptyRounds': 3,
        'detailTimeout': 10000,
        'greetTimeout': 12000,
        'preloadScrollPixels': 180,
        'preloadScrollWaitMs': 450,
        'preloadStableRoundsLimit': 24,
        'preloadMaxRounds': 300,
        'preloadActivateCardEvery': 0,
        'preloadActivateCardWaitMs': 250,
    },
    'scoring': {
        'title_block_keywords': {
            '测试': 100,
            '销售': 100,
            '商务': 100,
            '运营': 100,
            '客服': 100,
            '管培生': 100,
            '培训生': 100,
            '储备干部': 100,
            '储干': 100,
            '项目经理': 100,
            '项目管理': 100,
            '数据开发': 100,
            '数据治理': 100,
            '算法': 100,
            '算法工程师': 100,
            '算法研究员': 100,
            '机器学习算法': 100,
            '深度学习算法': 100,
            '推荐算法': 100,
            '搜索算法': 100,
            'cv算法': 100,
            'nlp算法': 100,
            '多模态算法': 100,
            '模型训练': 100,
            '模型研发': 100,
            '大模型算法': 100,
            '训练': 100,
            '预训练': 100,
            '微调': 100,
            '嵌入式': 100,
            '硬件': 100,
            '渠道': 100,
            '光伏': 100,
        },
        'title_penalty_keywords': {
            'java': 35,
            '前端': 45,
            '后端': 20,
            '全栈': 18,
        },
        'title_strong_keywords': {
            'ai应用': 88,
            '人工智能应用': 88,
            'ai工程': 85,
            '人工智能工程师': 85,
            'ai开发': 86,
            'ai提效': 86,
            'ai产品': 84,
            '人工智能产品': 84,
            'ai产品经理': 84,
            'ai解决方案': 82,
            'ai实施顾问': 80,
            'ai agent': 88,
            '智能体': 88,
            'ai工作流': 86,
            '工作流工程师': 84,
            '大模型应用': 86,
            'llm应用': 86,
            'vibe coding': 88,
            'vibecoding': 88,
            '自动化工程师': 82,
            '工具开发': 80,
            '效率工程': 80,
            '云计算工程师': 58,
            '云计算开发工程师': 60,
            '云原生工程师': 58,
            '云原生开发工程师': 60,
            '云平台开发工程师': 58,
            '网络工程师': 52,
            '平台开发工程师': 52,
            '技术平台开发工程师': 54,
            '基础设施工程师': 52,
            '基础架构工程师': 54,
            'dba工程师': 52,
            '运维开发工程师': 60,
            '运维开发': 58,
            'devops': 58,
            'sre': 58,
            '站点可靠性工程师': 58,
            '运维工程师': 55,
            '平台工程师': 55,
            '平台工程': 55,
            '自动化运维': 55,
            '可靠性工程师': 52,
        },
        'title_medium_keywords': {
            'ai': 58,
            'agent': 76,
            'workflow': 72,
            '工作流': 72,
            '自动化开发': 70,
            '解决方案': 70,
            '实施顾问': 68,
            '产品经理': 68,
            'saas': 68,
            '工具': 64,
            '效率': 64,
            'rag': 68,
            '知识库': 66,
            'mcp': 66,
            'prompt': 64,
            '提示词': 64,
            'token': 72,
            'tokens': 72,
            '上下文工程': 72,
            'prompt工程': 72,
            '提示词工程': 72,
            '运维': 42,
            'linux运维': 42,
            '系统运维': 40,
            '云运维': 40,
            '云平台': 36,
            '基础架构': 36,
            '发布工程师': 34,
            'linux': 30,
        },
        'detail_infra_keywords': {
            'k8s': 10,
            'kubernetes': 10,
            'docker': 8,
            'ansible': 8,
            'jenkins': 8,
            'prometheus': 8,
            'grafana': 8,
            'elk': 8,
            'nginx': 6,
            'helm': 6,
            'terraform': 8,
            '云原生': 8,
            'devops': 8,
            'sre': 8,
            'ai agent': 10,
            '智能体': 10,
            'mcp': 8,
            'rag': 8,
            '知识库': 6,
            '工作流': 6,
            'workflow': 6,
            'aigc': 8,
            'llm': 8,
            '大模型应用': 8,
            'vibe coding': 24,
            'vibecoding': 24,
        },
        'detail_support_keywords': {
            'linux': 5,
            'shell': 4,
            'python': 4,
            '日志': 3,
            '监控': 3,
            '部署': 3,
            '发布': 3,
            '故障处理': 4,
            '高可用': 4,
            '自动化': 1,
            '服务器': 2,
            '运维': 3,
            '平台工程': 4,
            'ai': 3,
            '提效': 4,
            '自动化办公': 5,
            '效率工具': 5,
            '提示词': 5,
            'prompt': 5,
            'agent': 4,
            'copilot': 5,
            'saas': 4,
            '产品经理': 4,
            '解决方案': 4,
            '实施': 2,
            '顾问': 2,
            '工具开发': 6,
            '效率工程': 6,
            'token': 8,
            'tokens': 8,
            '上下文': 4,
            '上下文工程': 8,
            '提示词工程': 8,
            'prompt工程': 8,
            'embedding': 8,
            'rerank': 8,
            '知识召回': 8,
            'vibe': 6,
        },
        'detail_negative_keywords': {
            'spring': 12,
            'spring boot': 16,
            'react': 16,
            'vue': 16,
            'android': 12,
            'ios': 12,
            '小程序': 12,
            '客户': 10,
            '渠道': 12,
            '销售': 12,
            '新能源': 12,
            '光伏': 16,
            'to b': 8,
            'to c': 8,
        },
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        elif value is not None:
            result[key] = value
    return result


def _apply_legacy_compat(config: dict, user_config: dict) -> dict:
    legacy_top_level_to_nested = {
        'job_score_delay_base_ms': ('backend', 'job_score_delay_base_ms'),
        'job_score_delay_jitter_ms': ('backend', 'job_score_delay_jitter_ms'),
        'thread': ('frontend', 'thread'),
    }
    for old_key, (group, new_key) in legacy_top_level_to_nested.items():
        if old_key in user_config and user_config[old_key] is not None:
            config[group][new_key] = user_config[old_key]
    return config


def _normalize_profile_name(profile_name: str | None) -> str:
    raw = (profile_name or '').strip().lower()
    if not raw:
        return DEFAULT_PROFILE_NAME
    return PROFILE_ALIASES.get(raw, raw)


ACTIVE_PROFILE = _normalize_profile_name(os.getenv(PROFILE_ENV_KEY))


def _load_raw_user_config():
    config_path = 'user_config.json'
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
        if isinstance(user_config, dict):
            return user_config
    return {}


def load_user_config():
    config = copy.deepcopy(DEFAULT_USER_CONFIG)
    user_config = RAW_USER_CONFIG
    if isinstance(user_config, dict) and user_config:
        user_base_config = {k: v for k, v in user_config.items() if k != 'profiles'}
        config = _deep_merge(config, user_base_config)
        config = _apply_legacy_compat(config, user_base_config)

        profile_overrides = user_config.get('profiles', {})
        if isinstance(profile_overrides, dict):
            active_profile_config = profile_overrides.get(ACTIVE_PROFILE)
            if isinstance(active_profile_config, dict):
                profile_override_without_tags = {
                    k: v for k, v in active_profile_config.items() if k != 'tags'
                }
                config = _deep_merge(config, profile_override_without_tags)
                config = _apply_legacy_compat(config, profile_override_without_tags)
    return config


RAW_USER_CONFIG = _load_raw_user_config()
USER_CONFIG = load_user_config()


class Config:
    resume_name = USER_CONFIG['resume_name']
    think_model = USER_CONFIG['think_model']
    chat_model = USER_CONFIG['chat_model']
    introduce = USER_CONFIG['introduce']
    character = USER_CONFIG['character']
    tags = USER_CONFIG['tags']

    job_score_delay_base_ms = USER_CONFIG['backend']['job_score_delay_base_ms']
    job_score_delay_jitter_ms = USER_CONFIG['backend']['job_score_delay_jitter_ms']

    title_block_keywords = USER_CONFIG['scoring']['title_block_keywords']
    title_penalty_keywords = USER_CONFIG['scoring']['title_penalty_keywords']
    title_strong_keywords = USER_CONFIG['scoring']['title_strong_keywords']
    title_medium_keywords = USER_CONFIG['scoring']['title_medium_keywords']
    detail_infra_keywords = USER_CONFIG['scoring']['detail_infra_keywords']
    detail_support_keywords = USER_CONFIG['scoring']['detail_support_keywords']
    detail_negative_keywords = USER_CONFIG['scoring']['detail_negative_keywords']

    frontend = USER_CONFIG['frontend']
    backend = USER_CONFIG['backend']
    scoring = USER_CONFIG['scoring']
    delivery_profiles = USER_CONFIG['deliveryProfiles']
    routing = USER_CONFIG['routing']

    profile = ACTIVE_PROFILE

    @classmethod
    def get_delivery_profile(cls, profile_name: str | None = None):
        normalized_profile = _normalize_profile_name(profile_name) if profile_name else None
        selected_profile = normalized_profile or cls.routing.get('defaultProfile') or 'ai'
        return cls.delivery_profiles.get(selected_profile, cls.delivery_profiles.get('ai', {}))

    @classmethod
    def get_default_introduce(cls):
        return cls.get_delivery_profile().get('introduce', cls.introduce)

    @classmethod
    def get_client_config(cls):
        return {
            'profile': cls.profile,
            'introduce': cls.get_default_introduce(),
            'character': cls.character,
            'tags': cls.tags,
            'frontend': cls.frontend,
        }
