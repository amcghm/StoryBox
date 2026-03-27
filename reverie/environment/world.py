import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

import yaml
import os
from typing import List, Tuple
from loguru import logger

from reverie.environment.city import City
from reverie.environment.place import Place
from reverie.environment.area import Area
from reverie.environment.object import Object
from reverie.manager.event_manager import event_manager


class World:
    """
    world -> city -> place -> area -> object
    """

    def __init__(self,
                 name: str = None,
                 description: str = None,
                 file_path: str = None,
                 cities: dict[str, City] = None):

        self.name = name
        self.description = description
        self.cities = cities or {}

        if file_path:
            self.load_file(file_path)

    def __getitem__(self, index):
        return self.cities[index]

    def __repr__(self):
        return f"World(name = {self.name}, description = {self.description}, cities = \n{self.cities})"

    def load_file(self, file_path: str) -> bool:
        """
        Load the world from a yaml file

        :param str file_path: File path
        :return: True if loaded successfully; False otherwise
        """

        if os.path.exists(file_path):
            with open(file_path) as f:
                data = yaml.safe_load(f)

            self.name = data.get("name")
            self.description = data.get("description")

            for city_data in data.get("cities", {}):
                city = City(name=city_data["name"], description=city_data["description"])
                for place_data in city_data.get("places", {}):
                    place = Place(name=place_data["name"], description=place_data["description"])
                    for area_data in place_data.get("areas", {}):
                        area = Area(name=area_data["name"], description=area_data["description"])
                        for obj_data in area_data.get("objects", {}):
                            obj = Object(name=obj_data["name"], description=obj_data["description"])
                            area.objects[obj_data["name"]] = obj
                        place.areas[area_data["name"]] = area
                    city.places[place_data["name"]] = place
                self.cities[city_data["name"]] = city

            return True

        return False

    def get_nearby_objects(self, curr_area: str) -> List[str]:
        """
        Get the objects located in the current area based on the given area location.

        :param str curr_area: The current area, e.g., "World:Guangzhou:Yuexiu Park:Children's Playground"
        :return list[str]: A list of objects in the specified area
        """

        curr_world, curr_city, curr_place, curr_area = curr_area.split(":")

        objects = self[curr_city][curr_place][curr_area].objects

        return list(objects.keys())

    def get_nearby_events(self, curr_area: str) -> List[Tuple]:
        """
        Get nearby events based on the current area, sorted by distance in ascending order.

        :param curr_area: The current area, e.g., "World:Guangzhou:Yuexiu Park:Children's Playground"
        :return: A list of nearby events [(event: Event, distance: int)]
        """
        events = []
        all_events = event_manager.get_all_events()
        for event in all_events:
            distance = self.get_distance(curr_area, event.location)
            events.append((event, distance))

        # Remove duplicates; if there are duplicates, choose the one with the smaller distance
        event_dict = {}
        for event, distance in events:
            if event not in event_dict or distance < event_dict[event]:
                event_dict[event] = distance

        events = list(event_dict.items())

        # Sort by distance in ascending order
        events.sort(key=lambda x: x[1])

        return events

    @staticmethod
    def get_distance(location1: str, location2: str) -> int:
        """
        Get the relative distance between two locations.

        :param location1: Location 1, e.g., "World:Guangzhou:Yuexiu Park:Children's Playground"
        :param location2: Location 2, e.g., "World:Shenzhen:Shenzhen Bay Park:Trail"
        :return: The calculated distance
        """
        # Maximum distance
        MAX_DISTANCE = 4

        # Location lists
        location1_ls = location1.split(':')
        location2_ls = location2.split(':')
        n1, n2 = len(location1_ls), len(location2_ls)
        # Ensure location1_ls is shorter
        if n1 > n2:
            location1_ls, location2_ls = location2_ls, location1_ls
            n1, n2 = n2, n1

        # Distance
        distance = 0

        for i in range(n1):
            if location1_ls[i] == location2_ls[i]:
                continue

            # Differences have appeared at this point
            distance += MAX_DISTANCE - i
            break

        # Add the remaining distance
        if n1 == 3 and i == 1:
            distance += MAX_DISTANCE - i - 1
        elif n1 == 4 and i == 1:
            distance += (MAX_DISTANCE - i - 1) + (MAX_DISTANCE - i - 2)
        elif n1 == 4 and i == 2:
            distance += MAX_DISTANCE - i - 1

        if n2 == 3 and i == 1:
            distance += MAX_DISTANCE - i - 1
        elif n2 == 4 and i == 1:
            distance += (MAX_DISTANCE - i - 1) + (MAX_DISTANCE - i - 2)
        elif n2 == 4 and i == 2:
            distance += MAX_DISTANCE - i - 1

        return distance

    def is_existed(self, location: str) -> bool:
        """
        Determine whether a given location string exists in the world.

        :param location: Location string
        :return: True if it exists, False otherwise
        """
        try:
            curr_world, curr_city, curr_place, curr_area = location.split(":")

            if self.cities[curr_city][curr_place][curr_area]:
                return True
        except Exception as e:
            logger.error(f"{location} does not exist. {e}")
            return False

    def get_flat_world(self, with_description: bool = True) -> str:
        """
        Get a flattened representation of the world.
        
        :param with_description: Whether to include local descriptions
        :return: Flattened world string
        """
        ret: list[str] = []

        def _flatten_memory(item, to_now: list[str]):
            # If it is an Area, it means it's ready to be outputted
            if isinstance(item, Area):
                if with_description:
                    location = f"{item.description} \"{':'.join(to_now)}\""
                else:
                    location = f"\"{':'.join(to_now)}\""
                ret.append(location)
                return

            if isinstance(item, World):
                for name, city in item.cities.items():
                    _flatten_memory(city, to_now + [name])
            elif isinstance(item, City):
                for name, place in item.places.items():
                    _flatten_memory(place, to_now + [name])
            elif isinstance(item, Place):
                for name, area in item.areas.items():
                    _flatten_memory(area, to_now + [name])

        _flatten_memory(self, [self.name])

        return '\n'.join(ret)


if __name__ == "__main__":
    world = World()
    world.load_file(f"{project_root}/data/story01/world.yaml")
    # print(world)

    # print(world.get_distance("World:Guangzhou:Yuexiu Park:Children's Playground", "World:Shenzhen:Shenzhen Bay Park:Trail"))
    # print(world.get_distance("World:Guangzhou:Yuexiu Park:Children's Playground", "World:Shenzhen"))
    # print(world.get_distance("World:Guangzhou:Yuexiu Park:Children's Playground", "World:Shenzhen:Shenzhen Bay Park"))
    # print(world.get_distance("World:Guangzhou:Yuexiu Park:Children's Playground", "World:Shenzhen:Yuexiu Park:Children's Playground"))
    # print(world.get_distance("World:Guangzhou:Yuexiu Park:Children's Playground", "World:Shenzhen:Yuexiu Park"))
