import json
import os
from datetime import datetime

from reverie.persona.memory.memory_item import MemoryItem
from reverie.manager.prompt_manager import prompt_manager
from reverie.manager.datetime_manager import datetime_manager


class LongTermMemory:
    def __init__(self, file_path: str = None) -> None:
        # Event memory list
        self.event_mem: list[MemoryItem] = []
        # Thought memory list
        self.thought_mem: list[MemoryItem] = []
        # Chat memory list
        self.chat_mem: list[MemoryItem] = []

        if file_path:
            self.load_file(file_path)

    def __repr__(self) -> str:
        return f"""LongTermMemory(
    event_mem = {self.event_mem},
    thought_mem = {self.thought_mem},
    chat_mem = {self.chat_mem} )"""

    def load_file(self, file_path: str) -> bool:
        """
        Load long-term memory from a file.
        :param file_path: File path
        :return: True if loaded successfully, False otherwise
        """

        if os.path.exists(file_path):
            with open(file_path) as f:
                data = json.load(f)

            memory_types = {
                'event_mem': self.event_mem,
                'thought_mem': self.thought_mem,
                'chat_mem': self.chat_mem,
            }

            # Iterate over each memory type and dynamically load memory items
            for memory_type, memory_list in memory_types.items():
                for item_data in data.get(memory_type, []):
                    # Create MemoryItem instance
                    memory_item = MemoryItem(
                        content=item_data['content'],
                        memory_type=item_data['memory_type'],
                        create_time=datetime.strptime(item_data['create_time'], '%Y-%m-%d %I:%M %p'),
                        retrieval_cnt=item_data['retrieval_cnt'],
                    )

                    # If it's a chat type, speaker and listener also need to be set
                    if memory_type == 'chat_mem':
                        memory_item.speaker = item_data['speaker']
                        memory_item.listener = item_data['listener']

                    # Add the memory item to the corresponding list
                    memory_list.append(memory_item)

            return True

        return False

    def save(self, file_path: str) -> None:
        """
        Save long-term memory to a file.
        :param file_path: File path
        :return: None
        """

        data = {
            'event_mem': [item.to_dict() for item in self.event_mem],
            'thought_mem': [item.to_dict() for item in self.thought_mem],
            'chat_mem': [item.to_dict() for item in self.chat_mem],
        }

        with open(file_path, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def summarize_memories(self) -> None:
        """
        Summarize memories.
        :return: None
        """

        for i, mem in enumerate([self.event_mem, self.thought_mem, self.chat_mem]):
            if mem:
                mem_type = 'event' if i == 0 else 'thought' if i == 1 else 'chat'
                prompt_inputs = [mem_type, mem]
                response = prompt_manager.async_chat_and_parse('summarize_memories.txt', prompt_inputs,
                                                               json_response=True)

                ## Parse
                new_event_mem = []
                for item in response:
                    memory_item = MemoryItem(content=item.get('content'),
                                             memory_type=item.get('memory_type'),
                                             create_time=datetime.strptime(item.get('create_time'),
                                                                           '%Y-%m-%d %I:%M %p'),
                                             retrieval_cnt=item.get('retrieval_cnt'))
                    new_event_mem.append(memory_item)

                if i == 0:
                    self.event_mem = new_event_mem
                elif i == 1:
                    self.thought_mem = new_event_mem
                else:
                    self.chat_mem = new_event_mem

    def add_chat_mem(self, chat_history: list[tuple[str, str, str]]) -> None:
        """
        Add chat memory.
        :param chat_history: Chat history, [(speaker_name, listener_name, utterance)]
        :return: None
        """

        for speaker_name, listener_name, utterance in chat_history:
            memory_item = MemoryItem(
                content=utterance,
                memory_type='chat',
                create_time=datetime_manager.get_current_datetime(),
                retrieval_cnt=0,
                speaker=speaker_name,
                listener=listener_name
            )

            self.chat_mem.append(memory_item)


if __name__ == '__main__':
    long_term_memory = LongTermMemory()
    long_term_memory.event_mem.append(MemoryItem('there is a singer in the park', 'event'))
    long_term_memory.event_mem.append(MemoryItem('there is a singer in the park', 'event'))
    long_term_memory.event_mem.append(MemoryItem('there are two singers in the natural park', 'event'))
    long_term_memory.summarize_memories()
    print(long_term_memory)
