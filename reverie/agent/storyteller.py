import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

import ast
import json
import os
import sqlite3
from datetime import datetime, timedelta
from loguru import logger

from reverie.common.utils import format_time_from_db
from reverie.config.config import Config
from reverie.environment.world import World
from reverie.manager.faiss_manager import faiss_manager
from reverie.manager.prompt_manager import prompt_manager
from reverie.persona.persona import Persona


class Storyteller:
    def __init__(self, story_dir: str, output_dir: str):
        # Output directory
        self.output_dir: str = output_dir
        # Database connection
        self.conn = None
        # Story world
        self.world: World = None
        # Story personas
        self.personas: dict[str, Persona] = {}
        # Story title
        self.story_title: str = ''
        # Story type
        self.story_type: str = ''
        # Story background
        self.story_background: str = ''
        # Story themes
        self.story_themes: list[str] = []
        # Story chapters
        self.story_chapters: list[dict] = []
        # Story conflicts
        self.story_conflicts: dict[str, list] = {}
        # Story plot points
        self.story_plot_points: dict[str, list] = {}
        # Final story, by chapters
        self.story: list[list] = []

        # Event summaries [ [ date, { persona_name: event_summary } ] ]
        self.event_summaries: list[list[str, dict[str, str]]] = []
        # Summaries of events within the window [ [ date, summary ] ]
        self.days_in_window_summaries: list[str, str] = []

        # Initialization
        self._connect_with_db(f"{output_dir}/db.sqlite")
        self._load_world(story_dir)
        self._load_personas(story_dir)
        self._load_novelist(f"{story_dir}/novelist.json")

    def _connect_with_db(self, db_path):
        self.conn = sqlite3.connect(db_path)

    def _load_world(self, story_dir):
        self.world = World()
        self.world.load_file(f"{story_dir}/world.yaml")

    def _load_personas(self, story_dir):
        persona_folder = f"{story_dir}/personas"
        persona_names = os.listdir(persona_folder)
        for persona_name in persona_names:
            persona = Persona(persona_name, f"{persona_folder}/{persona_name}")
            self.personas[persona_name] = persona

    def _load_novelist(self, file_path):
        if os.path.exists(file_path):
            with open(file_path) as f:
                data = json.load(f)

            for k, v in data.items():
                if hasattr(self, k):
                    setattr(self, k, v)

    def summarize_daily_by_persona(self):
        cursor = self.conn.cursor()
        datetime_now = datetime.strptime(Config.start_datetime, "%Y-%m-%d %I:%M %p")

        while True:
            have_content = False
            today = datetime_now.strftime("%Y-%m-%d")

            today_event_summaries = [today, {}]

            for persona_name in self.personas.keys():
                cursor.execute("""
                               SELECT *
                               FROM event
                               WHERE participants LIKE ?
                                 AND start_time LIKE ?
                               """, (f"%{persona_name}%", f"{today}%"))

                events = cursor.fetchall()

                if events:
                    have_content = True

                event_sentences = []

                # Reorganize events
                for event in events:
                    event_sentence = self._format_event_as_sentence(*event)
                    event_sentences.append(event_sentence)

                # Summarize
                if event_sentences:
                    prompt_inputs = [
                        persona_name,
                        self.personas[persona_name].scratch.get_iss(),
                        today,
                        "\n".join(event_sentences),
                    ]

                    response = prompt_manager.chat_and_parse('summarize_daily_by_persona.txt',
                                                             prompt_inputs,
                                                             json_response=True,
                                                             required_keys=['summary'])

                    if response.get('summary'):
                        logger.info(f"summarize_daily_by_persona - {today} - {persona_name} - {response['summary']}")
                        today_event_summaries[1][persona_name] = response['summary']

            if today_event_summaries[1]:
                self.event_summaries.append(today_event_summaries)

            if not have_content:
                break

            datetime_now += timedelta(days=1)

    def _format_event_as_sentence(self,
                                  event_id,
                                  description,
                                  detail,
                                  start_time,
                                  end_time,
                                  duration,
                                  participants,
                                  location):
        """
        Integrate the elements of an event into a complete descriptive sentence.

        :param event_id: Event ID (int or str)
        :param description: Brief description of the event (str)
        :param detail: Detailed description of the event (str)
        :param start_time: Start time (str)
        :param end_time: End time (str)
        :param duration: Duration (str)
        :param participants: List of participants (list[str])
        :param location: Location of the event (str)
        :return: Integrated complete sentence (str)
        """

        # Convert time format to "%Y-%m-%d %I:%M %p"
        start_time = format_time_from_db(start_time)
        end_time = format_time_from_db(end_time)

        participants = ast.literal_eval(participants)

        # Convert participants to natural language description
        participant_text = ", ".join(participants) if participants else "No participants"

        # Integrate start and end times
        time_text = f"from {start_time} to {end_time}" if start_time and end_time else ""

        # Integrate location information
        location_text = f"at <{location}>" if location else ""

        # If it is a conversation, the format of the detail needs to be modified
        if 'is chatting with' in description:
            chat_history = ast.literal_eval(detail)
            detail = [f"{speaker} to {listener}: {utterance}" for speaker, listener, utterance in chat_history]

        # Use templating to construct the event sentence
        event_sentence = (
            f"Event '{description}' occurred {time_text} {location_text}. "
            f"The event involved {participant_text}. Details: {detail if detail else 'null'}."
        )

        # Remove extra spaces to keep it fluent
        return " ".join(event_sentence.split())

    def generate_story_title(self) -> None:
        if self.story_title:
            logger.error(f"Story title already exists: '{self.story_title}'")
            return

        # Sliding window
        i = 0
        window_of_day = Config.storyteller['window_of_day']
        while i * window_of_day < len(self.event_summaries):
            # Organize the string format of events within the window
            window_event_summaries = self.event_summaries[i * window_of_day: (i + 1) * window_of_day]
            window_event_summaries_str = ''
            for date, d in window_event_summaries:
                window_event_summaries_str += f'[{date}]\n'
                for name, event_summary in d.items():
                    window_event_summaries_str += f"{name}: {event_summary}\n"

            prompt_inputs = [
                '\n'.join(self.days_in_window_summaries),
                window_event_summaries_str,
                self.story_title
            ]

            response = prompt_manager.chat_and_parse('generate_story_title.txt',
                                                     prompt_inputs,
                                                     json_response=True,
                                                     required_keys=['story_title'])
            self.story_title = response['story_title']

            logger.info(f"generate_story_title - {self.story_title}")

            days_in_window_summary = self.summarize_days_in_window(window_event_summaries)
            self.days_in_window_summaries.append(days_in_window_summary)

            i += 1

    def summarize_days_in_window(self, window_event_summaries: list) -> str:
        window_event_summaries_str = ''
        for date, d in window_event_summaries:
            window_event_summaries_str += f'[{date}]\n'
            for name, event_summary in d.items():
                window_event_summaries_str += f"{name}: {event_summary}\n"

        prompt_inputs = [
            window_event_summaries_str,
        ]

        response = prompt_manager.chat_and_parse('summarize_days_in_window.txt',
                                                 prompt_inputs,
                                                 json_response=True,
                                                 required_keys=['summary'])
        date_range = f"From {window_event_summaries[0][0]} to {window_event_summaries[-1][0]}:"

        logger.info(f"summarize_days_in_window - {date_range + response['summary']}")

        return date_range + response['summary']

    def generate_story_type(self) -> None:
        if self.story_type:
            logger.error(f"Story type already exists: '{self.story_type}'")
            return

        # Generate story_type based on self.days_in_window_summaries and self.story_title
        prompt_inputs = [
            '\n'.join(self.days_in_window_summaries),
            self.story_title
        ]

        response = prompt_manager.chat_and_parse('generate_story_type.txt',
                                                 prompt_inputs,
                                                 json_response=True,
                                                 required_keys=['story_type'])
        self.story_type = response['story_type']

        logger.info(f"generate_story_type - {self.story_type}")

    def generate_story_background(self) -> None:
        if self.story_background:
            logger.error(f"Story background already exists: '{self.story_background}'")
            return

        # Generate story_background based on self.days_in_window_summaries, self.story_title, and self.story_type
        prompt_inputs = [
            '\n'.join(self.days_in_window_summaries),
            self.story_title,
            self.story_type
        ]

        response = prompt_manager.chat_and_parse('generate_story_background.txt',
                                                 prompt_inputs,
                                                 json_response=True,
                                                 required_keys=['story_background'])
        self.story_background = response['story_background']

        logger.info(f"generate_story_background - {self.story_background}")

    def generate_story_themes(self, n: int = 3) -> None:
        if self.story_themes:
            logger.error(f"Story themes already exists: '{self.story_themes}'")
            return

        prompt_inputs = [
            '\n'.join(self.days_in_window_summaries),
            self.story_title,
            self.story_type,
            self.story_background,
            n
        ]

        response = prompt_manager.chat_and_parse('generate_story_themes.txt', prompt_inputs, json_response=True)
        self.story_themes = response

        logger.info(f"generate_story_themes - {self.story_themes}")

    def generate_story_chapters(self, n: int = 5) -> None:
        if self.story_chapters:
            logger.error(f"Story chapters already exists: '{self.story_chapters}'")
            return

        prompt_inputs = [
            '\n'.join(self.days_in_window_summaries),
            self.story_title,
            self.story_type,
            self.story_background,
            self.story_themes,
            n
        ]

        response = prompt_manager.chat_and_parse('generate_story_chapters.txt', prompt_inputs, json_response=True)
        self.story_chapters = response[:n]

        logger.info(f"generate_story_chapters - {self.story_chapters}")

    def generate_story_conflicts(self, n: int = 10) -> None:
        if self.story_conflicts:
            logger.error(f"Story conflicts already exists: '{self.story_conflicts}'")
            return

        prompt_inputs = [
            '\n'.join(self.days_in_window_summaries),
            self.story_title,
            self.story_type,
            self.story_background,
            self.story_themes,
            '\n'.join([f"Chapter {i + 1}: {chapter['title']}: {chapter['summary']}"
                       for i, chapter in enumerate(self.story_chapters)]),
            n
        ]

        response = prompt_manager.chat_and_parse('generate_story_conflicts.txt', prompt_inputs, json_response=True)
        self.story_conflicts = response

        logger.info(f"generate_story_conflicts - {self.story_conflicts}")

    def generate_story_plot_points(self, n: int = 5) -> None:
        if self.story_plot_points:
            logger.error(f"Story plot points already exists: '{self.story_plot_points}'")
            return

        story_conflict_input = ''
        for i, chapter in enumerate(self.story_chapters):
            story_conflict_input += (f"[Chapter {i + 1}]\n"
                                     f"title: {chapter['title']}\n"
                                     f"summary: {chapter['summary']}\n")

            if f"Chapter {i + 1}" in self.story_conflicts:
                story_conflict_input += f"conflict: {self.story_conflicts[f'Chapter {i + 1}']}\n"

            story_conflict_input += '\n'

        prompt_inputs = [
            '\n'.join(self.days_in_window_summaries),
            self.story_title,
            self.story_type,
            self.story_background,
            self.story_themes,
            story_conflict_input,
            n
        ]

        response = prompt_manager.chat_and_parse('generate_story_plot_points.txt', prompt_inputs, json_response=True)
        self.story_plot_points = response

        logger.info(f"generate_story_plot_points - {self.story_plot_points}")

    def generate_story(self) -> None:
        """
        Generate the story. Conflicts and plot points for each chapter have been generated previously. First, generate content based on these two, and then organize it into complete chapters.
        :return: None
        """
        # Store the summaries of chapters generated historically
        chapter_summaries = []
        chapter_summaries_str = ''

        for i, chapter in enumerate(self.story_chapters):
            if chapter_summaries:
                chapter_summaries_str += (f"Chapter {i - 1}: {self.story_chapters[i - 1]['title']}\n"
                                          f"Chapter summary: {chapter_summaries[-1]}\n\n")

            plot_contents = self.generate_plot_content(i, chapter_summaries_str)
            chapter_content = '\n'.join(plot_contents)

            self.story.append([f"Chapter {i + 1}: {chapter['title']}", chapter_content])

            logger.info(f"generate_story - Chapter {i + 1}: {chapter['title']} - {chapter_content}")

            chapter_summary = self.summarize_chapter(chapter_content)
            chapter_summaries.append(chapter_summary)

    def generate_plot_content(self, chapter_i: int, chapter_summaries_str) -> list[str]:
        """
        Generate plot content, main body.
        :param chapter_i: The i-th chapter
        :param chapter_summaries_str: Summaries of chapters generated historically
        :return: plot_contents
        """

        plot_contents = []
        for i, plot_point in enumerate(self.story_plot_points.get(f"Chapter {chapter_i + 1}")):
            relevant_events = faiss_manager.query(plot_point, k=5)

            prompt_inputs = [
                self.story_title,
                self.story_type,
                self.story_background,
                self.story_themes,
                self.story_chapters,
                chapter_i + 1,
                chapter_summaries_str,
                i,
                '\n'.join(plot_contents),
                plot_point,
                relevant_events
            ]

            response = prompt_manager.chat_and_parse('generate_plot_content.txt',
                                                     prompt_inputs,
                                                     json_response=True,
                                                     required_keys=['plot'])
            plot_content = response.get("plot")
            plot_contents.append(plot_content)

        return plot_contents

    def summarize_chapter(self, chapter_content) -> str:
        prompt_inputs = [
            chapter_content
        ]

        response = prompt_manager.chat_and_parse('summarize_chapter.txt',
                                                 prompt_inputs,
                                                 json_response=True,
                                                 required_keys=['summary'])

        logger.info(f"summarize_chapter - {response.get('summary')}")

        return response.get('summary')

    def get_story(self, with_title: bool = False) -> str:
        story = f"{self.story_title}\n\n" if with_title else ''
        for chapter, content in self.story:
            story += f"[{chapter}]\n{content}\n\n"

        return story

    def save(self) -> None:
        data = {
            'story_title': self.story_title,
            'story_type': self.story_type,
            'story_background': self.story_background,
            'story_themes': self.story_themes,
            'story_chapters': self.story_chapters,
            'story_conflicts': self.story_conflicts,
            'story_plot_points': self.story_plot_points,
            'story': self.get_story()
        }

        with open(f"{self.output_dir}/story.json", 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    logger.debug(f'Running with story: {Config.story_name}')
    # If you only want to run this part, you need to change story_name and output_dir in Config
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
