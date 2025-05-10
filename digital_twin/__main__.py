import sys
import time
from contextlib import suppress
from pathlib import Path
from pprint import pprint

from digital_twin import config, colour, neighbours
from digital_twin.config import Config
from digital_twin.entities import JunctionState
from digital_twin.state import WorldState, Connection

HINTS_DIR = Path('hints')

steps_since_north = 0
steps_since_east = 0
steps_since_south = 0
steps_since_west = 0


def get_next_flow(conn: Connection, junction: JunctionState):
    north_count = junction.north.vehicle_count.get(conn)
    south_count = junction.south.vehicle_count.get(conn)
    east_count = junction.east.vehicle_count.get(conn)
    west_count = junction.west.vehicle_count.get(conn)

    north_south = north_count + south_count
    east_west = east_count + west_count
    max_count = max(north_south, east_west)
    if max_count == 0:
        return "0", "0", "0", "0"
    if north_south > east_west:
        return "1", "0", "1", "0"
    return "0", "1", "0", "1"


THRESHOLD = 5


def update(conn: Connection, cfg: Config):
    global steps_since_north
    global steps_since_east
    global steps_since_south
    global steps_since_west

    junction = JunctionState(f'junction-{cfg.junction_id}'.encode())

    north, east, south, west = get_next_flow(conn, junction)

    for i, direction in enumerate(['north', 'east', 'south', 'west']):
        neighbour_id = neighbours.NEIGHBOURS[direction]
        if neighbour_id is None:
            continue
        neighbour_hints = []
        with suppress(FileNotFoundError):
            hints_file = HINTS_DIR / f'junction-{neighbour_id}'
            neighbour_hints = hints_file.read_text().split()
        if cfg.protections.repudiation:
            if len(neighbour_hints) != 5:
                print(f"Malformed hint")
                continue
            signature, *neighbour_hints = neighbour_hints
            if signature != str(neighbour_id):
                print(f"Invalid signature: {signature}")
                continue
        if len(neighbour_hints) != 4:
            print(f"Malformed hint")
            continue
        print(f"Neighbour {neighbour_id} hints: {neighbour_hints[:4]}")
        hint = neighbour_hints[i]
        if hint == "0":
            continue
        match direction:
            case 'north':
                steps_since_north = max(steps_since_north, THRESHOLD - 1)
            case 'east':
                steps_since_east = max(steps_since_east, THRESHOLD - 1)
            case 'south':
                steps_since_south = max(steps_since_south, THRESHOLD - 1)
            case 'west':
                steps_since_west = max(steps_since_west, THRESHOLD - 1)

    if steps_since_north > THRESHOLD:
        north = "1"
        east = "0"
        west = "0"
    elif steps_since_east > THRESHOLD:
        east = "1"
        north = "0"
        south = "0"
    elif steps_since_south > THRESHOLD:
        south = "1"
        east = "0"
        west = "0"
    elif steps_since_west > THRESHOLD:
        west = "1"
        north = "0"
        south = "0"

    def apply(direction, steps_since):
        if direction == "1":
            return 0, colour.GREEN
        return steps_since + 1, colour.RED

    steps_since_north, north_colour = apply(north, steps_since_north)
    steps_since_east, east_colour = apply(east, steps_since_east)
    steps_since_south, south_colour = apply(south, steps_since_south)
    steps_since_west, west_colour = apply(west, steps_since_west)

    print(f"Setting lights: {north_colour}N{east_colour}E{south_colour}S{west_colour}W{colour.RESET}")

    if cfg.protections.dos:
        HINTS_DIR.mkdir(exist_ok=True, parents=True)
    with suppress(FileNotFoundError):
        hints_file = HINTS_DIR / f'junction-{cfg.junction_id}'
        message = f"{north} {east} {south} {west}"
        if cfg.protections.repudiation:
            message = f"{cfg.junction_id} {message}"
        hints_file.write_text(message)

    junction.north.light.set(conn, north)
    junction.south.light.set(conn, south)
    junction.east.light.set(conn, east)
    junction.west.light.set(conn, west)


def init(conn: Connection, cfg: Config):
    pass


def loop(conn: Connection, cfg: Config, max_iterations: int = -1):
    if max_iterations == -1:
        max_iterations = float('inf')
    with suppress(KeyboardInterrupt):
        i = 0
        while i < max_iterations:
            update(conn, cfg)
            time.sleep(1)
            i += 1


def shutdown(conn: Connection, cfg: Config):
    pass


def main():
    if len(sys.argv) < 2:
        print('USAGE: python3 SCRIPT CONFIG_FILE [MAX_ITERATIONS] [-j JUNCTION_ID]')
        exit(-1)

    cfg = config.load(sys.argv[1])
    if '-j' in sys.argv:
        cfg.junction_id = int(sys.argv[sys.argv.index('-j') + 1])
    elif cfg.junction_id is None:
        print('No junction ID specified')
        exit(-1)
    pprint(cfg)

    if len(sys.argv) > 2 and sys.argv[2] != '-j':
        max_iterations = int(sys.argv[2])
    else:
        max_iterations = -1

    world_state = WorldState.from_config(cfg.world_state)
    conn = world_state.connect()

    neighbours.init(cfg)
    init(conn, cfg)
    time.sleep(1)
    loop(conn, cfg, max_iterations)
    shutdown(conn, cfg)


if __name__ == '__main__':
    exit(main())
