import os
import json
import yaml
from pathlib import Path


class SpatialMemory:
    """
    Spatial memory
    """

    def __init__(self, f_saved):
        # Use hierarchical memory
        self.memory = {}

        # If the file exists, read it directly
        self.load_file(f_saved)

    def load_file(self, file_path: str):
        """
        Read from a file, supports json and yaml formats.

        :param str file_path: File path
        """

        if os.path.exists(file_path):
            with open(file_path) as f:
                if file_path.endswith(".json"):
                    self.memory = json.load(f)
                elif file_path.endswith(".yaml") or file_path.endswith(".yml"):
                    self.memory = yaml.safe_load(f)

    def get_memory(self, flatten: bool = True) -> str:
        """
        Print spatial memory.
        :param flatten: Whether to flatten the memory
        :return: Spatial memory
        """

        if flatten:
            flat_memory = self.flatten_memory()
            return '\n'.join(flat_memory)

        ret = ""

        def _print_memory(memory=None, depth=0) -> None:
            """
            The actual function that outputs spatial memory
            :param memory: Spatial memory
            :param depth: Depth of the tree memory
            :return: None
            """
            nonlocal ret

            dash = " >" * depth

            if isinstance(memory, list):
                if memory:
                    ret += f"{dash} {memory} \n"
                    return

            for key, val in memory.items():
                if key:
                    ret += f"{dash} {key} \n"
                _print_memory(val, depth + 1)

        _print_memory(self.memory, 0)

        return ret

    def flatten_memory(self) -> list[str]:
        """
        Flatten the hierarchical memory
        :return: Flattened memory
        """
        ret: list[str] = []

        # DFS
        def _flatten_memory(memory: dict | list, to_now: list):
            # If it is a list type, it means it has reached the objects layer
            if isinstance(memory, list):
                location = ':'.join(to_now)
                ret.append(location)
                return

            for key in memory.keys():
                _flatten_memory(memory[key], to_now + [key])

        _flatten_memory(self.memory, [])

        return ret

    def save(self, output_file_path: str):
        """
        Save spatial memory.

        :param str output_file_path: File path to save
        """

        with open(output_file_path, "w") as f:
            json.dump(self.memory, f, indent=2, ensure_ascii=False)

    def get_accessible_cities(self, curr_world: str) -> str:
        """
        Output the cities accessible from the current world

        :param str curr_world: Current world, e.g., "World"
        :return str: Cities accessible from the current world
        """

        x = ", ".join(list(self.memory[curr_world].keys()))
        return x

    def get_accessible_city_places(self, curr_city: str) -> str:
        """
        Output the places accessible from the current city

        :param str curr_city: Current city, e.g., "World:Guangzhou"
        :return str: Places accessible from the current city
        """

        curr_world, curr_city = curr_city.split(":")

        if not curr_city:
            return ""
        x = ", ".join(list(self.memory[curr_world][curr_city].keys()))
        return x

    def get_accessible_city_place_areas(self, curr_place: str) -> str:
        """
        Output the areas accessible from the current place

        :param str curr_place: Current place, e.g., "World:Guangzhou:Yuexiu Park"
        :return str: Areas accessible from the current place
        """

        curr_world, curr_city, curr_place = curr_place.split(":")

        if not curr_place:
            return ""

        x = ", ".join(list(self.memory[curr_world][curr_city][curr_place].keys()))
        return x

    def get_accessible_city_place_area_objects(self, curr_area: str) -> str:
        """
        Output the objects accessible from the current area

        :param str curr_area: Current area, e.g., "World:Guangzhou:Yuexiu Park:Children's Playground"
        :return str: Objects accessible from the current area
        """

        curr_world, curr_city, curr_place, curr_area = curr_area.split(":")

        if not curr_area:
            return ""

        x = ", ".join(list(self.memory[curr_world][curr_city][curr_place][curr_area]))
        return x


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[3]
    spatial_memory_path = f"{project_root}/data/school/personas/Zehao Chen/spatial_memory.json"
    spatial_memory = SpatialMemory(spatial_memory_path)
    spatial_memory.get_memory()
    # print(spatial_memory.get_accessible_city_place_area_objects("World:Guangzhou:Yuexiu Park:Children's Playground"))
