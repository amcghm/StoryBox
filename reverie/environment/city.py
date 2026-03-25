from reverie.environment.place import Place


class City:
    """
    world -> city -> place -> area -> item
    """

    def __init__(self,
                 name: str = None,
                 description: str = None,
                 places: dict[str, Place] = None):
        self.name = name
        self.description = description
        self.places = places or {}

    def __getitem__(self, place_name: str) -> Place:
        return self.places[place_name]

    def __repr__(self):
        return f"City(name = {self.name}, description = {self.description}, places = {self.places})"


if __name__ == "__main__":
    city = City("123", "City")
    print(city)
