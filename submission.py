"""Standalone submission for Kaggriculture Competition."""
from __future__ import annotations
import math
import json
import re
from dataclasses import dataclass, field

# === MODULE: constants.py ===
"""Snapshot of Kaggriculture 0.1.0 rules shipped by kaggle-environments 1.32.7.

The submission deliberately does not import private engine modules at runtime.
Tests compare this snapshot with the installed engine to detect competition drift.
"""



ENGINE_PACKAGE_VERSION = "1.32.7"
ENGINE_ENV_VERSION = "0.1.0"

EPISODE_STEPS = 720
TURNS_PER_DAY = 24
BOARD_SIZE = 10
STARTING_MONEY = 3000
SHED_CAPACITY = 100
MAX_MARKET_ORDERS = 10
MARKET_I0 = 10_000
PRICE_FLOOR = 1
HINGE_GAIN = 8.0

CROPS = {
    "WHEAT": {
        "seed": 10,
        "first_yield_day": 2,
        "max_yield_day": 4,
        "interval": 0,
        "max_yield": 6,
        "ongoing": False,
    },
    "CARROT": {
        "seed": 20,
        "first_yield_day": 2,
        "max_yield_day": 3,
        "interval": 0,
        "max_yield": 4,
        "ongoing": False,
    },
    "TOMATO": {
        "seed": 50,
        "first_yield_day": 8,
        "max_yield_day": 8,
        "interval": 1,
        "max_yield": 4,
        "ongoing": True,
    },
    "STRAWBERRY": {
        "seed": 100,
        "first_yield_day": 10,
        "max_yield_day": 10,
        "interval": 2,
        "max_yield": 4,
        "ongoing": True,
    },
    "MELON": {
        "seed": 80,
        "first_yield_day": 10,
        "max_yield_day": 12,
        "interval": 0,
        "max_yield": 6,
        "ongoing": False,
    },
}

ANIMALS = {
    "GOOSE": {
        "cost": 300,
        "structure": "COOP",
        "first_yield_day": 4,
        "interval": 1,
        "max_held": 4,
        "product": "EGG",
    },
    "COW": {
        "cost": 400,
        "structure": "PASTURE",
        "first_yield_day": 8,
        "interval": 2,
        "max_held": 6,
        "product": "MILK",
    },
    "SHEEP": {
        "cost": 500,
        "structure": "PASTURE",
        "first_yield_day": 6,
        "interval": 3,
        "max_held": 6,
        "product": "WOOL",
    },
}

PRODUCTS = (
    "WHEAT",
    "CARROT",
    "TOMATO",
    "STRAWBERRY",
    "MELON",
    "EGG",
    "MILK",
    "WOOL",
    "FERTILIZER",
)

MARKET_PARAMS = {
    "WHEAT":      {"base": 25,  "I0": MARKET_I0, "T": 400, "below_func": "sqrt",  "below_target": 0.80, "above_func": "log",    "above_target": 0.20},
    "CARROT":     {"base": 35,  "I0": MARKET_I0, "T": 450, "below_func": "hinge", "below_target": 1.00, "above_func": "sqrt",   "above_target": 0.70},
    "TOMATO":     {"base": 60,  "I0": MARKET_I0, "T": 200, "below_func": "hinge", "below_target": 0.40, "above_func": "sqrt",   "above_target": 0.60},
    "STRAWBERRY": {"base": 120, "I0": MARKET_I0, "T": 100, "below_func": "sqrt",  "below_target": 0.70, "above_func": "linear", "above_target": 1.60},
    "MELON":      {"base": 250, "I0": MARKET_I0, "T": 300, "below_func": "log",   "below_target": 0.20, "above_func": "sq",     "above_target": 3.60},
    "EGG":        {"base": 50,  "I0": MARKET_I0, "T": 332, "below_func": "hinge", "below_target": 0.40, "above_func": "log",    "above_target": 0.20},
    "MILK":       {"base": 160, "I0": MARKET_I0, "T": 122, "below_func": "sqrt",  "below_target": 0.60, "above_func": "linear", "above_target": 1.60},
    "WOOL":       {"base": 200, "I0": MARKET_I0, "T": 105, "below_func": "log",   "below_target": 0.20, "above_func": "sq",     "above_target": 3.20},
    "FERTILIZER": {"base": 100, "I0": MARKET_I0, "T": 200, "below_func": "linear","below_target": 0.40, "above_func": "linear", "above_target": 0.40},
}

SHOPS = {
    "BAKERY": ("EGG", "WHEAT"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}

LAND_ORDER = ("NE", "SW", "SE")
LAND_PRICES = (1000, 2000, 4000)

FARMER_MOVES = {
    "NORTH": (0, -1),
    "SOUTH": (0, 1),
    "EAST": (1, 0),
    "WEST": (-1, 0),
}

UNIT_OPS = frozenset(
    {
        *FARMER_MOVES,
        "PASS",
        "PICKUP",
        "PLACE",
        "DROP",
        "PLANT",
        "WATER",
        "HARVEST",
        "FERTILIZE",
        "BUILD_COOP",
        "BUILD_PASTURE",
        "FEED",
        "COLLECT_FERTILIZER",
        "CARE",
        "DIG",
    }
)

MARKET_OPS = frozenset(
    {"BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL", "SELL", "HIRE", "BUY_LAND"}
)

SELL_RESERVE_FACTORS = {
    "WHEAT": 0.55,
    "CARROT": 0.58,
    "TOMATO": 0.60,
    "STRAWBERRY": 0.72,
    "MELON": 0.72,
    "EGG": 0.55,
    "MILK": 0.68,
    "WOOL": 0.68,
    "FERTILIZER": 0.45,
}



# === MODULE: access.py ===
"""Small defensive access helpers for Kaggle Struct and plain dictionaries."""



from typing import Any


def getv(obj: Any, key: str, default: Any = None) -> Any:
    """Read ``key`` from a dict-like object without assuming its concrete type."""

    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    getter = getattr(obj, "get", None)
    if callable(getter):
        try:
            return getter(key, default)
        except (AttributeError, KeyError, TypeError):
            pass
    return getattr(obj, key, default)


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError, OverflowError):
        return default


def count_of(mapping: Any, key: str) -> int:
    return max(0, as_int(getv(mapping, key, 0), 0))



# === MODULE: models.py ===
"""Lightweight records shared by the planner."""



from dataclasses import dataclass, field
from typing import Any

Position = tuple[int, int]


@dataclass(frozen=True, slots=True)
class UnitState:
    index: int
    position: Position
    inventory: dict[str, int]
    is_hand: bool = False

    def has(self, item: str, quantity: int = 1) -> bool:
        return self.inventory.get(item, 0) >= quantity


@dataclass(frozen=True, slots=True)
class LocatedTile:
    position: Position
    tile: Any


@dataclass(frozen=True, slots=True)
class Task:
    kind: str
    target: Position
    priority: int
    deadline: int
    value: float = 0.0
    item: str = ""
    quantity: int = 1
    stable_id: str = ""


@dataclass(slots=True)
class EconomicPlan:
    animal_targets: dict[str, int] = field(default_factory=dict)
    crop_targets: dict[str, int] = field(default_factory=dict)
    animal_buys: dict[str, int] = field(default_factory=dict)
    seed_buys: dict[str, int] = field(default_factory=dict)
    wheat_buy: int = 0
    desired_hands: int = 0
    buy_land: bool = False
    reserve_cash: int = 0



# === MODULE: routing.py ===
"""Deterministic routing for a board without blocking collisions."""





def step_toward(source: Position, target: Position) -> list[str]:
    sx, sy = source
    tx, ty = target
    dx = tx - sx
    dy = ty - sy
    if dx == 0 and dy == 0:
        return ["PASS"]
    # Prefer the longer axis. Fixed tie-breaking prevents oscillation.
    if abs(dx) >= abs(dy) and dx != 0:
        return ["EAST" if dx > 0 else "WEST"]
    if dy != 0:
        return ["SOUTH" if dy > 0 else "NORTH"]
    return ["EAST" if dx > 0 else "WEST"]



# === MODULE: world.py ===
"""Observation parsing and compact read-only world model."""



from dataclasses import dataclass
from typing import Any



def _mapping_counts(value: Any, keys: tuple[str, ...] | list[str]) -> dict[str, int]:
    return {key: count_of(value, key) for key in keys}


@dataclass(slots=True)
class WorldState:
    raw_obs: Any
    player: int
    opponent: int
    day: int
    hour: int
    step: int
    remaining_steps: int
    board_size: int
    money: float
    opponent_money: float
    farm: Any
    opponent_farm: Any
    private: Any
    market: Any
    town: Any
    tiles: Any
    units: list[UnitState]
    plants: list[LocatedTile]
    animals: list[LocatedTile]
    weeds: list[LocatedTile]
    empty_tiles: list[Position]
    empty_structures: list[LocatedTile]
    locked_tiles: list[Position]
    shed: dict[str, int]
    seeds: dict[str, int]
    unlocked_quadrants: tuple[str, ...]
    hires_today: int
    market_inventory: dict[str, int]
    market_prices: dict[str, int]
    shops: tuple[str, ...]
    opponent_plants: dict[str, int]
    opponent_animals: dict[str, int]

    @classmethod
    def from_observation(cls, obs: Any) -> "WorldState":
        farms = getv(obs, "farms", []) or []
        player = as_int(getv(obs, "player", 0), 0)
        if not farms or player < 0 or player >= len(farms):
            raise ValueError("observation does not contain the current player's farm")
        opponent = 1 - player if len(farms) >= 2 else player
        farm = farms[player]
        opponent_farm = farms[opponent]
        tiles = getv(farm, "tiles", []) or []
        board_size = len(tiles)
        if board_size <= 0:
            raise ValueError("farm has no tile grid")

        day = as_int(getv(obs, "day", 0), 0)
        hour = as_int(getv(obs, "hour", 0), 0)
        step = as_int(getv(obs, "step", day * TURNS_PER_DAY + hour), day * TURNS_PER_DAY + hour)
        private = getv(obs, "private", {}) or {}
        market = getv(obs, "market", {}) or {}
        town = getv(obs, "town", {}) or {}

        hands = getv(farm, "hands", []) or []
        positions = [getv(farm, "farmer", [0, 0]), *hands]
        inventories = getv(private, "inventories", []) or []
        units: list[UnitState] = []
        for index, pos in enumerate(positions):
            if not isinstance(pos, (list, tuple)) or len(pos) < 2:
                pos = [0, 0]
            inv = inventories[index] if index < len(inventories) else {}
            inv_counts = {
                key: count_of(inv, key)
                for key in (*PRODUCTS, *ANIMALS)
                if count_of(inv, key) > 0
            }
            units.append(
                UnitState(
                    index=index,
                    position=(as_int(pos[0]), as_int(pos[1])),
                    inventory=inv_counts,
                    is_hand=index > 0,
                )
            )

        plants: list[LocatedTile] = []
        animals: list[LocatedTile] = []
        weeds: list[LocatedTile] = []
        empty_tiles: list[Position] = []
        empty_structures: list[LocatedTile] = []
        locked_tiles: list[Position] = []

        for y, row in enumerate(tiles):
            for x, tile in enumerate(row):
                pos = (x, y)
                if tile is None:
                    empty_tiles.append(pos)
                elif tile == "LOCKED":
                    locked_tiles.append(pos)
                elif getv(tile, "kind", "") == "PLANT":
                    plants.append(LocatedTile(pos, tile))
                elif getv(tile, "kind", "") == "WEED":
                    weeds.append(LocatedTile(pos, tile))
                elif getv(tile, "animal", None) in ANIMALS:
                    animals.append(LocatedTile(pos, tile))
                elif getv(tile, "kind", "") in ("COOP", "PASTURE"):
                    empty_structures.append(LocatedTile(pos, tile))

        opponent_plants = {crop: 0 for crop in CROPS}
        opponent_animals = {animal: 0 for animal in ANIMALS}
        opponent_tiles = getv(opponent_farm, "tiles", []) or []
        for row in opponent_tiles:
            for tile in row:
                crop = getv(tile, "crop", "")
                animal = getv(tile, "animal", "")
                if crop in opponent_plants:
                    opponent_plants[crop] += 1
                if animal in opponent_animals:
                    opponent_animals[animal] += 1

        shed_source = getv(private, "shed", {}) or {}
        seed_source = getv(private, "seeds", {}) or {}
        shed = _mapping_counts(shed_source, [*PRODUCTS, *ANIMALS])
        seeds = _mapping_counts(seed_source, list(CROPS))
        market_inventory = _mapping_counts(getv(market, "inventory", {}) or {}, list(PRODUCTS))
        market_prices = _mapping_counts(getv(market, "prices", {}) or {}, list(PRODUCTS))

        return cls(
            raw_obs=obs,
            player=player,
            opponent=opponent,
            day=day,
            hour=hour,
            step=step,
            remaining_steps=max(0, EPISODE_STEPS - step - 1),
            board_size=board_size,
            money=as_float(getv(farm, "money", 0.0)),
            opponent_money=as_float(getv(opponent_farm, "money", 0.0)),
            farm=farm,
            opponent_farm=opponent_farm,
            private=private,
            market=market,
            town=town,
            tiles=tiles,
            units=units,
            plants=plants,
            animals=animals,
            weeds=weeds,
            empty_tiles=empty_tiles,
            empty_structures=empty_structures,
            locked_tiles=locked_tiles,
            shed=shed,
            seeds=seeds,
            unlocked_quadrants=tuple(getv(farm, "unlocked_quadrants", ["NW"]) or ["NW"]),
            hires_today=as_int(getv(farm, "hires_today", len(hands)), len(hands)),
            market_inventory=market_inventory,
            market_prices=market_prices,
            shops=tuple(getv(town, "unlocked_shops", []) or []),
            opponent_plants=opponent_plants,
            opponent_animals=opponent_animals,
        )

    @property
    def shed_load(self) -> int:
        return sum(self.shed.values())

    @property
    def remaining_days(self) -> float:
        return self.remaining_steps / float(TURNS_PER_DAY)

    def is_shed_access(self, position: Position) -> bool:
        half = self.board_size // 2
        return position in {
            (half - 1, half - 1),
            (half, half - 1),
            (half - 1, half),
            (half, half),
        }

    def nearest_shed_access(self, position: Position) -> Position:
        half = self.board_size // 2
        candidates = (
            (half - 1, half - 1),
            (half, half - 1),
            (half - 1, half),
            (half, half),
        )
        return min(candidates, key=lambda p: (manhattan(position, p), p[1], p[0]))

    def tile_at(self, position: Position) -> Any:
        x, y = position
        if 0 <= y < self.board_size and 0 <= x < self.board_size:
            return self.tiles[y][x]
        return "LOCKED"

    def inventory_total(self, item: str) -> int:
        return self.shed.get(item, 0) + sum(unit.inventory.get(item, 0) for unit in self.units)

    def animal_count(self, animal: str, include_pending: bool = True) -> int:
        placed = sum(1 for located in self.animals if getv(located.tile, "animal", "") == animal)
        if not include_pending:
            return placed
        return placed + self.inventory_total(animal)

    def crop_count(self, crop: str, include_seeds: bool = True) -> int:
        planted = sum(1 for located in self.plants if getv(located.tile, "crop", "") == crop)
        return planted + (self.seeds.get(crop, 0) if include_seeds else 0)


def manhattan(a: Position, b: Position) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])



# === MODULE: market.py ===
"""Pure market math and bounded marginal-sale decisions."""



import math



def _shape(func: str, x: float, throughput: float | None = None) -> float:
    x = max(0.0, x)
    if func == "linear":
        return x
    if func == "sq":
        return x * x
    if func == "sqrt":
        return math.sqrt(x)
    if func == "log":
        return math.log1p(x)
    if func == "log10":
        return math.log10(1.0 + x)
    if func == "hinge":
        if not throughput or throughput <= 0:
            return x
        u = x / throughput
        return u + HINGE_GAIN * max(0.0, u - 1.0) ** 2
    return x


def market_price(item: str, inventory: int) -> int:
    params = MARKET_PARAMS[item]
    base = float(params["base"])
    equilibrium = int(params["I0"])
    throughput = float(params["T"])
    if inventory < equilibrium:
        func = str(params["below_func"])
        amplitude = float(params["below_target"]) * base / _shape(func, throughput, throughput)
        price = base + amplitude * _shape(func, equilibrium - inventory, throughput)
    else:
        func = str(params["above_func"])
        amplitude = float(params["above_target"]) * base / _shape(func, throughput, throughput)
        price = base - amplitude * _shape(func, inventory - equilibrium, throughput)
    return max(PRICE_FLOOR, int(round(price)))


def demand_counts(shops: tuple[str, ...]) -> dict[str, int]:
    demand = {item: 0 for item in MARKET_PARAMS}
    for shop in shops:
        products = SHOPS.get(shop, ())
        multiplier = 2 if len(products) == 1 else 1
        for item in products:
            demand[item] += multiplier
    return demand


def daily_town_demand(world: WorldState, item: str) -> float:
    """Exact average units/day removed by the town for a market item.

    The town centre removes one unit per day.  Shops run six times per day;
    single-product shops remove two units on each run.
    """

    centre = 0.0 if item == "FERTILIZER" else 1.0
    return centre + 6.0 * demand_counts(world.shops).get(item, 0)


def profitable_inventory_ceiling(item: str, reserve_factor: float) -> int:
    """Largest market inventory whose quote remains above a reserve price.

    A bounded binary search keeps this exact for all engine price curves while
    avoiding a slow per-unit scan in the turn loop.
    """

    params = MARKET_PARAMS[item]
    equilibrium = int(params["I0"])
    threshold = max(PRICE_FLOOR + 1, int(round(float(params["base"]) * reserve_factor)))
    throughput = max(1, int(math.ceil(float(params["T"]))))

    low = equilibrium
    high = equilibrium + throughput
    hard_limit = equilibrium + 16 * throughput
    while high < hard_limit and market_price(item, high) >= threshold:
        low = high
        high = min(hard_limit, equilibrium + 2 * (high - equilibrium))
    if market_price(item, high) >= threshold:
        return high

    while low + 1 < high:
        middle = (low + high) // 2
        if market_price(item, middle) >= threshold:
            low = middle
        else:
            high = middle
    return low


def profitable_headroom(world: WorldState, item: str, reserve_factor: float) -> int:
    """Shared units the market can still absorb above ``reserve_factor``."""

    current = world.market_inventory.get(item, int(MARKET_PARAMS[item]["I0"]))
    return max(0, profitable_inventory_ceiling(item, reserve_factor) - current)


def visible_opponent_supply(world: WorldState, item: str) -> int:
    if item in world.opponent_plants:
        return world.opponent_plants[item]
    product_to_animal = {"EGG": "GOOSE", "MILK": "COW", "WOOL": "SHEEP"}
    animal = product_to_animal.get(item)
    return world.opponent_animals.get(animal, 0) if animal else 0


def marginal_sale_prices(item: str, inventory: int, quantity: int) -> list[int]:
    """Return the engine's pre-sale quote for each unit in a single-player estimate."""

    prices: list[int] = []
    current = inventory
    for _ in range(max(0, quantity)):
        price = market_price(item, current)
        prices.append(price)
        if price > PRICE_FLOOR:
            current += 1
    return prices


def choose_sale_quantity(world: WorldState, item: str, held: int) -> int:
    """Choose a bounded batch using marginal price, horizon, pressure and visible supply."""

    if held <= 0:
        return 0
    if world.day >= 28:
        return held

    keep = 0
    if item == "WHEAT":
        unfed = sum(1 for located in world.animals if not bool(getv(located.tile, "fed_today", False)))
        carried = sum(unit.inventory.get("WHEAT", 0) for unit in world.units)
        required_today = max(0, unfed - carried)
        pending_animals = sum(world.animal_count(animal) for animal in ANIMALS)
        unlocked = len(world.unlocked_quadrants)
        saving_for_land = (unlocked == 1 and world.day >= 2) or (unlocked == 2 and world.day >= 5)
        feed_buffer = pending_animals if saving_for_land else 2 * pending_animals + 2
        keep = min(held, max(feed_buffer, required_today + pending_animals))
    if item == "FERTILIZER" and world.day < 24:
        unlocked = len(world.unlocked_quadrants)
        saving_for_land = (unlocked == 1 and world.day >= 2) or (unlocked == 2 and world.day >= 5)
        if not saving_for_land:
            keep = max(keep, min(4, held))
    sellable = max(0, held - keep)
    if sellable <= 0:
        return 0

    params = MARKET_PARAMS[item]
    base = int(params["base"])
    reserve_factor = SELL_RESERVE_FACTORS[item]
    if world.day >= 24:
        reserve_factor *= 0.50
    elif world.day >= 15:
        reserve_factor *= 0.72

    pressure = max(0.0, (world.shed_load - 65) / max(1.0, SHED_CAPACITY - 65))
    if pressure > 0:
        reserve_factor *= max(0.35, 1.0 - 0.55 * pressure)
    if world.money < max(200.0, len(world.animals) * 22.0):
        reserve_factor *= 0.75
    if visible_opponent_supply(world, item) >= 8:
        reserve_factor *= 0.86

    # Market processing precedes town consumption.  Selling at step%4==0 gets
    # a worse quote because shops haven't drained yet.  Prefer step%4==1 which
    # executes right after shops consume, yielding better prices.
    shop_demand = demand_counts(world.shops).get(item, 0)
    imminent_centre_drain = item != "FERTILIZER" and world.step % 24 == 0
    if (
        (shop_demand > 0 or imminent_centre_drain)
        and world.step % 4 == 0
        and pressure < 0.35
        and world.money >= max(250.0, len(world.animals) * 25.0)
        and world.day < 28
    ):
        return 0
    # Actively prefer selling right after shop drain for best quote.
    if (
        world.step % 4 == 1
        and (shop_demand > 0 or imminent_centre_drain)
        and world.day < 28
        and pressure < 0.6
    ):
        # Boost: sell a bit more aggressively on optimal timing steps.
        reserve_factor *= 0.92

    reserve_price = max(2, int(round(base * reserve_factor)))
    if world.day < 15:
        batch_cap = 20
    elif world.day < 24:
        batch_cap = 32
    else:
        batch_cap = sellable
    batch_cap = min(sellable, batch_cap)

    inventory = world.market_inventory.get(item, int(params["I0"]))
    quantity = 0
    for price in marginal_sale_prices(item, inventory, batch_cap):
        if price < reserve_price and pressure < 0.5:
            break
        quantity += 1
    return quantity


# === MODULE: economy.py ===
"""Bounded strategic portfolio planner.

The planner intentionally exposes all high-impact choices as deterministic
functions so profiles can later be tuned by the champion/challenger harness.
"""



import math



# Effective output with daily FEED+CARE.  CARE bonuses accumulate between
# production days, hence Cow and Sheep output is much higher than the raw
# interval alone suggests.
ANIMAL_DAILY_OUTPUT = {"GOOSE": 2.0, "COW": 1.5, "SHEEP": 4.0 / 3.0}

# Official MARKET_PARAMS.T is defined as the output of a 5x5 field over a
# 24-day productive window.  Dividing by 600 gives a robust scheduling rate
# which already accounts for setup and imperfect utilisation.
CROP_DAILY_OUTPUT = {
    crop: float(MARKET_PARAMS[crop]["T"]) / (25.0 * 24.0)
    for crop in CROPS
}


def _shared_daily_capacity(world: WorldState, item: str) -> float:
    """Town drain plus a bounded correction toward market equilibrium.

    Market headroom is a stock, not a recurring daily demand.  The bounded
    drift prevents long, slow price curves (notably Egg) from consuming the
    entire portfolio merely because their theoretical ceiling is distant.
    """

    params = MARKET_PARAMS[item]
    current = world.market_inventory.get(item, int(params["I0"]))
    horizon = max(5.0, min(12.0, world.remaining_days))
    throughput_per_day = float(params["T"]) / 24.0
    drift = (float(params["I0"]) - current) / horizon
    drift = max(-throughput_per_day, min(throughput_per_day, drift))
    return max(0.0, daily_town_demand(world, item) + drift)


def _competitive_share(world: WorldState, shared_target: int, opponent: int) -> int:
    """Stable response around a fair share of shared market capacity."""

    if shared_target <= 0:
        return 0
    half = shared_target / 2.0
    response = half + 0.35 * (half - opponent)
    lower = int(math.ceil(0.30 * shared_target))
    upper = int(math.ceil(0.75 * shared_target))
    return max(lower, min(upper, int(math.ceil(response))))


def _animal_scores(world: WorldState) -> dict[str, float]:
    demand = demand_counts(world.shops)
    scores = {
        "GOOSE": 0.42 + 0.95 * demand["EGG"],
        "COW": 1.12 + 0.78 * demand["MILK"],
        "SHEEP": 1.18 + 1.05 * demand["WOOL"],
    }
    for animal, data in ANIMALS.items():
        product = str(data["product"])
        price = world.market_prices.get(product, int(MARKET_PARAMS[product]["base"]))
        base = int(MARKET_PARAMS[product]["base"])
        scarcity = max(0.6, min(1.8, price / max(1.0, base)))
        opponent_penalty = 1.0 / (1.0 + 0.06 * world.opponent_animals.get(animal, 0))
        scores[animal] *= scarcity * opponent_penalty
    return scores


def desired_animal_targets(world: WorldState) -> dict[str, int]:
    current = {animal: world.animal_count(animal) for animal in ANIMALS}
    if world.day == 0:
        goose_target = 0
        if demand_counts(world.shops).get("EGG", 0) > 0:
            goose_target = min(2, int(math.ceil(
                _shared_daily_capacity(world, "EGG") / ANIMAL_DAILY_OUTPUT["GOOSE"]
            )))
        return {"GOOSE": goose_target, "COW": 3, "SHEEP": 2}
    if world.day <= 2 or world.day > 18:
        return current

    targets: dict[str, int] = {}
    shop_demand = demand_counts(world.shops)
    for animal, data in ANIMALS.items():
        product = str(data["product"])
        if animal == "GOOSE" and shop_demand.get("EGG", 0) <= 0:
            targets[animal] = current[animal]
            continue
        shared_target = int(
            math.ceil(_shared_daily_capacity(world, product) / ANIMAL_DAILY_OUTPUT[animal])
        )
        opponent = world.opponent_animals.get(animal, 0)
        targets[animal] = _competitive_share(world, shared_target, opponent)

    # Preserve the proven balanced opening and every live/pending investment.
    targets["COW"] = max(3, targets["COW"])
    targets["SHEEP"] = max(2, targets["SHEEP"])
    for animal in ANIMALS:
        targets[animal] = max(targets[animal], current[animal])

    # Leave space for feed crops, movement and weeds.  When demand exceeds the
    # current land footprint, the land planner unlocks the next quadrant first.
    growth_cap = 5 if world.day <= 5 else min(24, 5 + 2 * (world.day - 5))
    physical_cap = max(5, len(world.unlocked_quadrants) * 25 - 12)
    owned_capacity = min(growth_cap, physical_cap)
    scores = _animal_scores(world)
    opening_floor = {"GOOSE": current["GOOSE"], "COW": max(3, current["COW"]), "SHEEP": max(2, current["SHEEP"])}
    while sum(targets.values()) > owned_capacity:
        removable = [name for name in ANIMALS if targets[name] > opening_floor[name]]
        if not removable:
            break
        animal = min(removable, key=lambda name: (scores[name], -targets[name], name))
        targets[animal] -= 1

    return targets


def desired_crop_targets(world: WorldState, animal_targets: dict[str, int]) -> dict[str, int]:
    demand = demand_counts(world.shops)
    animal_total = sum(animal_targets.values())
    targets = {crop: 0 for crop in CROPS}

    if world.day == 0:
        return {"WHEAT": 9, "CARROT": 0, "TOMATO": 0, "STRAWBERRY": 0, "MELON": 5}

    cutoffs = {"WHEAT": 25, "CARROT": 26, "TOMATO": 18, "STRAWBERRY": 16, "MELON": 17}
    for crop in CROPS:
        if world.day > cutoffs[crop]:
            continue
        # Early land is reserved for the opening animal+Wheat+Melon engine.
        if world.day < 5 and crop not in {"WHEAT", "MELON"} and demand.get(crop, 0) == 0:
            continue
        shared_target = int(
            math.ceil(_shared_daily_capacity(world, crop) / max(0.01, CROP_DAILY_OUTPUT[crop]))
        )
        opponent = world.opponent_plants.get(crop, 0)
        targets[crop] = _competitive_share(world, shared_target, opponent)

    # Wheat consumed as feed never reaches the public market.  Maintain an own
    # production floor separately from the fair-share market calculation.
    if world.day <= cutoffs["WHEAT"]:
        feed_floor = min(40, int(math.ceil(1.35 * animal_total)) + 2)
        targets["WHEAT"] = max(targets["WHEAT"], feed_floor)

    max_crop_slots = max(0, len(world.unlocked_quadrants) * 25 - animal_total - 5)
    max_crop_slots = min(66, max_crop_slots)
    minimums = {crop: 0 for crop in CROPS}
    feed_floor = min(40, int(math.ceil(1.35 * animal_total)) + 2)
    minimums["WHEAT"] = min(targets["WHEAT"], feed_floor, max_crop_slots)
    while sum(targets.values()) > max_crop_slots:
        removable = [crop for crop, value in targets.items() if value > minimums[crop]]
        if not removable:
            break
        crop = min(
            removable,
            key=lambda name: (
                CROP_DAILY_OUTPUT[name]
                * float(MARKET_PARAMS[name]["base"])
                * (1.0 + 0.35 * demand.get(name, 0))
                + 0.10
                * CROP_DAILY_OUTPUT[name]
                * max(0, world.market_prices.get(name, 0) - int(MARKET_PARAMS[name]["base"])),
                -CROPS[name]["first_yield_day"],
                name,
            ),
        )
        targets[crop] -= 1
    return targets


def desired_hands(world: WorldState, animal_targets: dict[str, int]) -> int:
    if world.hour >= 10:
        return world.hires_today
    schedule = {0: 5, 1: 4, 2: 5, 3: 5, 4: 5, 5: 5, 6: 8, 7: 8, 8: 9, 9: 10, 10: 11}
    return schedule.get(world.day, 12)


def _future_hire_cost(current: int, desired: int) -> int:
    a, b = 1, 1
    costs: list[int] = []
    for _ in range(max(0, desired)):
        costs.append(a)
        a, b = b, a + b
    return sum(costs[max(0, current) : max(0, desired)])


def _should_buy_land(world: WorldState, reserve_cash: int) -> bool:
    unlocked = len(world.unlocked_quadrants)
    if unlocked >= 3 or world.day >= 21:
        return False
    next_cost = LAND_PRICES[unlocked - 1]
    occupied = len(world.plants) + len(world.animals) + len(world.empty_structures) + len(world.weeds)
    if unlocked == 1:
        return world.day >= 4 and world.money >= next_cost + reserve_cash
    return world.day >= 7 and world.money >= next_cost + reserve_cash


def make_economic_plan(world: WorldState) -> EconomicPlan:
    animal_targets = desired_animal_targets(world)
    crop_targets = desired_crop_targets(world, animal_targets)
    current_animals = {animal: world.animal_count(animal) for animal in ANIMALS}
    feed_price = max(1, world.market_prices.get("WHEAT", 25))
    reserve_cash = max(250, int(sum(current_animals.values()) * feed_price * 1.25))
    buy_land = _should_buy_land(world, reserve_cash)
    unlocked = len(world.unlocked_quadrants)
    land_due = (unlocked == 1 and world.day >= 4) or (unlocked == 2 and world.day >= 7)
    land_saving = (unlocked == 1 and world.day >= 2) or (unlocked == 2 and world.day >= 5)

    hand_target = desired_hands(world, animal_targets)
    hire_reserve = _future_hire_cost(world.hires_today, hand_target)

    budget = int(world.money) - reserve_cash - hire_reserve
    if buy_land:
        budget -= LAND_PRICES[len(world.unlocked_quadrants) - 1]
    budget = max(0, budget)
    if land_due and not buy_land:
        budget = 0
    elif land_saving and not buy_land:
        next_land_cost = LAND_PRICES[unlocked - 1]
        budget = min(
            budget,
            max(0, int(world.money) - reserve_cash - hire_reserve - next_land_cost),
        )

    animal_buys = {animal: 0 for animal in ANIMALS}
    if world.day <= 18:
        scores = _animal_scores(world)
        gaps = {
            animal: max(0, animal_targets[animal] - current_animals[animal])
            for animal in ANIMALS
        }
        while budget > 0 and any(gaps.values()):
            candidates = [animal for animal, gap in gaps.items() if gap > 0]
            candidates.sort(
                key=lambda animal: (
                    scores[animal] / ANIMALS[animal]["cost"],
                    scores[animal],
                    -ANIMALS[animal]["cost"],
                    animal,
                ),
                reverse=True,
            )
            bought = False
            for animal in candidates:
                cost = int(ANIMALS[animal]["cost"])
                if budget >= cost:
                    animal_buys[animal] += 1
                    gaps[animal] -= 1
                    budget -= cost
                    bought = True
                    break
            if not bought:
                break

    seed_buys = {crop: 0 for crop in CROPS}
    if world.day <= 26:
        demand = demand_counts(world.shops)
        crop_order = sorted(
            CROPS,
            key=lambda crop: (
                demand.get(crop, 0),
                world.market_prices.get(crop, MARKET_PARAMS[crop]["base"]) / MARKET_PARAMS[crop]["base"],
                -CROPS[crop]["first_yield_day"],
                crop,
            ),
            reverse=True,
        )
        for crop in crop_order:
            gap = max(0, crop_targets[crop] - world.crop_count(crop))
            cost = int(CROPS[crop]["seed"])
            quantity = min(gap, 10, budget // cost)
            if quantity > 0:
                seed_buys[crop] = quantity
                budget -= quantity * cost

    # Essential feed may spend the strategic reserve, but only for animals
    # already owned/pending in the observation (not speculative same-turn buys).
    total_wheat = world.inventory_total("WHEAT")
    owned_animals = sum(current_animals.values())
    wheat_target = owned_animals * 2 + 2 if world.day <= 28 else 0
    if land_saving and not buy_land:
        wheat_target = owned_animals
    wheat_gap = min(36, max(0, wheat_target - total_wheat))
    committed = (
        sum(animal_buys[a] * int(ANIMALS[a]["cost"]) for a in ANIMALS)
        + sum(seed_buys[c] * int(CROPS[c]["seed"]) for c in CROPS)
        + hire_reserve
        + (LAND_PRICES[len(world.unlocked_quadrants) - 1] if buy_land else 0)
    )
    feed_budget = max(0, int(world.money) - committed - 25)
    wheat_buy = min(wheat_gap, feed_budget // feed_price)
    remaining_reserve = max(25, reserve_cash - wheat_buy * feed_price)

    return EconomicPlan(
        animal_targets=animal_targets,
        crop_targets=crop_targets,
        animal_buys=animal_buys,
        seed_buys=seed_buys,
        wheat_buy=wheat_buy,
        desired_hands=hand_target,
        buy_land=buy_land,
        reserve_cash=remaining_reserve,
    )


# === MODULE: tasks.py ===
"""Turn-level task generation with explicit survival and endgame priorities."""





def _stable(kind: str, position: Position, suffix: str = "") -> str:
    return f"{kind}:{position[0]}:{position[1]}:{suffix}"


def _build_positions(world: WorldState, quantity: int, excluded: set[Position]) -> list[Position]:
    center = (world.board_size // 2 - 1, world.board_size // 2 - 1)
    candidates = [position for position in world.empty_tiles if position not in excluded]
    candidates.sort(key=lambda p: (manhattan(p, center), p[1], p[0]))
    return candidates[: max(0, quantity)]


def _fertilizer_has_future_value(world: WorldState, tile: object, crop: str) -> bool:
    data = CROPS[crop]
    planted = as_int(getv(tile, "planted_day", world.day), world.day)
    age = world.day - planted
    if not bool(data["ongoing"]):
        window_start = (int(data["max_yield_day"]) + 1) // 2
        return any(window_start <= age + offset <= int(data["max_yield_day"]) for offset in range(3))
    for offset in range(3):
        next_day = world.day + offset + 1
        since_first = next_day - planted - int(data["first_yield_day"])
        if since_first < 0 or since_first % int(data["interval"]) != 0:
            continue
        production_count = since_first // int(data["interval"]) + 1
        if production_count <= int(data["max_yield"]):
            return True
    return False


def generate_tasks(world: WorldState, plan: EconomicPlan) -> list[Task]:
    tasks: list[Task] = []
    reserved_tiles: set[Position] = set()
    endgame = world.day >= 29
    turns_left_today = max(0, 22 - world.hour + 1) if endgame else 24 - world.hour

    # 1) Logistics for already-carried animals has the shortest path to activation.
    empty_by_structure: dict[str, list[Position]] = {"COOP": [], "PASTURE": []}
    for located in world.empty_structures:
        kind = str(getv(located.tile, "kind", ""))
        if kind in empty_by_structure:
            empty_by_structure[kind].append(located.position)
    for positions in empty_by_structure.values():
        positions.sort(key=lambda p: (manhattan(p, world.nearest_shed_access(p)), p[1], p[0]))

    carried_by_animal = {
        animal: sum(unit.inventory.get(animal, 0) for unit in world.units)
        for animal in ANIMALS
    }
    for structure in ("PASTURE", "COOP"):
        positions = list(empty_by_structure[structure])
        animals = [
            animal
            for animal in ANIMALS
            if ANIMALS[animal]["structure"] == structure
        ]
        animal_queue: list[str] = []
        for animal in sorted(animals, key=lambda name: (-carried_by_animal[name], name)):
            animal_queue.extend([animal] * carried_by_animal[animal])
        for position, animal in zip(positions, animal_queue):
            tasks.append(
                Task(
                    "PLACE_ANIMAL",
                    position,
                    priority=2,
                    deadline=world.step + turns_left_today,
                    value=500.0,
                    item=animal,
                    stable_id=_stable("PLACE", position, animal),
                )
            )

    # 2) Build exactly enough structures for shed/carried/planned animals.
    occupied_structures = {"COOP": 0, "PASTURE": 0}
    for located in world.animals:
        kind = str(getv(located.tile, "kind", ""))
        if kind in occupied_structures:
            occupied_structures[kind] += 1
    planned_pending = {
        animal: world.inventory_total(animal) + plan.animal_buys.get(animal, 0)
        for animal in ANIMALS
    }
    for structure in ("PASTURE", "COOP"):
        pending = sum(
            planned_pending[animal]
            for animal in ANIMALS
            if ANIMALS[animal]["structure"] == structure
        )
        missing = max(0, pending - len(empty_by_structure[structure]))
        build_positions = _build_positions(world, missing, reserved_tiles)
        for position in build_positions:
            reserved_tiles.add(position)
            tasks.append(
                Task(
                    f"BUILD_{structure}",
                    position,
                    priority=7,
                    deadline=world.step + turns_left_today,
                    value=350.0,
                    stable_id=_stable(f"BUILD_{structure}", position),
                )
            )
            empty_by_structure[structure].append(position)

    # 3) Pick pending animals up from the shed. The target is symbolic: any of
    # the four shed-access tiles is accepted by the assignment layer.
    shed_target = world.nearest_shed_access(world.units[0].position)
    for animal in ANIMALS:
        matching = str(ANIMALS[animal]["structure"])
        available = min(world.shed.get(animal, 0), len(empty_by_structure[matching]))
        for index in range(available):
            tasks.append(
                Task(
                    "PICKUP_ANIMAL",
                    shed_target,
                    priority=5,
                    deadline=world.step + turns_left_today,
                    value=450.0,
                    item=animal,
                    quantity=1,
                    stable_id=_stable("PICKUP_ANIMAL", shed_target, f"{animal}:{index}"),
                )
            )

    # 4) Endgame conversion. There is no action at day 29/hour 23 in the
    # official engine, so all carried products must reach the shed by hour 22.
    if endgame:
        for unit in world.units:
            carried_products = sum(unit.inventory.get(item, 0) for item in PRODUCTS)
            if carried_products <= 0:
                continue
            distance = manhattan(unit.position, world.nearest_shed_access(unit.position))
            tasks.append(
                Task(
                    "DROP",
                    world.nearest_shed_access(unit.position),
                    priority=0,
                    deadline=world.step + max(0, turns_left_today - 1),
                    value=10_000.0 + distance,
                    stable_id=f"DROP:{unit.index}",
                )
            )

    # 5) Mandatory daily care. Last-day feed/water cannot create sellable value.
    if not endgame:
        unfed = []
        for located in world.animals:
            tile = located.tile
            if not bool(getv(tile, "fed_today", False)):
                unfed.append(located)
                urgency = 3 if world.hour >= 15 or as_int(getv(tile, "consecutive_unfed", 0)) >= 1 else 14
                tasks.append(
                    Task(
                        "FEED",
                        located.position,
                        priority=urgency,
                        deadline=(world.day + 1) * 24 - 1,
                        value=900.0,
                        item="WHEAT",
                        stable_id=_stable("FEED", located.position),
                    )
                )

        carried_wheat = sum(unit.inventory.get("WHEAT", 0) for unit in world.units)
        required_pickup = max(0, len(unfed) - carried_wheat)
        wheat_available = world.shed.get("WHEAT", 0)
        pickup_quantity = min(required_pickup, wheat_available)
        pickup_index = 0
        while pickup_quantity > 0 and pickup_index < len(world.units):
            quantity = min(6, pickup_quantity)
            tasks.append(
                Task(
                    "PICKUP_WHEAT",
                    shed_target,
                    priority=4 if world.hour >= 12 else 12,
                    deadline=(world.day + 1) * 24 - 1,
                    value=700.0,
                    item="WHEAT",
                    quantity=quantity,
                    stable_id=_stable("PICKUP_WHEAT", shed_target, str(pickup_index)),
                )
            )
            pickup_quantity -= quantity
            pickup_index += 1

        for located in world.plants:
            tile = located.tile
            if not bool(getv(tile, "watered_today", False)):
                urgency = 2 if world.hour >= 16 or as_int(getv(tile, "consecutive_unwatered", 0)) >= 1 else 16
                tasks.append(
                    Task(
                        "WATER",
                        located.position,
                        priority=urgency,
                        deadline=(world.day + 1) * 24 - 1,
                        value=850.0,
                        stable_id=_stable("WATER", located.position),
                    )
                )

    # 6) Harvest before production caps/decay. On the final day this outranks
    # optional farm maintenance but not returning already-carried goods.
    for located in world.plants:
        tile = located.tile
        crop = str(getv(tile, "crop", ""))
        yield_units = as_int(getv(tile, "yield_units", 0))
        age = world.day - as_int(getv(tile, "planted_day", world.day))
        if crop not in CROPS or yield_units <= 0 or age < CROPS[crop]["first_yield_day"]:
            continue
        if endgame:
            distance = manhattan(located.position, world.nearest_shed_access(located.position))
            if distance + 2 > max(0, 23 - world.hour):
                continue
        priority = 4 if endgame else (9 if yield_units >= CROPS[crop]["max_yield"] else 25)
        tasks.append(
            Task(
                "HARVEST",
                located.position,
                priority=priority,
                deadline=world.step + max(0, turns_left_today - 2),
                value=float(yield_units * 100),
                item=crop,
                stable_id=_stable("HARVEST_PLANT", located.position),
            )
        )

    for located in world.animals:
        tile = located.tile
        animal = str(getv(tile, "animal", ""))
        yield_units = as_int(getv(tile, "yield_units", 0))
        if animal not in ANIMALS or yield_units <= 0:
            continue
        if endgame:
            distance = manhattan(located.position, world.nearest_shed_access(located.position))
            if distance + 2 > max(0, 23 - world.hour):
                continue
        near_cap = yield_units >= int(ANIMALS[animal]["max_held"]) - 1
        priority = 3 if endgame else (8 if near_cap else 24)
        tasks.append(
            Task(
                "HARVEST",
                located.position,
                priority=priority,
                deadline=world.step + max(0, turns_left_today - 2),
                value=float(yield_units * 120),
                item=str(ANIMALS[animal]["product"]),
                stable_id=_stable("HARVEST_ANIMAL", located.position),
            )
        )

    # 7) Fertilizer is produced daily and is valuable either as product or input.
    if world.day <= 28:
        fertilizer_price = world.market_prices.get("FERTILIZER", 0)
        fertilizer_priority = 30 if fertilizer_price >= 60 else 55 if fertilizer_price >= 20 else 88
        for located in world.animals:
            if bool(getv(located.tile, "fertilizer_available", False)):
                tasks.append(
                    Task(
                        "COLLECT_FERTILIZER",
                        located.position,
                        priority=fertilizer_priority,
                        deadline=world.step + turns_left_today,
                        value=100.0,
                        item="FERTILIZER",
                        stable_id=_stable("COLLECT_FERTILIZER", located.position),
                    )
                )

    if world.day <= 27:
        for located in world.animals:
            tile = located.tile
            if bool(getv(tile, "fed_today", False)) and not bool(getv(tile, "cared_today", False)):
                tasks.append(
                    Task(
                        "CARE",
                        located.position,
                        priority=15,
                        deadline=(world.day + 1) * 24 - 1,
                        value=85.0,
                        stable_id=_stable("CARE", located.position),
                    )
                )

        carried_fertilizer = sum(unit.inventory.get("FERTILIZER", 0) for unit in world.units)
        fertilizable = []
        unlocked = len(world.unlocked_quadrants)
        saving_for_land = (unlocked == 1 and world.day >= 2) or (unlocked == 2 and world.day >= 5)
        for located in world.plants if not saving_for_land else ():
            tile = located.tile
            crop = str(getv(tile, "crop", ""))
            fertilized_until = as_int(getv(tile, "fertilized_until_day", -1), -1)
            age = world.day - as_int(getv(tile, "planted_day", world.day))
            if (
                crop in CROPS
                and fertilized_until < world.day
                and age <= CROPS[crop]["max_yield_day"]
                and _fertilizer_has_future_value(world, tile, crop)
            ):
                fertilizable.append(located)
                tasks.append(
                    Task(
                        "FERTILIZE",
                        located.position,
                        priority=43,
                        deadline=world.step + turns_left_today,
                        value=70.0,
                        item="FERTILIZER",
                        stable_id=_stable("FERTILIZE", located.position),
                    )
                )
        if carried_fertilizer == 0 and fertilizable and world.shed.get("FERTILIZER", 0) > 0:
            quantity = min(4, world.shed.get("FERTILIZER", 0), len(fertilizable))
            tasks.append(
                Task(
                    "PICKUP_FERTILIZER",
                    shed_target,
                    priority=36,
                    deadline=world.step + turns_left_today,
                    value=80.0,
                    item="FERTILIZER",
                    quantity=quantity,
                    stable_id=_stable("PICKUP_FERTILIZER", shed_target),
                )
            )

    # 8) Plant only where at least one unit can still arrive, plant and water
    # before the end-of-day refresh.  This is less wasteful than a fixed early
    # cutoff and lets the opening portfolio use its full 14 planned tiles.
    if world.day <= 26 and world.hour <= 22:
        action_slots = 24 - world.hour
        plantable = [
            position
            for position in world.empty_tiles
            if position not in reserved_tiles
            and min(manhattan(unit.position, position) for unit in world.units) + 2 <= action_slots
        ]
        center = (world.board_size // 2 - 1, world.board_size // 2 - 1)
        plantable.sort(key=lambda p: (manhattan(p, center), p[1], p[0]))
        cursor = 0
        for crop in sorted(CROPS, key=lambda name: (CROPS[name]["first_yield_day"], name)):
            quantity = min(world.seeds.get(crop, 0), max(0, plan.crop_targets.get(crop, 0) - world.crop_count(crop, False)))
            for index in range(quantity):
                if cursor >= len(plantable):
                    break
                position = plantable[cursor]
                cursor += 1
                reserved_tiles.add(position)
                tasks.append(
                    Task(
                        "PLANT",
                        position,
                        priority=18 if world.day == 0 else 32,
                        deadline=(world.day + 1) * 24 - 2,
                        value=50.0,
                        item=crop,
                        stable_id=_stable("PLANT", position, f"{crop}:{index}"),
                    )
                )

    # Weeds are low priority unless they block a nearly full field.
    weed_priority = 46 if len(world.empty_tiles) < 4 else 72
    for located in world.weeds:
        tasks.append(
            Task(
                "DIG",
                located.position,
                priority=weed_priority,
                deadline=world.step + 96,
                value=20.0,
                stable_id=_stable("DIG", located.position),
            )
        )

    # Mid-game drop enables market sales without waiting for end of day.
    if not endgame:
        for unit in world.units:
            carried_products = sum(unit.inventory.get(item, 0) for item in PRODUCTS)
            if carried_products >= 8 or (world.money < 150 and carried_products > 0):
                tasks.append(
                    Task(
                        "DROP",
                        world.nearest_shed_access(unit.position),
                        priority=34,
                        deadline=world.step + turns_left_today,
                        value=float(carried_products * 20),
                        stable_id=f"DROP:{unit.index}",
                    )
                )

    tasks.sort(key=lambda task: (task.priority, task.deadline, -task.value, task.stable_id))
    return tasks[:192]


# === MODULE: assignment.py ===
"""Bounded deterministic unit-task assignment and action materialization."""





def _has_products(unit: UnitState) -> bool:
    return any(unit.inventory.get(item, 0) > 0 for item in PRODUCTS)


def _feasible(unit: UnitState, task: Task, world: WorldState) -> bool:
    if task.kind == "FEED":
        return unit.has("WHEAT")
    if task.kind == "FERTILIZE":
        return unit.has("FERTILIZER")
    if task.kind == "PLACE_ANIMAL":
        return unit.has(task.item)
    if task.kind == "DROP":
        return _has_products(unit)
    if task.kind == "PICKUP_ANIMAL":
        return world.shed.get(task.item, 0) > 0
    if task.kind == "PICKUP_WHEAT":
        return world.shed.get("WHEAT", 0) > 0 and unit.inventory.get("WHEAT", 0) < task.quantity
    if task.kind == "PICKUP_FERTILIZER":
        return world.shed.get("FERTILIZER", 0) > 0 and unit.inventory.get("FERTILIZER", 0) == 0
    return True


def _effective_target(unit: UnitState, task: Task, world: WorldState) -> tuple[int, int]:
    if task.kind.startswith("PICKUP_") or task.kind == "DROP":
        return world.nearest_shed_access(unit.position)
    return task.target


def _action_for(unit: UnitState, task: Task, world: WorldState) -> list:
    target = _effective_target(unit, task, world)
    at_target = unit.position == target
    if task.kind.startswith("PICKUP_") or task.kind == "DROP":
        at_target = world.is_shed_access(unit.position)
    if not at_target:
        return step_toward(unit.position, target)

    if task.kind == "PLACE_ANIMAL":
        return ["PLACE", task.item]
    if task.kind == "PICKUP_ANIMAL":
        return ["PICKUP", task.item, task.quantity]
    if task.kind == "PICKUP_WHEAT":
        return ["PICKUP", "WHEAT", task.quantity]
    if task.kind == "PICKUP_FERTILIZER":
        return ["PICKUP", "FERTILIZER", task.quantity]
    if task.kind == "DROP":
        return ["DROP"]
    if task.kind == "PLANT":
        return ["PLANT", task.item]
    if task.kind in {
        "FEED",
        "WATER",
        "HARVEST",
        "FERTILIZE",
        "CARE",
        "COLLECT_FERTILIZER",
        "DIG",
        "BUILD_COOP",
        "BUILD_PASTURE",
    }:
        return [task.kind]
    return ["PASS"]


def _fallback_action(unit: UnitState, world: WorldState) -> list:
    if world.day >= 29:
        if _has_products(unit):
            if world.is_shed_access(unit.position):
                return ["DROP"]
            return step_toward(unit.position, world.nearest_shed_access(unit.position))
        return ["PASS"]

    tile = world.tile_at(unit.position)
    if getv(tile, "kind", "") == "PLANT":
        if not bool(getv(tile, "watered_today", False)) and world.day < 29:
            return ["WATER"]
        crop = str(getv(tile, "crop", ""))
        planted_day = int(getv(tile, "planted_day", world.day) or world.day)
        mature = crop in CROPS and world.day - planted_day >= CROPS[crop]["first_yield_day"]
        if int(getv(tile, "yield_units", 0) or 0) > 0 and mature:
            return ["HARVEST"]
    animal = str(getv(tile, "animal", ""))
    if animal in ANIMALS:
        if not bool(getv(tile, "fed_today", False)) and unit.has("WHEAT") and world.day < 29:
            return ["FEED"]
        if int(getv(tile, "yield_units", 0) or 0) > 0:
            return ["HARVEST"]
        if bool(getv(tile, "fertilizer_available", False)):
            return ["COLLECT_FERTILIZER"]
    return ["PASS"]


def assign_actions(world: WorldState, tasks: list[Task]) -> list[list]:
    candidates: list[tuple] = []
    for unit in world.units:
        for task_index, task in enumerate(tasks):
            if not _feasible(unit, task, world):
                continue
            target = _effective_target(unit, task, world)
            candidates.append(
                (
                    task.priority,
                    task.deadline,
                    manhattan(unit.position, target),
                    -task.value,
                    task.stable_id,
                    unit.index,
                    task_index,
                )
            )
    candidates.sort()

    assigned_units: set[int] = set()
    assigned_tasks: set[int] = set()
    selected: dict[int, Task] = {}
    for *_, unit_index, task_index in candidates:
        if unit_index in assigned_units or task_index in assigned_tasks:
            continue
        assigned_units.add(unit_index)
        assigned_tasks.add(task_index)
        selected[unit_index] = tasks[task_index]
        if len(assigned_units) >= len(world.units):
            break

    actions: list[list] = []
    for unit in world.units:
        task = selected.get(unit.index)
        actions.append(_action_for(unit, task, world) if task else _fallback_action(unit, world))
    return actions


# === MODULE: orders.py ===
"""Market-order construction with a hard ten-order budget."""





def _hire_orders(world: WorldState, plan: EconomicPlan, available_slots: int) -> list[list]:
    if available_slots <= 0 or world.hour >= 10:
        return []
    missing = max(0, plan.desired_hands - world.hires_today)
    return [["HIRE"] for _ in range(min(missing, available_slots))]


def build_market_orders(world: WorldState, plan: EconomicPlan) -> list[list]:
    if world.day >= 29:
        liquidation = []
        for item in PRODUCTS:
            quantity = world.inventory_total(item)
            if quantity > 0:
                liquidation.append(["SELL", item, quantity])
        liquidation.sort(
            key=lambda order: (
                -(order[2] * world.market_prices.get(order[1], MARKET_PARAMS[order[1]]["base"])),
                order[1],
            )
        )
        orders = liquidation[:MAX_MARKET_ORDERS]
        orders.extend(_hire_orders(world, plan, MAX_MARKET_ORDERS - len(orders)))
        return orders[:MAX_MARKET_ORDERS]

    sales: list[list] = []
    for item in PRODUCTS:
        # Never churn feed by selling and repurchasing Wheat in one market
        # queue.  The engine intentionally makes that round-trip zero-profit.
        if item == "WHEAT" and plan.wheat_buy > 0:
            continue
        held = world.shed.get(item, 0)
        quantity = choose_sale_quantity(world, item, held)
        if quantity > 0:
            sales.append(["SELL", item, quantity])
    sales.sort(
        key=lambda order: (
            -(order[2] * world.market_prices.get(order[1], MARKET_PARAMS[order[1]]["base"])),
            order[1],
        )
    )
    sales = sales[: (7 if world.day >= 27 else 4)]

    orders: list[list] = list(sales)
    if plan.wheat_buy > 0 and len(orders) < MAX_MARKET_ORDERS:
        orders.append(["BUY_PRODUCT", "WHEAT", plan.wheat_buy])
    if plan.buy_land and len(orders) < MAX_MARKET_ORDERS:
        orders.append(["BUY_LAND"])

    for animal in sorted(
        ANIMALS,
        key=lambda name: (-plan.animal_buys.get(name, 0) * ANIMALS[name]["cost"], name),
    ):
        quantity = plan.animal_buys.get(animal, 0)
        if quantity > 0 and len(orders) < MAX_MARKET_ORDERS:
            orders.append(["BUY_ANIMAL", animal, quantity])

    # Operations need labor before optional extra seed inventory. Missing hires
    # are spread over the first few turns when sales consume the order budget.
    orders.extend(_hire_orders(world, plan, MAX_MARKET_ORDERS - len(orders)))

    for crop in sorted(
        CROPS,
        key=lambda name: (
            -plan.seed_buys.get(name, 0) * CROPS[name]["seed"],
            CROPS[name]["first_yield_day"],
            name,
        ),
    ):
        quantity = plan.seed_buys.get(crop, 0)
        if quantity > 0 and len(orders) < MAX_MARKET_ORDERS:
            orders.append(["BUY_SEED", crop, quantity])

    return orders[:MAX_MARKET_ORDERS]


# === MODULE: validator.py ===
"""Final action-boundary validation and resource oversubscription guards."""





def _normalize_unit_action(action: object) -> list:
    if not isinstance(action, list) or not action or action[0] not in UNIT_OPS:
        return ["PASS"]
    op = action[0]
    if op == "PLANT":
        return ["PLANT", action[1]] if len(action) >= 2 and action[1] in CROPS else ["PASS"]
    if op in {"PICKUP", "PLACE"}:
        if len(action) < 2 or action[1] not in {*PRODUCTS, *ANIMALS}:
            return ["PASS"]
        if len(action) < 3:
            return [op, action[1]]
        try:
            quantity = int(action[2])
        except (TypeError, ValueError, OverflowError):
            return ["PASS"]
        return [op, action[1], quantity] if quantity > 0 else ["PASS"]
    return [op]


def _normalize_market_order(order: object) -> list | None:
    if not isinstance(order, list) or not order or order[0] not in MARKET_OPS:
        return None
    op = order[0]
    if op in {"HIRE", "BUY_LAND"}:
        return [op]
    if len(order) < 3:
        return None
    item = order[1]
    valid_item = (
        (op == "BUY_SEED" and item in CROPS)
        or (op == "BUY_PRODUCT" and item in {"WHEAT", "FERTILIZER"})
        or (op == "BUY_ANIMAL" and item in ANIMALS)
        or (op == "SELL" and item in PRODUCTS)
    )
    if not valid_item:
        return None
    try:
        quantity = int(order[2])
    except (TypeError, ValueError, OverflowError):
        return None
    if quantity <= 0:
        return None
    return [op, item, quantity]


def validate_action(world: WorldState, unit_actions: list[list], market_orders: list[list]) -> dict:
    expected_units = len(world.units)
    normalized = [_normalize_unit_action(action) for action in unit_actions[:expected_units]]
    while len(normalized) < expected_units:
        normalized.append(["PASS"])

    # Mirror the engine's atomic seed guard locally, but keep earlier reserved
    # actions instead of allowing every request for the crop to be cancelled.
    used_seeds = {crop: 0 for crop in CROPS}
    for index, action in enumerate(normalized):
        if action[0] != "PLANT" or len(action) < 2:
            continue
        crop = action[1]
        if crop not in CROPS or used_seeds[crop] >= world.seeds.get(crop, 0):
            normalized[index] = ["PASS"]
        else:
            used_seeds[crop] += 1

    market: list[list] = []
    for order in market_orders:
        normalized_order = _normalize_market_order(order)
        if normalized_order is not None:
            market.append(normalized_order)
        if len(market) >= MAX_MARKET_ORDERS:
            break

    return {
        "farmer": normalized[0] if normalized else ["PASS"],
        "hands": normalized[1:],
        "market": market,
    }


# === MODULE: entrypoint.py ===
"""Public competition entry point."""





def _safe_fallback(obs) -> dict:
    try:
        player = int(getv(obs, "player", 0))
        farms = getv(obs, "farms", []) or []
        farm = farms[player]
        hands = getv(farm, "hands", []) or []
        farmer = ["PASS"]
        position = getv(farm, "farmer", [0, 0])
        tiles = getv(farm, "tiles", []) or []
        if tiles and len(position) >= 2:
            x, y = int(position[0]), int(position[1])
            tile = tiles[y][x]
            if getv(tile, "kind", "") == "PLANT" and not bool(getv(tile, "watered_today", False)):
                farmer = ["WATER"]
            elif int(getv(tile, "yield_units", 0) or 0) > 0:
                farmer = ["HARVEST"]
        return {
            "farmer": farmer,
            "hands": [["PASS"] for _ in hands],
            "market": [],
        }
    except Exception:
        return {"farmer": ["PASS"], "hands": [], "market": []}


def decide(obs) -> dict:
    world = WorldState.from_observation(obs)
    plan = make_economic_plan(world)
    tasks = generate_tasks(world, plan)
    unit_actions = assign_actions(world, tasks)
    market_orders = build_market_orders(world, plan)
    return validate_action(world, unit_actions, market_orders)


def agent(obs) -> dict:
    try:
        return decide(obs)
    except Exception:
        return _safe_fallback(obs)



# === KAGGLE ENTRY POINT ===
def agent(obs) -> dict:
    try:
        return decide(obs)
    except Exception:
        return _safe_fallback(obs)
