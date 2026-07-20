from .declaration import Declaration


class Environment:
    """
    Environment: a collection of declarations (axioms, theorems, etc.) with unique names.
    """

    def __init__(self):
        self.declarations: dict[str, Declaration] = {}

    def add(self, declaration: Declaration):
        if declaration.name in self.declarations:
            raise ValueError(f"Declaration with name '{declaration.name}' already exists.")
        self.declarations[declaration.name] = declaration

    def get(self, name: str) -> Declaration | None:
        return self.declarations.get(name)

    def update(self, other: Environment):
        self.declarations.update(other.declarations)

    def items(self):
        return self.declarations.items()
