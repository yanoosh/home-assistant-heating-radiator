from typing import List, Callable


class Patch:
    def __init__(self, change: float, conditions: Callable):
        self._change = change
        self._conditions = conditions

    def get_change(self) -> float:
        if self._conditions():
            return self._change
        else:
            return 0


class Patches:
    def __init__(self, patches: List[Patch]) -> None:
        self._patches = patches

    def get_change(self) -> float:
        return sum(patch.get_change() for patch in self._patches)


class PatchesEmpty(Patches):
    def __init__(self):
        pass

    def get_change(self) -> float:
        return 0
