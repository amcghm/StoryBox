from reverie.environment.area import Area


class Place:
    """
    world -> city -> place -> area -> object
    """

    def __init__(self,
                 name: str = None,
                 description: str = None,
                 areas: dict[str, Area] = None):
        self.name = name
        self.description = description
        self.areas = areas or {}

    def __getitem__(self, area_name: str) -> Area:
        return self.areas[area_name]

    def __repr__(self):
        return f"Place(name = {self.name}, description = {self.description}, areas = {self.areas})"


if __name__ == "__main__":
    place = Place("123", "Place")
    print(place)
