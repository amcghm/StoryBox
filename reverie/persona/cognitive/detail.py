from loguru import logger

from reverie.common.event import Event
from reverie.manager.datetime_manager import datetime_manager
from reverie.manager.event_manager import event_manager
from reverie.manager.persona_manager import persona_manager
from reverie.manager.prompt_manager import prompt_manager


async def generate_event_detail(persona, current_event: Event) -> str | None:
    """
    Generate the details of the event and the corresponding persona's psychology.
    :param persona: Persona
    :param current_event: Current event
    :return: str | None
    """
    prompt_inputs = [
        persona.scratch.get_iss(),
        datetime_manager.get_current_datetime(return_str=True),
        persona_manager.get_curr_location_by_name(persona.name),
        persona.scratch.name,
        current_event,
    ]

    prompt_file_name = 'generate_event_detail_abnormal.txt' if persona.scratch.abnormal else 'generate_event_detail.txt'

    response = await prompt_manager.async_chat_and_parse(prompt_file_name, prompt_inputs, json_response=True)
    try:
        return response['detail']
    except:
        return None


async def detail(persona) -> None:
    """
    If the persona is busy with an event, it might be very simple, so we need to describe it in detail.
    :param persona: Persona
    :return: None
    """

    # Get the event the current persona is currently doing
    current_event_id = persona_manager.get_curr_event_id_by_name(persona.name)
    current_event = event_manager.get_event_by_id(current_event_id)

    # If the current event exists and no detail has been generated yet
    if current_event and not current_event.detail:
        logger.debug(f"[{persona.name}] is detailing.")
        # Generate a more detailed description of the event
        event_detail = await generate_event_detail(persona, current_event)

        if event_detail:
            # logger.debug(f"[{persona.name}'s detailed event description] {event_detail}")

            current_event.detail = event_detail
            event_manager.update_event(current_event)

    # Clear abnormal status
    persona.scratch.abnormal = False
