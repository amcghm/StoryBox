from loguru import logger

from reverie.environment.world import World
from reverie.persona.memory.memory_item import MemoryItem
from reverie.manager.persona_manager import persona_manager


def perceive(persona, world: World) -> list:
    """
    Perceive the events around the persona and save them into memory, including events and spaces.

    We first perceive events near the persona. If many events occur in that range,
    we will select the closest <att_bandwidth> events.

    Finally, we check if these events are new, which is determined by <retention>.
    If they are new, we will save these events and return the corresponding <ConceptNode> instances.

    :param persona: An instance representing the current persona
    :param world: An instance representing the world the current persona is in

    :return list[Event]: A list containing the newly perceived events.
    """


    # Spatial perception
    logger.debug(f"[{persona.name}] is perceiving the objects around...")
    ## Get nearby objects around the current persona's location
    curr_location = persona_manager.get_curr_location_by_name(persona.name)
    objects = world.get_nearby_objects(curr_location)

    ## Attach objects to the persona
    curr_world, curr_city, curr_place, curr_area = curr_location.split(":")
    persona.spatial_mem.memory[curr_world][curr_city][curr_place][curr_area] = objects

    logger.debug(f"[{persona.name}] perceives that there are {objects} around, and then updates the memory.")

    # Event perception
    logger.debug(f"[{persona.name}] is perceiving the events around...")
    ## Get nearby events around the current persona's location
    perceived_events = world.get_nearby_events(curr_location)
    ## Select the closest events based on <att_bandwidth>
    perceived_events = perceived_events[:persona.scratch.att_bandwidth]
    ## Keep only the 0th element of the tuple
    perceived_events = [event[0] for event in perceived_events]

    # Store events
    ## Need to retrieve some old memories from the persona
    retained_mem = persona.long_term_mem.event_mem[:persona.scratch.retention]

    ## At this point, the elements in events are of Event type and need to be converted to MemoryItem type
    perceived_mem = []
    for event in perceived_events:
        memory_item = MemoryItem(content=event.get_str(), memory_type='event')
        perceived_mem.append(memory_item)

    ## Compare retained_mem and perceived_mem, add those not in retained_mem to long-term memory, and return them as an event list
    ret_events = []
    for i, mem in enumerate(perceived_mem):
        for retained_mem_item in retained_mem:
            if mem.content == retained_mem_item.content:
                break
        else:
            ret_events.append(perceived_events[i])
            ## Add the event to the persona's long-term memory
            persona.long_term_mem.event_mem.append(mem)

    ## At this point, there might be some duplicated memories in the persona's long-term memory, so summarization is needed
    # logger.debug(f"[{persona.name}] is summarizing memories.")
    # persona.long_term_mem.summarize_memories()

    return ret_events
