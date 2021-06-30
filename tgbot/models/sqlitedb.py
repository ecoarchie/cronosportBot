from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, BigInteger
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Boolean, Date
from datetime import date, datetime

engine = create_engine("sqlite:///tgbot/data/copernico.db")

Base = declarative_base()


class Race(Base):
    __tablename__ = "races"
    id = Column("Id", Integer, primary_key=True)
    race_id = Column("RaceId", String)
    race_title = Column("RaceTitle", String)
    race_date = Column("RaceDate", Date)
    is_running = Column("IsRunning", String, default="running")
    children = relationship("User", back_populates="parent")


class User(Base):
    __tablename__ = "users"
    id = Column("Id", Integer, primary_key=True)
    telegram_id = Column("UserId", BigInteger)
    user_name = Column("UserName", String)
    race_following = Column(String, ForeignKey("races.RaceId"))
    parent = relationship("Race", back_populates="children")


class CopernicoData(Base):
    pass


async def create_tables():
    Base.metadata.bind = engine
    Base.metadata.create_all()


Session = sessionmaker(bind=engine)
ses = Session()


async def add_user(user_id, user_name, race_following=None):
    ses.add(
        User(telegram_id=user_id, user_name=user_name, race_following=race_following)
    )
    ses.commit()


async def set_race_followed(user_id, race_id):
    ses.query(User).filter(User.telegram_id == user_id).update(
        {User.race_following: race_id}, synchronize_session="fetch"
    )
    ses.commit()


async def add_race(race_id, race_title, race_date):
    ses.add(Race(race_id=race_id, race_title=race_title, race_date=race_date))
    ses.commit()


async def get_all_races():
    q = ses.query(Race.race_id, Race.race_title, Race.is_running, Race.race_date).all()
    print(q)  # TODO заменить на return для хэндлера


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
    print(q)  # TODO заменить на return для хэндлера


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


async def delete_race_data_from_db(race_id):
    ses.query(CopernicoData).filter(CopernicoData.race_id == race_id).delete(
        synchronize_session="fetch"
    )
    ses.commit()
