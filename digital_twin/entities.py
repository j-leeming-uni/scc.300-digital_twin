from .state import Entity


class BranchState(Entity):
    vehicle_count: int
    light: str


class JunctionState(Entity):
    north: BranchState
    south: BranchState
    east: BranchState
    west: BranchState
