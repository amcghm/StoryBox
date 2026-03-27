from datetime import timedelta

from loguru import logger

from reverie.environment.world import World
from reverie.manager.persona_manager import persona_manager
from reverie.manager.event_manager import event_manager
from reverie.manager.prompt_manager import prompt_manager
from reverie.manager.datetime_manager import datetime_manager
from reverie.persona.cognitive.retrieve import retrieve
from reverie.persona.memory.memory_item import MemoryItem
from reverie.config.config import Config


async def summarize_relationship(curr_persona, target_persona, retrieved: dict[str, list[MemoryItem]]) -> str:
    """
    Summarize the relationship between two personas.

    :param curr_persona: Current persona
    :param target_persona: Target persona
    :param retrieved: Current persona's memory of the target persona
    :return: Summary of the relationship between the two personas
    """

    retrieved = list(retrieved.values())[0]
    statements = [item.content for item in retrieved]

    prompt_inputs = [
        statements,
        curr_persona.name,
        target_persona.name,
    ]

    response = await prompt_manager.async_chat_and_parse('summarize_relationship.txt', prompt_inputs,
                                                         json_response=True)
    relationship = response.get('relationship')

    return relationship


async def generate_single_utterance(speaker, listener, retrieved, chat_history) -> tuple[str, bool]:
    """
    Generate a single utterance.

    :param speaker: Speaker
    :param listener: Listener
    :param retrieved: Retrieved memory
    :param chat_history: Chat history
    :return: (Utterance, whether to end the chat)
    """

    retrieved = list(retrieved.values())[0]
    impression = [item.content for item in retrieved]

    prompt_inputs = [
        speaker.scratch.get_iss(),
        listener.scratch.get_iss(),
        speaker.name,
        listener.name,
        impression,
        persona_manager.get_curr_location_by_name(speaker.name),
        chat_history
    ]

    prompt_file_name = 'generate_single_utterance_abnormal.txt' if speaker.scratch.abnormal else 'generate_single_utterance.txt'

    response = await prompt_manager.async_chat_and_parse(prompt_file_name, prompt_inputs, json_response=True)

    utterance = response.get('utterance')
    is_end = response.get('is_end')
    is_end = True if is_end and is_end.lower() == 'true' else False

    return utterance, is_end


def move(persona, plan: dict) -> None:
    """
    Move to a location.

    :param persona: Persona
    :param plan: Plan, which contains the key 'move'
    :return: None
    """

    persona_manager.set_location(persona.name, plan['move']['location'])
    # Create a corresponding new event
    new_event = event_manager.create_event(
        description=plan['move']['event']['description'],
        start_time=plan['move']['event']['start_time'],
        end_time=plan['move']['event']['end_time'],
        participants=[persona.name],
        location=plan['move']['location']
    )
    persona_manager.set_event_id(persona.name, new_event.event_id)


async def chat(curr_persona, plan: dict, round_num: int = 5, history_limit: int = 4) -> None:
    """
    Chat with another persona.

    :param curr_persona: Current persona
    :param plan: Plan
    :param round_num: Number of chat rounds
    :param history_limit: Memory limit
    :return: None
    """

    # Get the chat target
    target_persona_name = plan['chat']
    target_persona = persona_manager.get_persona_by_name(target_persona_name)

    # Teleport curr_persona to target_persona's location
    target_location = persona_manager.get_curr_location_by_name(target_persona.name)
    persona_manager.set_location(curr_persona.name, target_location)

    logger.debug(f"{curr_persona.name} is chatting with {target_persona.name}")

    # Chat history for the conversation rounds, [(speaker_name, listener_name, utterance)]
    chat_history: list[tuple[str, str, str]] = []

    for round_i in range(round_num):
        for speaker, listener in [(curr_persona, target_persona), (target_persona, curr_persona)]:
            # Get memory about the target_persona
            focal_points = [listener.name]
            retrieved = retrieve(speaker, focal_points, 30)
            # Summarize the relationship between these two people
            relationship = await summarize_relationship(speaker, listener, retrieved)
            # Get chat history, needs to be limited by history_limit
            last_chat = [f"{name}: {dialogue}" for name, _, dialogue in chat_history[-history_limit:]]
            last_chat = "\n".join(last_chat)

            # Retrieve memory again based on chat history
            if last_chat:
                focal_points = [listener.name, relationship, last_chat]
            else:
                focal_points = [listener.name, relationship]

            retrieved = retrieve(speaker, focal_points, 10)

            # Generate a single utterance, rather than a whole round
            utterance, is_end = await generate_single_utterance(speaker, listener, retrieved, last_chat)
            chat_history.append((speaker.name, listener.name, utterance))

            # Check if the chat needs to end early
            if is_end:
                break

        if is_end:
            break

    # Write the chat content into the memory of the corresponding personas
    curr_persona.long_term_mem.add_chat_mem(chat_history)
    target_persona.long_term_mem.add_chat_mem(chat_history)

    logger.debug(f"[chat history of {curr_persona.name} and {target_persona.name}] {chat_history}")

    # Calculate the duration required for the chat
    total_characters = sum(len(utterance) for _, _, utterance in chat_history)
    total_seconds = total_characters / Config.execute['chat_avg_speed']
    duration = timedelta(seconds=round(total_seconds))

    # Create a new chat event
    new_event = event_manager.create_event(
        description=f"{curr_persona.name} is chatting with {target_persona.name}",
        detail=str(chat_history),
        start_time=datetime_manager.get_current_datetime(),
        duration=duration,
        participants=[curr_persona.name, target_persona.name],
        location=target_location
    )
    persona_manager.set_event_id(curr_persona.name, new_event.event_id)


async def execute(persona, world: World, plan: dict) -> bool:
    """
    Execute the plan.
    
    :param persona: Persona
    :param world: World
    :param plan: Plan
    :return: Whether the execution is successful
    """

    logger.debug(f"[{persona.name}] is executing.")

    # If the current persona has unfinished events, let them finish the current events first
    if persona_manager.is_busy(persona.name):
        return False

    if not plan:
        return False

    # Move to a location
    if 'move' in plan:
        move(persona, plan)

    # Chat with someone
    elif 'chat' in plan:
        await chat(persona, plan, Config.execute['round_num'])

    return True
