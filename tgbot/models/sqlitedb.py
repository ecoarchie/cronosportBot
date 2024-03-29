from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, BigInteger
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Date, DateTime, Time
import datetime
import pandas as pd
import numpy as np
from tgbot.config import load_config

config = load_config(".env")
engine = create_engine("sqlite:///tgbot/data/copernico.db")

Base = declarative_base()


class Race(Base):
    __tablename__ = "races"
    id = Column(Integer, primary_key=True)
    race_id = Column(String, unique=True)
    race_title = Column(String)
    race_date = Column(Date)
    is_running = Column(String, default="running")
    user = relationship("User", back_populates="race")
    copernico_data = relationship("CopernicoData", back_populates="race")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True)
    user_name = Column(String)
    race_following = Column(String, ForeignKey("races.race_id"))
    race = relationship("Race", back_populates="user")


class CopernicoData(Base):
    __tablename__ = "copernico_data"
    id = Column(Integer, primary_key=True)
    dorsal = Column(Integer)
    event = Column(String)
    surname = Column(String)
    name = Column(String)
    gender = Column(String)
    birthdate = Column(Date)
    category = Column(String)
    status = Column(String)
    time_official = Column(Time)
    time_real = Column(Time)
    time_tod_finish = Column(DateTime)
    race_id = Column(String, ForeignKey("races.race_id"))
    race = relationship("Race", back_populates="copernico_data")


async def create_tables():
    Base.metadata.bind = engine
    Base.metadata.create_all()


async def delete_tables():
    Base.metadata.bind = engine
    Base.metadata.drop_all()


Session = sessionmaker(bind=engine)
ses = Session()


async def get_or_add_user(user_id, user_name, race_following=None):
    user = (
        ses.query(User.telegram_id, User.race_following)
        .filter(User.telegram_id == user_id)
        .first()
    )

    if user == None:
        ses.add(
            User(
                telegram_id=user_id, user_name=user_name, race_following=race_following
            )
        )
        ses.commit()
    else:
        return user  # returns user object


async def set_race_followed(user_id, race_id):
    ses.query(User).filter(User.telegram_id == user_id).update(
        {User.race_following: race_id}, synchronize_session="fetch"
    )
    ses.commit()


async def add_race(race_id, race_title, race_date):
    try:
        ses.add(Race(race_id=race_id, race_title=race_title, race_date=race_date))
        ses.commit()
        return "Мероприятие успешно добавлено в БД\nВот список активных мероприятий"
    except Exception as e:
        ses.rollback()
        return "Мероприятие с таким id уже есть в БД"


async def delete_race(id):
    ses.query(Race).filter(Race.race_id == id).delete(synchronize_session=False)
    ses.commit()
    return "Мероприятие было удалено"


async def get_all_races():
    q = ses.query(Race.race_id, Race.race_title, Race.race_date).all()
    return q


async def get_current_date_races(date: datetime.date):
    q = (
        ses.query(Race.race_id, Race.race_title, Race.is_running, Race.race_date)
        .filter(Race.race_date == date)
        .all()
    )
    print(q)  # TODO заменить на return для хэндлера


async def get_running_races():
    q = (
        ses.query(Race.race_id, Race.race_title, Race.race_date)
        .filter(Race.is_running == "running")
        .all()
    )
    return q


async def run_race(race_id):
    ses.query(Race).filter(Race.race_id == race_id).update(
        {Race.is_running: "running"}, synchronize_session="fetch"
    )
    ses.commit()


async def stop_race(race_id):
    ses.query(Race).filter(Race.race_id == race_id).update(
        {Race.is_running: "stopped"}, synchronize_session="fetch"
    )
    ses.commit()


column_names_aliases = {
    "times.official_:::finish:::": "time_official",
    "times.real_:::finish:::": "time_real",
    "times.tod_:::finish:::": "time_tod_finish",
}


async def update_copernico_db():
    running_races = await get_running_races()
    frames = []
    for race in running_races:
        race_id = race[0]
        COPERNICO_API = f"https://public-api.copernico.cloud/api/races/{race_id}/preset/{config.copernico.email}:::{config.copernico.preset_main}"
        df = pd.read_json(COPERNICO_API)
        df["race_id"] = pd.Series(None)
        df["race_id"] = df["race_id"].fillna(race_id)
        frames.append(df)
    res_df = pd.concat(frames)
    res_df.rename(columns=column_names_aliases, inplace=True)
    res_df["time_official"].replace(np.nan, 0, inplace=True)
    res_df["time_real"].replace(np.nan, 0, inplace=True)
    res_df["time_tod_finish"].replace(np.nan, 0, inplace=True)
    res_df["time_official"] = res_df["time_official"].apply(_millisec_to_time)
    res_df["time_real"] = res_df["time_real"].apply(_millisec_to_time)
    res_df["time_tod_finish"] = res_df["time_tod_finish"].apply(
        _from_millisec_to_datetime
    )
    res_df.to_sql(
        "copernico_data", engine, if_exists="replace", index=False, index_label="id"
    )


"""
async def update_copernico_db():
    #Апдейт базы Копернико при помощи SQLAlchemy - апдейт двух таблиц на 5000 строк занимает около 6 секунд
    running_races = await get_running_races()
    for race in running_races:
        race_id = race[0]
        ses.query(CopernicoData).filter(CopernicoData.race_id == race_id).delete(synchronize_session='fetch')
        ses.commit()
        COPERNICO_API = f"https://public-api.copernico.cloud/api/races/{race_id}/preset/au@cronosport.ru:::test101"
        r = requests.get(COPERNICO_API).json()
        list_of_entries = []
        for entry in r:
            new_entry = CopernicoData(
                dorsal=entry["dorsal"],
                event=entry["event"],
                surname=entry["surname"],
                name=entry["name"],
                gender=entry["gender"],
                birthdate=_birthdate_to_date(entry["birthdate"]),
                category=entry["category"],
                status=entry["status"],
                time_official=_millisec_to_time(entry["times.official_:::finish:::"]),
                time_real=_millisec_to_time(entry["times.real_:::finish:::"]),
                time_tod_finish=_from_millisec_to_datetime(entry["times.tod_:::finish:::"]),
                race_id=race_id,
            )
            list_of_entries.append(new_entry)
        ses.add_all(list_of_entries)
        ses.commit()
"""


async def find_entry(race_id, bib_or_surname):
    try:
        int(bib_or_surname)
        q = (
            ses.query(
                CopernicoData.dorsal,
                CopernicoData.name,
                CopernicoData.surname,
                CopernicoData.time_real,
                CopernicoData.category,
            )
            .filter(
                CopernicoData.race_id == race_id,
                CopernicoData.dorsal == bib_or_surname,
            )
            .all()
        )
        return q

    except ValueError:
        q = (
            ses.query(
                CopernicoData.dorsal,
                CopernicoData.name,
                CopernicoData.surname,
                CopernicoData.time_real,
                CopernicoData.category,
            )
            .filter(
                CopernicoData.race_id == race_id,
                CopernicoData.surname == bib_or_surname.capitalize(),
            )
            .all()
        )
        return q

    except Exception:
        return "Попробуй еще раз"


def _millisec_to_time(time_in_ms):
    if type(time_in_ms) is not None and time_in_ms > 0:
        seconds = int(time_in_ms) // 1000 % 60
        minutes = int(time_in_ms) // (1000 * 60) % 60
        hours = int(time_in_ms) // (1000 * 60 * 60)
        return datetime.time(hours, minutes, seconds)
    else:
        return datetime.time(0, 0, 0)


def _from_millisec_to_datetime(msec):
    if type(msec) is not None:
        return datetime.datetime.fromtimestamp(msec / 1000.0)
    else:
        return datetime.date(1900, 1, 1)


def _birthdate_to_date(birthdate):
    if type(birthdate) is str:
        date_obj = datetime.datetime.strptime(birthdate, "%Y-%m-%d")
        return date_obj
    else:
        datetime.date(1900, 1, 1)


# async def delete_race_data_from_db(race_id):
#     ses.query(CopernicoData).filter(CopernicoData.race_id == race_id).delete(
#         synchronize_session="fetch"
#     )
#     ses.commit()
