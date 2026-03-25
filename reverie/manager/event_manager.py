import json
import os
from datetime import datetime
from sqlalchemy.orm import Session

from reverie.database.database import db
from reverie.common.event import Event
from reverie.config.logging_config import logger


class EventManager:
    """
    Event Manager
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def load_file(self, file_path: str) -> bool:
        """
        Load events from a json file.
        :param file_path: File path
        :return: True if loaded successfully, False otherwise
        """

        if os.path.exists(file_path):

            logger.debug(f"Loading events from {file_path} ...")

            with open(file_path) as f:
                data = json.load(f)

            for event_item in data:
                # Remove event_id
                event_item.pop('event_id')
                self.create_event(**event_item)

            logger.debug(f"Events loaded, a total of {len(data)} events were loaded")

            return True

        return False

    def create_event(self,
                     description: str,
                     start_time: datetime | str,
                     detail: str = None,
                     location: str = None,
                     participants: list = None,
                     end_time: datetime | str = None,
                     duration: str = None) -> Event:
        event = Event(description=description, detail=detail, start_time=start_time, end_time=end_time,
                      duration=duration, participants=participants, location=location)

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return event

    def update_event(self, event: Event) -> Event:
        self.db.commit()
        self.db.refresh(event)
        return event


    def get_event_by_id(self, event_id: int, return_str: bool = False) -> Event | str | None:
        event = self.db.query(Event).filter(Event.event_id == event_id).first()
        return str(event) if return_str else event

    def get_current_event(self, curr_datetime: datetime, return_str: bool = False) -> list[Event | str] | None:
        current_events = (
            self.db.query(Event)
            .filter(Event.start_time <= curr_datetime, Event.end_time >= curr_datetime)
            .all()
        )
        return [str(event) for event in current_events] if return_str else current_events

    def get_all_events(self) -> list[Event]:
        """
        Get all events.
        :return: A list containing all events
        """
        events = self.db.query(Event).all()
        return events


event_manager = EventManager(db)
