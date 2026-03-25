class Object:
    """
    world -> city -> place -> area -> object
    """

    def __init__(self, name: str = None, description: str = None):
        self.name = name
        self.description = description

    def __repr__(self):
        return f"Object(name = {self.name}, description = {self.description})"


if __name__ == "__main__":
    object = Object("123", "Object")
    print(object)
