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
        # 角色的姓名
        self.name = name

        # 角色的初始设定
        scratch_saved = f"{folder_mem_saved}/scratch.json"
        self.scratch = Scratch(scratch_saved)

        # 角色的空间记忆
        f_spatial_mem_saved = f"{folder_mem_saved}/spatial_memory.json"
        self.spatial_mem = SpatialMemory(f_spatial_mem_saved)

        # 角色的长期记忆
        f_long_term_mem_saved = f"{folder_mem_saved}/long_term_memory.json"
        self.long_term_mem = LongTermMemory(f_long_term_mem_saved)

    def save(self, save_folder):
        f_spatial_mem = f"{save_folder}/spatial_memory.json"
        self.spatial_mem.save(f_spatial_mem)

        f_scratch = f"{save_folder}/scratch.json"
        self.scratch.save(f_scratch)

    def perceive(self, world):
        """
        感知角色周围的事件，并将其保存到记忆中，包括事件和空间。

        我们首先感知角色附近的事件，如果在该范围内发生了很多事件，
        我们将选择最近的 <att_bandwidth> 个事件。

        最后，我们检查这些事件是否是新的，这由 <retention> 决定。
        如果它们是新的，我们将保存这些事件并返回对应的 <ConceptNode> 实例。

        :param world: 一个表示当前角色所处世界的实例

        :return list[Event]: 一个包含感知到的新的事件的列表。
        """
        return perceive(self, world)

    def retrieve(self, perceived):
        """
        根据角色和感受到的事件，返回与这些事件相关的记忆列表
        :param perceived: 感受到的 事件 或 字符串
        :return: 记忆组成的列表的字典
        """
        return retrieve(self, perceived)

    async def plan(self, world: World, new_day, retrieved):
        """
        根据 retrieved 所得到的信息，进行一天的计划
        :param world: 世界
        :param new_day: 是否为新的一天，或模拟的第一天：False, "First day", "New day"
        :param retrieved: 检索到的相关记忆, { event_id: [MemoryItem] }
        :return: 计划
        """
        return await plan(self, world, new_day, retrieved)

    async def execute(self, world, plan_dict):
        """
        执行计划
        :param world: 世界
        :param plan_dict: 计划
        :return: 是否执行成功
        """

        return await execute(self, world, plan_dict)

    async def reflect(self):
        """
        回顾人物的记忆，并基于此产生新想法，设定为每天晚上执行一次反思
        :return: None
        """
        await reflect(self)

    async def detail(self):
        """
        如果人物正在忙事情，可能这个事情是很朴素的，那么需要对这个事情进行细节化的描述
        :return: None
        """

        await detail(self)

    async def step(self, world: World, new_day: str = None):
        """
        主流程
        :param world: 世界
        :param new_day: 是否为新的一天
        :return:
        """
        if not persona_manager.is_busy(self.name):
            perceived = self.perceive(world)
            retrieved = self.retrieve(perceived)
            next_plan = await self.plan(world, new_day, retrieved)
            if next_plan:
                await self.execute(world, next_plan)
                # await self.reflect()

        # 对角色当前所做的事件进行细节化的描述
        await self.detail()
