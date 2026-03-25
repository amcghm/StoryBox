import json
import random
from loguru import logger

from reverie.config.config import Config
from reverie.persona.cognitive.retrieve import retrieve
from reverie.manager.prompt_manager import prompt_manager
from reverie.manager.datetime_manager import datetime_manager
from reverie.persona.memory.memory_item import MemoryItem


async def generate_focal_points(persona, num_memories: int = 30, num_focal_points: int = 3) -> list[str]:
    """
    Generate a series of focal points based on the persona's memory.
    :param persona: Persona
    :param num_memories: Number of memories
    :param num_focal_points: Number of focal points to generate
    :return: Focal points
    """

    # Get all memories
    memories = persona.long_term_mem.event_mem + persona.long_term_mem.thought_mem + persona.long_term_mem.chat_mem

    # Calculate the number of randomly selected memories
    num_random_memories = int(num_memories * Config.reflect['random_memory_ratio'])
    num_latest_memories = num_memories - num_random_memories

    # Sort MemoryItems in descending order of creation time
    memories.sort(key=lambda x: x.create_time, reverse=True)

    # Select the latest memories
    latest_memories = memories[:num_latest_memories]

    # Randomly select from the remaining memories
    remaining_memories = memories[num_latest_memories:]
    random_memories = random.sample(remaining_memories, min(num_random_memories, len(remaining_memories)))

    # Combine the latest and randomly selected memories
    selected_memories = latest_memories + random_memories

    # Convert to str for the prompt
    selected_memories = [mem.content for mem in selected_memories]
    selected_memories = '\n'.join(selected_memories)

    prompt_inputs = [
        selected_memories,
        num_focal_points
    ]

    response = await prompt_manager.async_chat_and_parse('generate_focal_points.txt', prompt_inputs, json_response=True)
    focal_points = response[: num_focal_points]

    return focal_points


async def generate_thoughts(retrieved: list[MemoryItem], num_thoughts: int = 3) -> list[str]:
    """
    Generate thoughts based on retrieved memories.
    :param retrieved: Retrieved memories
    :param num_thoughts: Number of thoughts to generate
    :return: List of thoughts
    """

    # Convert to str for the prompt
    retrieved = [mem.content for mem in retrieved]
    retrieved = '\n'.join(retrieved)

    prompt_inputs = [
        retrieved,
        num_thoughts
    ]

    response = await prompt_manager.async_chat_and_parse('generate_thoughts.txt', prompt_inputs, json_response=True)
    thoughts = response[: num_thoughts]

    return thoughts


async def reflect(persona) -> None:
    """
    Review the persona's memories and generate new thoughts based on them, set to execute a reflection once every night.
    :param persona: Persona
    :return: None
    """

    logger.debug(f"[{persona.name}] is reflecting.")

    # Randomly generate focal points from all memories, then reflect
    # The focal_points here appear in the form of questions, e.g., "Who am I?"
    focal_points = await generate_focal_points(persona, 30, 3)

    logger.debug(f"[{persona.name}]'s focal points: {focal_points}")

    # Retrieve from memory
    retrieved = retrieve(persona, focal_points, 10)

    # Reflect based on each focal point
    for focal_point_retrieved in retrieved.values():
        thoughts = await generate_thoughts(focal_point_retrieved, 5)
        # Add each thought to the persona's thought memory
        for thought in thoughts:
            memory_item = MemoryItem(
                content=thought,
                memory_type='thought',
                create_time=datetime_manager.get_current_datetime()
            )

            persona.long_term_mem.thought_mem.append(memory_item)
