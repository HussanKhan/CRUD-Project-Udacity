import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(32), index=True)


class Games(Base):
    __tablename__ = 'video_games'

    id = Column(Integer, primary_key=True, unique=True)
    title = Column(String, nullable=False)
    genre = Column(String, nullable=False)
    more_info = Column(String, nullable=False)
    trailers = Column(String, nullable=False)
    summary = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey(User.id))
    video_games = relationship(User)

    # for returning json
    @property
    def serialize(self):
        return {
            'Title': self.title,
            'Genre': self.genre,
            'Wiki-Link': self.more_info,
            'Trailer Link': 'https://www.youtube.com' + str(self.trailers),
            'HTML Summary': self.summary,
        }

engine = create_engine('sqlite:///videogame.db')
Base.metadata.create_all(engine)
