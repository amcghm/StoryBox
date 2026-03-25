from datetime import datetime, timedelta
from reverie.config.config import Config


class DateTimeManager:
    def __init__(self, current_datetime: str | datetime):
        if isinstance(current_datetime, str):
            self._current_datetime = datetime.strptime(current_datetime, "%Y-%m-%d %I:%M %p")
        elif isinstance(current_datetime, datetime):
            self._current_datetime = current_datetime
        else:
            raise ValueError(
                "current_datetime should be a datetime object or a string in '%Y-%m-%d %I:%M %p' format.")

    def get_current_datetime(self,
                             return_str: bool = False,
                             str_format: str = "%Y-%m-%d %I:%M %p") -> str | datetime:
        """
        Return the current datetime.
        :param return_str: Whether to return in string format
        :param str_format: String format
        :return: Current datetime
        """
        if return_str:
            return self._current_datetime.strftime(str_format)

        return self._current_datetime

    def set_current_datetime(self, new_datetime: str | datetime):
        if isinstance(new_datetime, str):
            self._current_datetime = datetime.strptime(new_datetime, "%Y-%m-%d %I:%M %p")
        elif isinstance(new_datetime, datetime):
            self._current_datetime = new_datetime
        else:
            raise ValueError("new_datetime should be a datetime object or a string in '%Y-%m-%d %I:%M %p' format.")

    def advance_datetime(self, days: float = 0, hours: float = 0, minutes: float = 0, seconds: float = 0):
        self._current_datetime += timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

    def is_new_day(self) -> bool:
        current_time = self._current_datetime.time()
        return current_time.hour == 0 and current_time.minute == 0 and current_time.second == 0

datetime_manager = DateTimeManager(Config.start_datetime)
