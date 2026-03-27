import random
import re
from datetime import datetime, timedelta
from loguru import logger

from reverie.common.event import Event
from reverie.config.config import Config
from reverie.environment.world import World
from reverie.manager.event_manager import event_manager
from reverie.manager.persona_manager import persona_manager
from reverie.persona.memory.memory_item import MemoryItem
from reverie.manager.prompt_manager import prompt_manager
from reverie.manager.datetime_manager import datetime_manager


async def generate_wake_up_hour(persona) -> str:
    """
    Generate the persona's wake up hour

    :param persona: Persona
    :return: Wake up hour in 12-hour format, e.g., "8:00 am"
    """

    prompt_inputs = [persona.scratch.get_iss(), persona.scratch.name]
    response = await prompt_manager.async_chat_and_parse('wake_up_hour.txt', prompt_inputs, json_response=True)
    wake_up_hour = response.get("wake_up_hour")
    wake_up_hour = re.search(r"\d{1,2}:\d{2} (AM|PM|am|pm)", wake_up_hour).group()

    return wake_up_hour


async def generate_first_daily_plan(persona, wake_up_hour) -> list[str]:
    """
    Generate the persona's daily plan for the day, returning a list of actions the persona will perform today

    :param persona: Persona
    :param wake_up_hour: Wake up hour
    :return: A list containing the actions the persona will perform today
    """

    prompt_inputs = [
        persona.scratch.get_iss(),
        datetime_manager.get_current_datetime(return_str=True, str_format="%Y-%m-%d"),
        persona.scratch.name,
        wake_up_hour,
        persona.scratch.get_daily_plan_requirement_str()
    ]

    response = await prompt_manager.async_chat_and_parse('generate_first_daily_plan.txt', prompt_inputs,
                                                         json_response=True)
    return response


async def generate_new_daily_plan(persona, wake_up_hour: str):
    """
    Generate the persona's daily plan for the day, returning a list of actions the persona will perform today

    :param persona: Persona
    :param wake_up_hour: Wake up hour
    :return: A list containing the actions the persona will perform today
    """

    prompt_inputs = [
        persona.scratch.get_iss(),
        datetime_manager.get_current_datetime(return_str=True, str_format="%Y-%m-%d"),
        persona.scratch.name,
        wake_up_hour,
        persona.scratch.get_daily_plan_str(),
        persona.scratch.get_daily_plan_requirement_str()
    ]

    response = await prompt_manager.async_chat_and_parse('generate_new_daily_plan.txt', prompt_inputs,
                                                         json_response=True)
    return response


async def generate_daily_plan_requirement(persona):
    """
    Generate the persona's daily plan requirements for the day, returning a list of the persona's plan requirements for today
    
    :param persona: Persona
    :return: Requirements for the persona's plan today
    """

    prompt_inputs = [
        persona.scratch.get_iss(),
        datetime_manager.get_current_datetime(return_str=True, str_format="%Y-%m-%d"),
        persona.scratch.name,
        persona.scratch.get_daily_plan_requirement_str()
    ]

    response = await prompt_manager.async_chat_and_parse('generate_daily_plan_requirement.txt', prompt_inputs,
                                                         json_response=True)
    return response


async def generate_daily_plan_hourly(persona) -> dict[datetime, str]:
    """
    Generate daily_plan_hourly based on the persona's daily_plan

    :param persona: Persona
    :return: Daily plan containing 24 hours, e.g., {datetime("12:00 AM"): "Sleep"}
    """

    prompt_inputs = [
        persona.scratch.get_iss(),
        persona.name,
        persona.scratch.get_daily_plan_str()
    ]

    response = await prompt_manager.async_chat_and_parse('generate_daily_plan_hourly.txt', prompt_inputs,
                                                         json_response=True)

    # The generated list might not include every hour, so post-processing is needed
    time_format = '%I:%M %p'
    full_daily_plan = {
        datetime.strptime(
            re.search(r"\d{1,2}:\d{2} (AM|PM)", time).group(),
            time_format
        ): plan_event for plan_event, time in response
    }

    start_time = datetime.strptime("12:00 AM", time_format)
    end_time = datetime.strptime("11:00 PM", time_format)

    if start_time not in full_daily_plan:
        full_daily_plan[start_time] = 'Sleep'

    current_time = start_time
    prev_plan_event = 'Sleep'

    while current_time <= end_time:
        if current_time not in full_daily_plan:
            full_daily_plan[current_time] = prev_plan_event
        current_time += timedelta(hours=1)

    return full_daily_plan


async def long_term_planning(persona, new_day) -> None:
    """
    Long-term planning. It is actually the plan for the day.
    First create the wake-up hour for the day, then generate the hourly plan for the day

    :param persona: Persona
    :param new_day: Indicates whether it is "First day", "New day" of simulation, or neither
    :return: None
    """

    # Persona's wake-up hour
    wake_up_hour = await generate_wake_up_hour(persona)

    # If the time has not reached the wake-up hour, directly set it as a sleeping event
    current_time = datetime.strptime(datetime_manager.get_current_datetime().strftime("%I:%M %p"), "%I:%M %p")
    if current_time < datetime.strptime(wake_up_hour, "%I:%M %p"):
        duration = datetime.strptime(wake_up_hour, "%I:%M %p") - current_time
        new_event = event_manager.create_event(
            description='Sleeping',
            start_time=datetime_manager.get_current_datetime(),
            duration=duration,
            participants=[persona.name],
            location=persona.scratch.living_area
        )
        persona_manager.set_event_id(persona.name, new_event.event_id)

    # When a new day starts, we need to create a daily plan for the persona
    # daily_plan is a list of strings describing the persona's general schedule for the day
    if new_day == 'First day':
        persona.scratch.daily_plan = await generate_first_daily_plan(persona, wake_up_hour)
    elif new_day == 'New day':
        persona.scratch.daily_plan_requirement = await generate_daily_plan_requirement(persona)
        persona.scratch.daily_plan = await generate_new_daily_plan(persona, wake_up_hour)

    persona.scratch.daily_plan_hourly = await generate_daily_plan_hourly(persona)

    logger.debug(f"[{persona.name}]'s daily plan hourly: {persona.scratch.daily_plan_hourly}")


async def choose_focused_event(persona, retrieved: dict[int, list[MemoryItem]]) -> int:
    """
    Based on the retrieved list, select the event the persona is most likely to focus on first

    :param persona: Persona
    :param retrieved: Retrieved relevant memories, { event_id: [MemoryItem] }
    :return: The ID of the event most likely to be focused on first
    """

    prompt_inputs = [
        persona.scratch.get_iss(),
        datetime_manager.get_current_datetime(return_str=True, str_format="%Y-%m-%d %I:%M %p"),
        persona.scratch.name,
        persona.scratch.get_daily_plan_hourly_str(),
    ]

    retrieved_event_infos = []
    for event_id in retrieved.keys():
        event = event_manager.get_event_by_id(event_id, return_str=True)
        retrieved_event_infos.append(event)

    prompt_inputs.append("\n".join(retrieved_event_infos))

    response = await prompt_manager.async_chat_and_parse('choose_focused_event.txt', prompt_inputs, json_response=True)
    choose_focused_event_id = response.get("event_id")

    return choose_focused_event_id


async def choose_reaction_move(persona, world: World, focused_event_id: int) -> dict | None:
    """
    Choose for the persona to move to a certain place

    :param persona: Persona
    :param world: World
    :param focused_event_id: Focused event ID
    :return: Action to move to a certain place
    """
    prompt_inputs = [
        persona.scratch.get_iss(),
        world.get_flat_world(),
        persona.name,
        # event_manager.get_event_by_id(focused_event_id, return_str=True),
        '',
        persona.scratch.get_daily_plan_hourly_str(),
        datetime_manager.get_current_datetime(return_str=True, str_format="%Y-%m-%d %I:%M %p"),
        persona_manager.get_curr_location_by_name(persona.name)
    ]

    prompt_file_name = 'choose_reaction_move_abnormal.txt' if persona.scratch.abnormal else 'choose_reaction_move.txt'

    for _ in range(Config.max_retries):
        response = await prompt_manager.async_chat_and_parse(prompt_file_name, prompt_inputs, json_response=True)
        if world.is_existed(response.get('location')):
            return {'move': response}

    return None


async def choose_reaction_chat(persona, world: World, focused_event_id: int) -> dict | None:
    """
    Choose who the persona will chat with

    :param persona: Persona
    :param world: World
    :param focused_event_id: Focused event ID
    :return: Who to chat with
    """
    prompt_inputs = [
        persona.scratch.get_iss(),
        world.get_flat_world(),
        persona_manager.get_all_persona_names(),
        persona.name,
        # event_manager.get_event_by_id(focused_event_id, return_str=True),
        '',
        persona.scratch.get_daily_plan_hourly_str(),
        datetime_manager.get_current_datetime(return_str=True, str_format="%Y-%m-%d %I:%M %p"),
    ]

    prompt_file_name = 'choose_reaction_chat_abnormal.txt' if persona.scratch.abnormal else 'choose_reaction_chat.txt'

    for _ in range(Config.max_retries):
        response = await prompt_manager.async_chat_and_parse(prompt_file_name, prompt_inputs, json_response=True)
        if persona_manager.is_existed(response.get('chat')):
            return response

    return None


async def choose_reaction(persona, world: World, focused_event_id: int) -> dict | None:
    """
    Choose the action the persona might perform based on the persona's plan, the state of the world, and the focused event
    move, chat, move_chat, none

    :param persona: Persona
    :param world: World
    :param focused_event_id: Focused event ID
    :return: Action to be executed
    """

    # Randomly select an action
    actions = [choose_reaction_move, choose_reaction_chat, None]
    weights = [Config.plan['move'], Config.plan['chat'], Config.plan['none']]
    random_action = random.choices(actions, weights, k=1)[0]

    if not random_action:
        return None

    return await random_action(persona, world, focused_event_id)


async def plan(persona, world: World, new_day, retrieved: dict[Event, list[MemoryItem]]) -> dict | None:
    """
    Make a plan for the day based on the information obtained from retrieved
    
    :param persona: Persona
    :param world: World
    :param new_day: Whether it is a new day or the first day of simulation: False, "First day", "New day"
    :param retrieved: Retrieved relevant memories, { Event: [MemoryItem] }
    :return: Plan
    """

    # Convert Event in retrieved to event_id
    new_retrieved: dict[int: list[MemoryItem]] = dict()
    for event in retrieved.keys():
        new_retrieved[event.event_id] = retrieved[event]

    logger.debug(f"[{persona.name}] is planning.")

    # If it's a new day, let the persona consider the schedule for the day
    if new_day:
        await long_term_planning(persona, new_day)

    # If the persona still has things to do, skip planning for now
    if persona_manager.is_busy(persona.name):
        return None

    # Perform abnormal behavior based on the abnormal factor
    if random.random() < Config.plan['abnormal_factor']:
        logger.debug(f"[{persona.name}] will exhibit abnormal behavior now.")
        persona.scratch.abnormal = True

    # At this point, persona.scratch.daily_plan already has a value
    # Choose events to focus on based on the current time and daily schedule

    # There will be some events and related memories in retrieved
    ## We need to decide which event to focus on first
    if new_retrieved:
        focused_event_id = await choose_focused_event(persona, new_retrieved)
        ## At this point, we need to decide what action to take for this focused_event_id
        next_plan = await choose_reaction(persona, world, focused_event_id)

    # When new_retrieved is empty
    else:
        ## If the persona is idle, the next plan also needs to be made, but the passed focused_event_id is -1
        next_plan = await choose_reaction(persona, world, -1)

    logger.debug(f"[{persona.name}]'s next plan is {next_plan}.")

    return next_plan
