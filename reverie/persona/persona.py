from loguru import logger

from reverie.environment.world import World
from reverie.manager.persona_manager import persona_manager
from reverie.persona.memory.spatial_memory import SpatialMemory
from reverie.persona.memory.long_term_memory import LongTermMemory
from reverie.persona.memory.scratch import Scratch

from reverie.persona.cognitive.perceive import perceive
from reverie.persona.cognitive.retrieve import retrieve
from reverie.persona.cognitive.plan import plan
from reverie.persona.cognitive.execute import execute
from reverie.persona.cognitive.reflect import reflect
from reverie.persona.cognitive.detail import detail


class Persona:
    def __init__(self, name, folder_mem_saved=None):
        # Persona name
        self.name = name

        # Persona's scratch
        scratch_saved = f"{folder_mem_saved}/scratch.json"
        self.scratch = Scratch(scratch_saved)

        # Persona's spatial memory
        f_spatial_mem_saved = f"{folder_mem_saved}/spatial_memory.json"
        self.spatial_mem = SpatialMemory(f_spatial_mem_saved)

        # Persona's long-term memory
        f_long_term_mem_saved = f"{folder_mem_saved}/long_term_memory.json"
        self.long_term_mem = LongTermMemory(f_long_term_mem_saved)

    def save(self, save_folder):
        f_spatial_mem = f"{save_folder}/spatial_memory.json"
        self.spatial_mem.save(f_spatial_mem)

        f_scratch = f"{save_folder}/scratch.json"
        self.scratch.save(f_scratch)

    def perceive(self, world):
        """
        Perceive nearby events around the persona and store them in memory,
        including event and spatial information.

        We first perceive events near the persona. If many events happen
        within range, we keep the closest <att_bandwidth> events.

        Finally, we check whether these events are new, based on <retention>.
        If they are new, we store them and return the corresponding
        <ConceptNode> instances.

        :param world: An instance representing the world where the persona is.

        :return list[Event]: A list of newly perceived events.
        """
        return perceive(self, world)

    def retrieve(self, perceived):
        """
        Return memories related to the perceived events for this persona.

        :param perceived: A perceived event or string.
        :return: A dictionary where values are lists of memories.
        """
        return retrieve(self, perceived)

    async def plan(self, world: World, new_day, retrieved):
        """
        Create a daily plan based on information from retrieved memories.

        :param world: The world.
        :param new_day: Whether it is a new day, or the first simulated day:
            False, "First day", "New day".
        :param retrieved: Retrieved related memories, { event_id: [MemoryItem] }.
        :return: The generated plan.
        """
        return await plan(self, world, new_day, retrieved)

    async def execute(self, world, plan_dict):
        """
        Execute a plan.

        :param world: The world.
        :param plan_dict: The plan.
        :return: Whether execution succeeds.
        """

        return await execute(self, world, plan_dict)

    async def reflect(self):
        """
        Review the persona's memories and generate new thoughts.
        This is intended to run once every evening.

        :return: None
        """
        await reflect(self)

    async def detail(self):
        """
        If the persona is currently busy, the activity may be too plain,
        so this adds a more detailed description of that activity.
        :return: None
        """

        await detail(self)

    async def step(self, world: World, new_day: str = None):
        """
        Main workflow.
        
        :param world: The world.
        :param new_day: Whether it is a new day.
        :return: None
        """
        if not persona_manager.is_busy(self.name):
            perceived = self.perceive(world)
            retrieved = self.retrieve(perceived)
            next_plan = await self.plan(world, new_day, retrieved)
            if next_plan:
                await self.execute(world, next_plan)
                # await self.reflect()

        # Add detailed descriptions for the persona's current activity.
        await self.detail()
