from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Games
from sqlalchemy.ext.declarative import declarative_base
import json

Base = declarative_base()

engine = create_engine('sqlite:///videogame.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)


session = DBSession()

# DON'T RUN UNLESS DATABASE EMPTY

with open('COMBINEDFILE.json', 'r') as f:
    c = json.load(f)

    for item in c:
        attr = Games(title=item['Title'], genre=item['Genre'], more_info=item['Link'], trailers=item['Videos'][1], summary=item["Summary"][0])
        session.add(attr)
        session.commit()
        print('Item Added')

    print('ALL ITEMS ADDED')
    f.close


ana = session.query(Games).filter_by(title='Anthem').one()
session.delete(ana)
session.commit()
