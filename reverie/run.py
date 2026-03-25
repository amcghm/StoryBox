import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

import os
import asyncio
from config.config import Config

Config.save_to_json(f"{Config.output_dir}/config.json")

# Delete db.sqlite first
if os.path.exists(Config.database_url):
    os.remove(Config.database_url)

from reverie.agent.storyteller import Storyteller
from config.logging_config import logger
from reverie.manager.datetime_manager import datetime_manager
from reverie.manager.persona_manager import persona_manager
from reverie.persona.persona import Persona
from reverie.environment.world import World


async def step_all_personas(world: World, all_personas: list[Persona], new_day):
    tasks = [
        persona.step(world, new_day=new_day)
        for persona in all_personas
    ]
    await asyncio.gather(*tasks)


async def reverie_task():
    logger.debug(f'Running with story: {Config.story_name}')
    # Load world
    world = World()
    world.load_file(f"{Config.story_dir}/world.yaml")

    # Load all personas
    persona_folder = f"{Config.story_dir}/personas"
    persona_names = os.listdir(persona_folder)
    for persona_name in persona_names:
        persona = Persona(persona_name, f"{persona_folder}/{persona_name}")
        persona_manager.add_persona(persona)

    logger.debug("----- Start -----")

    all_personas = persona_manager.get_all_personas()

    for i in range(Config.max_iteration):
        logger.debug(
            f"----- iteration: {i + 1}, current_time: {datetime_manager.get_current_datetime(return_str=True)}")
        new_day = 'First day' if i == 0 else 'New day' if datetime_manager.is_new_day() else False

        for persona in all_personas:
            logger.debug(f"----- [Start persona] {persona.name} -----")
            try:
                await persona.step(world, new_day=new_day)
            except Exception as e:
                logger.exception(e)
                continue

        # Parallel execution
        # try:
        #     await step_all_personas(world, all_personas, new_day)
        # except Exception as e:
        #     logger.error(e)

        hours, minutes, seconds = map(int, Config.time_increment_per_iteration.split(':'))
        datetime_manager.advance_datetime(hours=hours, minutes=minutes, seconds=seconds)
        logger.debug('--------------------')

    # Storyteller starts creating
    storyteller = Storyteller(Config.story_dir, Config.output_dir)
    storyteller.summarize_daily_by_persona()
    storyteller.generate_story_title()
    storyteller.generate_story_type()
    storyteller.generate_story_background()
    storyteller.generate_story_themes()
    storyteller.generate_story_chapters()
    storyteller.generate_story_conflicts()
    storyteller.generate_story_plot_points()
    storyteller.generate_story()
    storyteller.save()


if __name__ == '__main__':
    asyncio.run(reverie_task())
