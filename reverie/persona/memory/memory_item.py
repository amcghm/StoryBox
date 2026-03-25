from datetime import datetime
from reverie.manager.datetime_manager import datetime_manager


class MemoryItem:
    def __init__(self,
                 content: str,
                 memory_type: str,
                 create_time: datetime = None,
                 retrieval_cnt: int = 0,
                 embedding=None,
                 speaker: str = None,
                 listener: str = None):
        # Memory content
        self.content = content
        # Memory type: event / thought / chat
        self.memory_type = memory_type
        # Memory creation time
        self.create_time = create_time if create_time else datetime_manager.get_current_datetime()
        # Memory retrieval count
        self.retrieval_cnt = retrieval_cnt
        # embedding
        self.embedding = embedding

        # If it is a chat type, the following properties are also required
        ## Speaker
        self.speaker = speaker
        ## Listener
        self.listener = listener

    def __repr__(self):
        if self.memory_type != 'chat':
            return (f"MemoryItem(content={self.content}, "
                    f"memory_type={self.memory_type}, "
                    f"create_time={self.create_time.strftime('%Y-%m-%d %I:%M %p')}, "
                    f"retrieval_cnt={self.retrieval_cnt})")
        else:
            return (f"MemoryItem(speaker={self.speaker},"
                    f"listener={self.listener}, "
                    f"content={self.content}, "
                    f"memory_type={self.memory_type}, "
                    f"create_time={self.create_time.strftime('%Y-%m-%d %I:%M %p')}, "
                    f"retrieval_cnt={self.retrieval_cnt})")

    def to_dict(self) -> dict:
        """
        Convert properties to a dict type
        :return: dict
        """

        item_dict = self.__dict__.copy()
        item_dict['create_time'] = item_dict['create_time'].strftime('%Y-%m-%d %I:%M %p')
        item_dict.pop('embedding')

        return item_dict


if __name__ == '__main__':
    memory_item = MemoryItem('Hello', 'event')
    print(memory_item)
