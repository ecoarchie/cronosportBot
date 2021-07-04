from dataclasses import dataclass

from environs import Env


@dataclass
class DbConfig:
    host: str
    password: str
    user: str
    database: str


@dataclass
class TgBot:
    token: str
    admin_ids: list
    use_redis: bool


@dataclass
class Miscellaneous:
    other_params: str = None


@dataclass
class Copernico:
    email: str
    preset_main: str
    preset_report_hl: str


@dataclass
class Config:
    tg_bot: TgBot
    db: DbConfig
    copernico: Copernico
    misc: Miscellaneous


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            token=env.str("BOT_TOKEN"),
            admin_ids=list(map(int, env.list("ADMINS"))),
            use_redis=env.bool("USE_REDIS"),
        ),
        db=DbConfig(
            host=env.str("DB_HOST"),
            password=env.str("DB_PASS"),
            user=env.str("DB_USER"),
            database=env.str("DB_NAME"),
        ),
        copernico=Copernico(
            email=env.str("COPERNICO_EMAIL"),
            preset_main=env.str("PRESET_MAIN"),
            preset_report_hl=env.str("PRESET_REPORT_HR"),
        ),
        misc=Miscellaneous(),
    )
