from sqlalchemy.orm import Session
from reverie.database.database import db
from reverie.database.table.persona_table import PersonaTable
from reverie.config.logging_config import logger
from reverie.manager.datetime_manager import datetime_manager
from reverie.manager.event_manager import event_manager


class PersonaManager:
    def __init__(self, db: Session, persona_dict: dict = None):
        self.db = db
        self._persona_dict = persona_dict or {}

    def add_persona(self,
                    persona,
                    name: str = None,
                    curr_location: str = None,
                    curr_event_id: int = None) -> PersonaTable:

        if not name:
            name = persona.name
        if not curr_location:
            curr_location = persona.scratch.living_area

        self._persona_dict[name] = persona
        persona_t = PersonaTable(name=name,
                                 curr_location=curr_location,
                                 curr_event_id=curr_event_id)

        self.db.add(persona_t)
        self.db.commit()
        self.db.refresh(persona_t)

        logger.debug(f"[Add persona] "
                     f"name: {name}, "
                     f"current location: {curr_location}, "
                     f"current event id: {curr_event_id}")

        return persona_t

    def get_all_persona_names(self) -> list[str] | None:
        return list(self._persona_dict.keys())

    def get_all_personas(self) -> list | None:
        return list(self._persona_dict.values())

    def set_location(self, name: str, new_location: str):
        persona = self.db.query(PersonaTable).filter(PersonaTable.name == name).first()
        prev_location = persona.curr_location
        persona.curr_location = new_location
        self.db.commit()

        logger.debug(f"[Set persona's current location] "
                     f"name: {name}, "
                     f"previous location: {prev_location}, "
                     f"current location: {new_location}")

    def set_event_id(self, name: str, new_event_id: int):
        persona = self.db.query(PersonaTable).filter(PersonaTable.name == name).first()
        persona.curr_event_id = new_event_id
        self.db.commit()

        logger.debug(f"[Set persona's current event id] "
                     f"name: {name}, "
                     f"current event id: {new_event_id}")

    def get_persona_by_name(self, name: str):
        return self._persona_dict.get(name)

    def get_persona_names_by_location(self, location: str) -> list[str]:
        personas = self.db.query(PersonaTable.name).filter(PersonaTable.curr_location == location).all()
        return [persona.name for persona in personas]

    def get_curr_location_by_name(self, name: str) -> str:
        persona = self.db.query(PersonaTable).filter(PersonaTable.name == name).first()
        return persona.curr_location

    def get_curr_event_id_by_name(self, name: str) -> int:
        persona = self.db.query(PersonaTable).filter(PersonaTable.name == name).first()
        return persona.curr_event_id

    def is_existed(self, name: str) -> bool:
        """
        Check if a persona exists given their name.

        :param name: Persona's name
        :return: Whether the persona exists
        """
        return name in self._persona_dict

    def is_busy(self, name: str) -> bool:
        """
        Check if a persona is currently busy given their name.
        
        :param name: Persona's name
        :return: Whether the persona is currently busy
        """
        curr_event_id = self.get_curr_event_id_by_name(name)
        if curr_event_id:
            curr_event = event_manager.get_event_by_id(curr_event_id)
            if curr_event.end_time > datetime_manager.get_current_datetime():
                return True

        return False

persona_manager = PersonaManager(db)
