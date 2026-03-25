from reverie.database.database import Base
from sqlalchemy import Column, Integer, String


class PersonaTable(Base):
    __tablename__ = 'persona'

    name = Column(String, primary_key=True)
    curr_location = Column(String)
    curr_event_id = Column(Integer)
