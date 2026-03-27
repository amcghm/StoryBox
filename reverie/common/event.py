from datetime import timedelta, datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON
from reverie.database.database import Base


class Event(Base):
    __tablename__ = 'event'

    event_id = Column(Integer, primary_key=True, index=True)
    description = Column(String, index=True)
    detail = Column(String, index=True, nullable=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True)
    # Stored as a string, can be converted to timedelta during calculation
    duration = Column(String, nullable=True)
    participants = Column(JSON, nullable=True)
    location = Column(String, nullable=True)

    def __init__(self, **kwargs):
        if isinstance(kwargs['start_time'], str):
            kwargs['start_time'] = datetime.strptime(kwargs['start_time'], "%Y-%m-%d %I:%M %p")

        if 'end_time' in kwargs and kwargs['end_time']:
            if isinstance(kwargs['end_time'], str):
                kwargs['end_time'] = datetime.strptime(kwargs['end_time'], "%Y-%m-%d %I:%M %p")
            kwargs['duration'] = str(kwargs['end_time'] - kwargs['start_time'])

        elif 'duration' in kwargs and kwargs['duration']:
            if isinstance(kwargs['duration'], str):
                h, m, s = map(int, kwargs['duration'].split(':'))
                kwargs['duration'] = timedelta(hours=h, minutes=m, seconds=s)

            kwargs['end_time'] = kwargs['start_time'] + kwargs['duration']
            kwargs['duration'] = str(kwargs['duration'])

        super().__init__(**kwargs)

    def __repr__(self):
        return (f"Event(id={self.event_id}, "
                f"description='{self.description}', "
                f"start_time={self.start_time.strftime('%Y-%m-%d %I:%M %p')}, "
                f"end_time={self.end_time.strftime('%Y-%m-%d %I:%M %p')}, "
                f"duration={self.duration})")

    def get_str(self) -> str:
        """
        Convert the event to a string representation, which is different from __repr__
        
        :return: Event in string format
        """

        ret_str = (f"{self.description}. "
                   f"This event starts at {self.start_time.strftime('%Y-%m-%d %I:%M %p')}, "
                   f"and will be end at {self.end_time.strftime('%Y-%m-%d %I:%M %p')}. "
                   f"Participants: {self.participants}. "
                   f"Location: {self.location}")

        return ret_str
