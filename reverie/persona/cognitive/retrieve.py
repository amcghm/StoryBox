from typing import Union
from loguru import logger
import numpy as np

from reverie.common.event import Event
from reverie.persona.memory.memory_item import MemoryItem
from reverie.common.llm import embedding_model


def retrieve(persona, perceived: list[Event | str], ret_cnt=30) -> dict[Event | str, list[MemoryItem]]:
    """
    Return a list of memories related to these events based on the persona and the perceived events.

    :param persona: Persona
    :param perceived: Perceived Event or string
    :param ret_cnt: Maximum number of retrieved memories to return
    :return: Dictionary of lists of memories
    """

    logger.debug(f"[{persona.name}] is retrieving relevant memories based on the perceived objects.")

    # List of memories to return
    retrieved = dict()

    # Iterate over the perceived events
    for event in perceived:
        # Get the persona's memory items (including event, thought, and chat_mem)
        memories = persona.long_term_mem.event_mem + persona.long_term_mem.thought_mem + persona.long_term_mem.chat_mem
        # Sort MemoryItems in descending order by creation time
        memories.sort(key=lambda x: x.create_time, reverse=True)
        # Get recency scores
        recency_scores = get_recency_score(persona, memories)
        recency_scores = normalize(recency_scores)
        # Get importance scores
        importance_scores = get_importance_score(persona, memories)
        importance_scores = normalize(importance_scores)
        # Get relevance scores
        relevance_scores = get_relevance_score(persona, memories, event)
        relevance_scores = normalize(relevance_scores)

        # Calculate the final score based on the weights in persona.scratch
        scores = [
            (i, persona.scratch.recency_w * recency_scores[i] + \
             persona.scratch.importance_w * importance_scores[i] + \
             persona.scratch.relevance_w * relevance_scores[i]) \
            for i in range(len(recency_scores))
        ]

        # Sort in descending order based on the calculated score
        scores.sort(key=lambda x: -x[1])
        # Top ret_cnt items
        scores = scores[:ret_cnt]
        retrieved[event] = [memories[i] for i, _ in scores]

    # logger.debug(f"[{persona.name}] retrieved memories are {retrieved}")

    return retrieved


def normalize(values: list[Union[int, float]]) -> list[float]:
    """
    Normalize a list of integers or floats to the range [0, 1]
    :param values: List containing integers or floats
    :return: List normalized to the range [0, 1]
    """

    if not values:
        return []

    min_value = min(values)
    max_value = max(values)

    # If all values are equal, return a list of all zeros
    if max_value - min_value == 0:
        return [0.0] * len(values)

    normalized_values = [(value - min_value) / (max_value - min_value) for value in values]
    return normalized_values


def get_embedding(text: str) -> np.ndarray:
    """
    Get the embedding vector corresponding to the text
    :param text: Text
    :return: Vector
    """

    if not text:
        raise ValueError("Input text cannot be empty.")

    return embedding_model.encode(text)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Cosine similarity
    :param a: np.ndarray
    :param b: np.ndarray
    :return: float
    """

    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def get_recency_score(persona, memories: list[MemoryItem]) -> list[float]:
    """
    Get recency score, calculated using power operation based on persona.scratch.recency_decay
    :param persona: Persona
    :param memories: List of memory items
    :return: List of recency scores corresponding to positions
    """

    scores = [persona.scratch.recency_decay ** i for i in range(len(memories))]
    return scores


def get_importance_score(persona, memories: list[MemoryItem]) -> list[float]:
    """
    Get importance score, temporarily returning 1.0 for all
    :param persona: Persona
    :param memories: List of memory items
    :return: List of importance scores corresponding to positions
    """

    # Because if the retrieval_cnt of most events is the same and minimal, they will become 0 after normalization
    scores = [1.0] * len(memories)
    return scores


def get_relevance_score(persona, memories: list[MemoryItem], event: Event | str) -> list[float]:
    """
    Get relevance score, calculate similarity based on embedding
    :param persona: Persona
    :param memories: List of memory items
    :param event: Current event or string
    :return: List of similarity scores corresponding to positions
    """

    scores = []
    # Get the embedding of the current event
    if isinstance(event, Event):
        event_embedding = get_embedding(event.description)
    elif isinstance(event, str):
        event_embedding = get_embedding(event)
    else:
        raise TypeError("Expected 'event' to be of type Event or str")

    # Iterate through memories and calculate similarity with their embeddings
    for mem in memories:
        if mem.embedding is None:
            mem.embedding = get_embedding(mem.content)
        # Calculate cosine_similarity
        score = cosine_similarity(event_embedding, mem.embedding)
        scores.append(score)

    return scores
