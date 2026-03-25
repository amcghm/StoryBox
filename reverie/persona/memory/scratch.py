import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

import os
import json
from datetime import datetime

from reverie.config.logging_config import logger
from reverie.manager.datetime_manager import datetime_manager


class Scratch:
    """
    Persona initial settings
    """

    def __init__(self, f_saved):

        # Persona core identity

        ## Basic information
        self.name = None
        self.age = None
        ## L0 Innate, unchanging core traits
        self.innate = None
        ## L1 Stable traits
        self.learned = None
        ## L2 External features
        self.currently = None
        self.lifestyle = None
        self.living_area = None

        # Persona hyperparameters

        ## The magnitude of the persona's perception of surrounding events
        self.att_bandwidth = 3
        ## Memory retention
        self.retention = 5

        ## Reflection parameters
        self.recency_w = 1
        self.relevance_w = 1
        self.importance_w = 1
        self.recency_decay = 0.99
        self.importance_trigger_max = 150
        self.importance_trigger_curr = self.importance_trigger_max
        self.importance_ele_n = 0
        self.thought_count = 5

        # Persona plan

        ## Daily plan requirements
        self.daily_plan_requirement = None

        ## Daily plan for the day
        self.daily_plan = []

        ## Hourly-based daily plan for the day
        self.daily_plan_hourly: dict[datetime, str] = dict()

        ## Abnormal behavior
        self.abnormal: bool = False

        # If the file exists, read it directly
        self.load_file(f_saved)

    def load_file(self, file_path):
        if os.path.exists(file_path):
            with open(file_path) as f:
                data = json.load(f)

            for key, value in data.items():
                setattr(self, key, value)

    def save(self, output_file_path):
        data = {}

        # Iterate over all properties of the object
        for key, value in self.__dict__.items():
            if isinstance(value, datetime.datetime):
                # If it is a datetime type, convert to string
                data[key] = value.strftime("%Y-%m-%d %I:%M %p")
            elif isinstance(value, tuple):
                # If it is a tuple type, store directly
                data[key] = list(value)
            else:
                data[key] = value

        # Save data as a JSON file
        with open(output_file_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_iss(self) -> str:
        """
        Generate and return an "Identity Stable Set" (ISS) summary of a persona.
        This summary provides the persona's basic information and is a minimal description of the persona, usually used in prompts that need to invoke the persona.
        It includes the persona's name, age, innate traits, learned traits, current status, lifestyle, and daily plan requirements.
        The final returned string summarizes this key information, making it easy to quickly identify the persona's basic characteristics and background in conversations or situations.
        """
        commonset = ""
        commonset += f"Name: {self.name}\n"
        commonset += f"Age: {self.age}\n"
        commonset += f"Innate traits: {self.innate}\n"
        commonset += f"Learned traits: {self.learned}\n"
        commonset += f"Currently: {self.currently}\n"
        commonset += f"Lifestyle: {self.lifestyle}\n"
        return commonset

    def get_daily_plan_str(self) -> str:
        """
        Return self.daily_plan in str format
        :return: self.daily_plan in str format
        """

        return "\n".join(self.daily_plan)

    def get_daily_plan_hourly_str(self, after_current_time: bool = True) -> str:
        """
        Return self.daily_plan_hourly in str format
        :return: self.daily_plan_hourly in str format
        """
        ret = []
        all_times = sorted(list(self.daily_plan_hourly.keys()))

        current_time = datetime.strptime(datetime_manager.get_current_datetime().strftime("%I:%M %p"), "%I:%M %p")

        for time in all_times:
            if after_current_time:
                if time < current_time:
                    continue

            time_str = time.strftime("%I:%M %p")
            ret.append(f"{time_str}: {self.daily_plan_hourly[time]}")

        return '\n'.join(ret)

    def get_daily_plan_requirement_str(self) -> str:
        """
        Return self.daily_plan_requirement in str format
        :return: self.daily_plan_requirement in str format
        """
        return "\n".join(self.daily_plan_requirement)


if __name__ == "__main__":
    scratch = Scratch(f"{project_root}/data/Journey_to_the_West/personas/Isabella Rodriguez/scratch.json")
    print(scratch.get_iss())
    print("---------")
