from reverie.environment.object import Object


class Area:
    """
    world -> city -> place -> area -> object
    """

    def __init__(self,
                 name: str = None,
                 description: str = None,
                 objects: dict[str, Object] = None):
        self.name = name
        self.description = description
        self.objects = objects or {}

    def __getitem__(self, object_name: str) -> Object:
        return self.objects[object_name]

    def __repr__(self):
        return f"Area(name = {self.name}, description = {self.description}, objects = {self.objects})"


if __name__ == "__main__":
    area = Area("123", "Area")
    print(area)
