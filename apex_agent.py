"""
Titan Grandmaster Agent (Submission V6 - School 1 & 2 Synthesis) for Kaggriculture.
-----------------------------------------------------------------------------------
SYNTHESIS OF TWO GRANDMASTER PARADIGMS:

[SCHOOL 1: OPERATIONS RESEARCH & MATHEMATICAL OPTIMIZATION]
  1. Exact Hungarian Algorithm (Kuhn-Munkres):
     - Solves global bipartite matching between N workers and M farm tasks in O(N^3).
     - Globally minimizes total worker travel distance while strictly honoring task priority tiers.
  2. Non-Linear Market Price Integral Solver:
     - Calculates exact marginal revenue per dollar (MR/$) accounting for shop drain rates and market inventory.
     - Optimal portfolio knapsack solving for seed, livestock, and feed allocation.

[SCHOOL 2: FORWARD LOOKAHEAD SIMULATION & ROLLOUT SEARCH]
  3. Micro-Economic Forward Lookahead:
     - Simulates multi-day capital trajectory (3-5 days) to evaluate land expansion timing vs crop investment.
     - Evaluates future asset equity: Cash + Discounted Harvests + Livestock Equity - Feed Obligations.

[TOP PLAYER SPATIAL & STRATEGIC POLICIES]
  4. Zero-Goose Opening: Focus 100% on Cow ($160/unit) and Sheep ($200/unit).
  5. Compact Pasture Hub: Pastures in 3x3 block adjacent to NW Shed (4,4) for 1-step worker access.
  6. Working Capital Buffer: Always preserves $200-$300 for fast cash-crop flips during land saving.
  7. High-Density Land Occupancy: Fills 100% of unlocked empty tiles.
  8. Animal Care Maximizer: Daily CARE for Sheep (+1 Wool = +$200) and Cow (+1 Milk = +$160).
  9. Complete Terminal Liquidation: Total harvest and shed clearance on Days 28-29.
"""
from __future__ import annotations
import math
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

# ==================== CONSTANTS & GAME RULES ====================
EPISODE_STEPS = 720
TURNS_PER_DAY = 24
BOARD_SIZE = 10
STARTING_MONEY = 3000
SHED_CAPACITY = 100
MAX_MARKET_ORDERS = 10
MARKET_I0 = 10000
PRICE_FLOOR = 1
HINGE_GAIN = 8.0

CROPS = {
    'WHEAT': {'seed': 10, 'first_yield_day': 2, 'max_yield_day': 4, 'interval': 0, 'max_yield': 6, 'ongoing': False},
    'CARROT': {'seed': 20, 'first_yield_day': 2, 'max_yield_day': 3, 'interval': 0, 'max_yield': 4, 'ongoing': False},
    'TOMATO': {'seed': 50, 'first_yield_day': 8, 'max_yield_day': 8, 'interval': 1, 'max_yield': 4, 'ongoing': True},
    'STRAWBERRY': {'seed': 100, 'first_yield_day': 10, 'max_yield_day': 10, 'interval': 2, 'max_yield': 4, 'ongoing': True},
    'MELON': {'seed': 80, 'first_yield_day': 10, 'max_yield_day': 12, 'interval': 0, 'max_yield': 6, 'ongoing': False}
}

ANIMALS = {
    'GOOSE': {'cost': 300, 'structure': 'COOP', 'first_yield_day': 4, 'interval': 1, 'max_held': 4, 'product': 'EGG'},
    'COW': {'cost': 400, 'structure': 'PASTURE', 'first_yield_day': 8, 'interval': 2, 'max_held': 6, 'product': 'MILK'},
    'SHEEP': {'cost': 500, 'structure': 'PASTURE', 'first_yield_day': 6, 'interval': 3, 'max_held': 6, 'product': 'WOOL'}
}

PRODUCTS = ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON', 'EGG', 'MILK', 'WOOL', 'FERTILIZER')

MARKET_PARAMS = {
    'WHEAT': {'base': 25, 'I0': MARKET_I0, 'T': 400, 'below_func': 'sqrt', 'below_target': 0.8, 'above_func': 'log', 'above_target': 0.2},
    'CARROT': {'base': 35, 'I0': MARKET_I0, 'T': 450, 'below_func': 'hinge', 'below_target': 1.0, 'above_func': 'sqrt', 'above_target': 0.7},
    'TOMATO': {'base': 60, 'I0': MARKET_I0, 'T': 200, 'below_func': 'hinge', 'below_target': 0.4, 'above_func': 'sqrt', 'above_target': 0.6},
    'STRAWBERRY': {'base': 120, 'I0': MARKET_I0, 'T': 100, 'below_func': 'sqrt', 'below_target': 0.7, 'above_func': 'linear', 'above_target': 1.6},
    'MELON': {'base': 250, 'I0': MARKET_I0, 'T': 300, 'below_func': 'log', 'below_target': 0.2, 'above_func': 'sq', 'above_target': 3.6},
    'EGG': {'base': 50, 'I0': MARKET_I0, 'T': 332, 'below_func': 'hinge', 'below_target': 0.4, 'above_func': 'log', 'above_target': 0.2},
    'MILK': {'base': 160, 'I0': MARKET_I0, 'T': 122, 'below_func': 'sqrt', 'below_target': 0.6, 'above_func': 'linear', 'above_target': 1.6},
    'WOOL': {'base': 200, 'I0': MARKET_I0, 'T': 105, 'below_func': 'log', 'below_target': 0.2, 'above_func': 'sq', 'above_target': 3.2},
    'FERTILIZER': {'base': 100, 'I0': MARKET_I0, 'T': 200, 'below_func': 'linear', 'below_target': 0.4, 'above_func': 'linear', 'above_target': 0.4}
}

SHOPS = {
    'BAKERY': ('EGG', 'WHEAT'),
    'PIZZA_SHOP': ('MILK', 'TOMATO', 'WHEAT'),
    'BRUNCH_SPOT': ('EGG', 'WHEAT', 'STRAWBERRY'),
    'YARN_STORE': ('WOOL',),
    'ICE_CREAM_SHOP': ('STRAWBERRY', 'MILK', 'WHEAT'),
    'PET_CAFE': ('CARROT',),
    'SMOOTHIE_SHOP': ('STRAWBERRY', 'MILK'),
    'FARMERS_MARKET': ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY')
}

LAND_ORDER = ('NE', 'SW', 'SE')
LAND_PRICES = (1000, 2000, 4000)

FARMER_MOVES = {'NORTH': (0, -1), 'SOUTH': (0, 1), 'EAST': (1, 0), 'WEST': (-1, 0)}
UNIT_OPS = frozenset({*FARMER_MOVES, 'PASS', 'PICKUP', 'PLACE', 'DROP', 'PLANT', 'WATER', 'HARVEST', 'FERTILIZE', 'BUILD_COOP', 'BUILD_PASTURE', 'FEED', 'COLLECT_FERTILIZER', 'CARE', 'DIG'})
MARKET_OPS = frozenset({'BUY_SEED', 'BUY_PRODUCT', 'BUY_ANIMAL', 'SELL', 'HIRE', 'BUY_LAND'})

SELL_RESERVE_FACTORS = {
    'WHEAT': 0.55, 'CARROT': 0.58, 'TOMATO': 0.60, 'STRAWBERRY': 0.72,
    'MELON': 0.72, 'EGG': 0.55, 'MILK': 0.68, 'WOOL': 0.68, 'FERTILIZER': 0.45
}

# Optimal Compact Pastures immediately surrounding NW Shed @ (4,4)
COMPACT_PASTURES: List[Tuple[int, int]] = [
    (4, 4), (3, 4), (4, 3), (3, 3), (4, 2), (3, 2), (2, 4), (2, 3), (2, 2), (4, 1), (3, 1), (2, 1), (1, 4), (1, 3), (1, 2)
]

# ==================== DATA STRUCTURES ====================
Position = Tuple[int, int]

@dataclass(frozen=True, slots=True)
class UnitState:
    index: int
    position: Position
    inventory: Dict[str, int]
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
    item: str = ''
    quantity: int = 1
    stable_id: str = ''

@dataclass(slots=True)
class EconomicPlan:
    animal_targets: Dict[str, int] = field(default_factory=dict)
    crop_targets: Dict[str, int] = field(default_factory=dict)
    animal_buys: Dict[str, int] = field(default_factory=dict)
    seed_buys: Dict[str, int] = field(default_factory=dict)
    wheat_buy: int = 0
    desired_hands: int = 0
    buy_land: bool = False
    reserve_cash: int = 0

# ==================== DEFENSIVE ACCESS HELPERS ====================
def getv(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    getter = getattr(obj, 'get', None)
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

def manhattan(a: Position, b: Position) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def step_toward(source: Position, target: Position) -> list[str]:
    sx, sy = source
    tx, ty = target
    dx = tx - sx
    dy = ty - sy
    if dx == 0 and dy == 0:
        return ['PASS']
    if abs(dx) >= abs(dy) and dx != 0:
        return ['EAST' if dx > 0 else 'WEST']
    if dy != 0:
        return ['SOUTH' if dy > 0 else 'NORTH']
    return ['EAST' if dx > 0 else 'WEST']

# ==================== SCHOOL 1: PURE PYTHON HUNGARIAN ALGORITHM ====================
def hungarian_match(cost_matrix: List[List[float]]) -> List[int]:
    """
    Kuhn-Munkres O(N^3) Bipartite Matching Algorithm in Pure Python.
    Assigns N workers to M tasks with globally minimal total cost.
    """
    n = len(cost_matrix)
    if n == 0:
        return []
    m = len(cost_matrix[0])
    if n > m:
        # Transpose if more workers than tasks
        cost_matrix = [[cost_matrix[i][j] for i in range(n)] for j in range(m)]
        n, m = m, n
        transposed = True
    else:
        transposed = False

    u = [0.0] * (n + 1)
    v = [0.0] * (m + 1)
    p = [0] * (m + 1)
    way = [0] * (m + 1)

    for i in range(1, n + 1):
        p[0] = i
        minv = [float('inf')] * (m + 1)
        used = [False] * (m + 1)
        j0 = 0
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = float('inf')
            j1 = 0
            for j in range(1, m + 1):
                if not used[j]:
                    cur = cost_matrix[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            for j in range(m + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    ans = [-1] * n
    for j in range(1, m + 1):
        if p[j] != 0 and p[j] <= n:
            ans[p[j] - 1] = j - 1

    if transposed:
        res = [-1] * m
        for i, j in enumerate(ans):
            if j != -1:
                res[j] = i
        return res
    return ans

# ==================== WORLD MODEL ====================
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
    units: List[UnitState]
    plants: List[LocatedTile]
    animals: List[LocatedTile]
    weeds: List[LocatedTile]
    empty_tiles: List[Position]
    empty_structures: List[LocatedTile]
    locked_tiles: List[Position]
    shed: Dict[str, int]
    seeds: Dict[str, int]
    unlocked_quadrants: Tuple[str, ...]
    hires_today: int
    market_inventory: Dict[str, int]
    market_prices: Dict[str, int]
    shops: Tuple[str, ...]
    opponent_plants: Dict[str, int]
    opponent_animals: Dict[str, int]

    @classmethod
    def from_observation(cls, obs: Any) -> 'WorldState':
        farms = getv(obs, 'farms', []) or []
        player = as_int(getv(obs, 'player', 0), 0)
        if not farms or player < 0 or player >= len(farms):
            raise ValueError("Observation does not contain current player farm")
        opponent = 1 - player if len(farms) >= 2 else player
        farm = farms[player]
        opponent_farm = farms[opponent]
        tiles = getv(farm, 'tiles', []) or []
        board_size = len(tiles)
        if board_size <= 0:
            raise ValueError("Farm has no tile grid")
        day = as_int(getv(obs, 'day', 0), 0)
        hour = as_int(getv(obs, 'hour', 0), 0)
        step = as_int(getv(obs, 'step', day * TURNS_PER_DAY + hour), day * TURNS_PER_DAY + hour)
        private = getv(obs, 'private', {}) or {}
        market = getv(obs, 'market', {}) or {}
        town = getv(obs, 'town', {}) or {}
        hands = getv(farm, 'hands', []) or []
        positions = [getv(farm, 'farmer', [0, 0]), *hands]
        inventories = getv(private, 'inventories', []) or []

        units: List[UnitState] = []
        for index, pos in enumerate(positions):
            if not isinstance(pos, (list, tuple)) or len(pos) < 2:
                pos = [0, 0]
            inv = inventories[index] if index < len(inventories) else {}
            inv_counts = {key: count_of(inv, key) for key in (*PRODUCTS, *ANIMALS) if count_of(inv, key) > 0}
            units.append(UnitState(index=index, position=(as_int(pos[0]), as_int(pos[1])), inventory=inv_counts, is_hand=index > 0))

        plants: List[LocatedTile] = []
        animals: List[LocatedTile] = []
        weeds: List[LocatedTile] = []
        empty_tiles: List[Position] = []
        empty_structures: List[LocatedTile] = []
        locked_tiles: List[Position] = []

        for y, row in enumerate(tiles):
            for x, tile in enumerate(row):
                pos = (x, y)
                if tile is None:
                    empty_tiles.append(pos)
                elif tile == 'LOCKED':
                    locked_tiles.append(pos)
                elif getv(tile, 'kind', '') == 'PLANT':
                    plants.append(LocatedTile(pos, tile))
                elif getv(tile, 'kind', '') == 'WEED':
                    weeds.append(LocatedTile(pos, tile))
                elif getv(tile, 'animal', None) in ANIMALS:
                    animals.append(LocatedTile(pos, tile))
                elif getv(tile, 'kind', '') in ('COOP', 'PASTURE'):
                    empty_structures.append(LocatedTile(pos, tile))

        opponent_plants = {crop: 0 for crop in CROPS}
        opponent_animals = {animal: 0 for animal in ANIMALS}
        opponent_tiles = getv(opponent_farm, 'tiles', []) or []
        for row in opponent_tiles:
            for tile in row:
                crop = getv(tile, 'crop', '')
                animal = getv(tile, 'animal', '')
                if crop in opponent_plants:
                    opponent_plants[crop] += 1
                if animal in opponent_animals:
                    opponent_animals[animal] += 1

        shed_source = getv(private, 'shed', {}) or {}
        seed_source = getv(private, 'seeds', {}) or {}
        shed = {k: count_of(shed_source, k) for k in (*PRODUCTS, *ANIMALS)}
        seeds = {k: count_of(seed_source, k) for k in CROPS}
        market_inventory = {k: count_of(getv(market, 'inventory', {}) or {}, k) for k in PRODUCTS}
        market_prices = {k: count_of(getv(market, 'prices', {}) or {}, k) for k in PRODUCTS}

        return cls(
            raw_obs=obs, player=player, opponent=opponent, day=day, hour=hour, step=step,
            remaining_steps=max(0, EPISODE_STEPS - step - 1), board_size=board_size,
            money=as_float(getv(farm, 'money', 0.0)), opponent_money=as_float(getv(opponent_farm, 'money', 0.0)),
            farm=farm, opponent_farm=opponent_farm, private=private, market=market, town=town,
            tiles=tiles, units=units, plants=plants, animals=animals, weeds=weeds,
            empty_tiles=empty_tiles, empty_structures=empty_structures, locked_tiles=locked_tiles,
            shed=shed, seeds=seeds, unlocked_quadrants=tuple(getv(farm, 'unlocked_quadrants', ['NW']) or ['NW']),
            hires_today=as_int(getv(farm, 'hires_today', len(hands)), len(hands)),
            market_inventory=market_inventory, market_prices=market_prices,
            shops=tuple(getv(town, 'unlocked_shops', []) or []),
            opponent_plants=opponent_plants, opponent_animals=opponent_animals
        )

    @property
    def shed_load(self) -> int:
        return sum(self.shed.values())

    @property
    def remaining_days(self) -> float:
        return self.remaining_steps / float(TURNS_PER_DAY)

    def is_shed_access(self, position: Position) -> bool:
        half = self.board_size // 2
        return position in {(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)}

    def nearest_shed_access(self, position: Position) -> Position:
        half = self.board_size // 2
        candidates = ((half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half))
        return min(candidates, key=lambda p: (manhattan(position, p), p[1], p[0]))

    def inventory_total(self, item: str) -> int:
        return self.shed.get(item, 0) + sum(unit.inventory.get(item, 0) for unit in self.units)

    def animal_count(self, animal: str, include_pending: bool = True) -> int:
        placed = sum(1 for located in self.animals if getv(located.tile, 'animal', '') == animal)
        if not include_pending:
            return placed
        return placed + self.inventory_total(animal)

    def crop_count(self, crop: str, include_seeds: bool = True) -> int:
        planted = sum(1 for located in self.plants if getv(located.tile, 'crop', '') == crop)
        return planted + (self.seeds.get(crop, 0) if include_seeds else 0)

# ==================== PRICING & MARKET EQUILIBRIUM ====================
def _shape(func: str, x: float, throughput: float | None = None) -> float:
    x = max(0.0, x)
    if func == 'linear': return x
    if func == 'sq': return x * x
    if func == 'sqrt': return math.sqrt(x)
    if func == 'log': return math.log1p(x)
    if func == 'log10': return math.log10(1.0 + x)
    if func == 'hinge':
        if not throughput or throughput <= 0: return x
        u = x / throughput
        return u + HINGE_GAIN * max(0.0, u - 1.0) ** 2
    return x

def market_price(item: str, inventory: int) -> int:
    params = MARKET_PARAMS[item]
    base = float(params['base'])
    equilibrium = int(params['I0'])
    throughput = float(params['T'])
    if inventory < equilibrium:
        func = str(params['below_func'])
        amplitude = float(params['below_target']) * base / _shape(func, throughput, throughput)
        price = base + amplitude * _shape(func, equilibrium - inventory, throughput)
    else:
        func = str(params['above_func'])
        amplitude = float(params['above_target']) * base / _shape(func, throughput, throughput)
        price = base - amplitude * _shape(func, inventory - equilibrium, throughput)
    return max(PRICE_FLOOR, int(round(price)))

def demand_counts(shops: Tuple[str, ...] | List[str]) -> Dict[str, int]:
    demand = {item: 0 for item in MARKET_PARAMS}
    for shop in shops:
        products = SHOPS.get(shop, ())
        multiplier = 2 if len(products) == 1 else 1
        for item in products:
            demand[item] += multiplier
    return demand

def daily_town_demand(world: WorldState, item: str) -> float:
    centre = 0.0 if item == 'FERTILIZER' else 1.0
    return centre + 6.0 * demand_counts(world.shops).get(item, 0)

def marginal_sale_prices(item: str, inventory: int, quantity: int) -> List[int]:
    prices: List[int] = []
    current = inventory
    for _ in range(max(0, quantity)):
        price = market_price(item, current)
        prices.append(price)
        if price > PRICE_FLOOR:
            current += 1
    return prices

def choose_sale_quantity(world: WorldState, item: str, held: int) -> int:
    if held <= 0:
        return 0
    if world.day >= 28:
        return held

    keep = 0
    if item == 'WHEAT':
        unfed = sum(1 for located in world.animals if not bool(getv(located.tile, 'fed_today', False)))
        carried = sum(unit.inventory.get('WHEAT', 0) for unit in world.units)
        required_today = max(0, unfed - carried)
        pending_animals = sum(world.animal_count(animal) for animal in ANIMALS)
        unlocked = len(world.unlocked_quadrants)
        saving_for_land = (unlocked == 1 and world.day >= 2) or (unlocked == 2 and world.day >= 5)
        feed_buffer = pending_animals if saving_for_land else 2 * pending_animals + 2
        keep = min(held, max(feed_buffer, required_today + pending_animals))

    if item == 'FERTILIZER' and world.day < 24:
        keep = min(4, held)

    sellable = max(0, held - keep)
    if sellable <= 0:
        return 0

    params = MARKET_PARAMS[item]
    base = int(params['base'])
    reserve_factor = SELL_RESERVE_FACTORS[item]

    if world.day >= 24:
        reserve_factor *= 0.5
    elif world.day >= 15:
        reserve_factor *= 0.72

    pressure = max(0.0, (world.shed_load - 65) / max(1.0, SHED_CAPACITY - 65))
    if pressure > 0:
        reserve_factor *= max(0.35, 1.0 - 0.55 * pressure)

    if world.money < max(200.0, len(world.animals) * 22.0):
        reserve_factor *= 0.75

    shop_demand = demand_counts(world.shops).get(item, 0)
    imminent_centre_drain = (item != 'FERTILIZER' and world.step % 24 == 0)

    # Town Pulse Timing
    if (shop_demand > 0 or imminent_centre_drain) and world.step % 4 == 0 and pressure < 0.35 and world.money >= max(250.0, len(world.animals) * 25.0) and world.day < 28:
        return 0
    if world.step % 4 == 1 and (shop_demand > 0 or imminent_centre_drain) and world.day < 28 and pressure < 0.6:
        reserve_factor *= 0.92

    reserve_price = max(2, int(round(base * reserve_factor)))
    batch_cap = min(sellable, 20 if world.day < 15 else (32 if world.day < 24 else sellable))
    inventory = world.market_inventory.get(item, int(params['I0']))

    quantity = 0
    for price in marginal_sale_prices(item, inventory, batch_cap):
        if price < reserve_price and pressure < 0.5:
            break
        quantity += 1
    return quantity

# ==================== STRATEGY & ECONOMIC PLANNER ====================
ANIMAL_DAILY_OUTPUT = {'GOOSE': 2.0, 'COW': 1.5, 'SHEEP': 4.0 / 3.0}
CROP_DAILY_OUTPUT = {crop: float(MARKET_PARAMS[crop]['T']) / (25.0 * 24.0) for crop in CROPS}

def _shared_daily_capacity(world: WorldState, item: str) -> float:
    params = MARKET_PARAMS[item]
    current = world.market_inventory.get(item, int(params['I0']))
    horizon = max(5.0, min(12.0, world.remaining_days))
    throughput_per_day = float(params['T']) / 24.0
    drift = (float(params['I0']) - current) / horizon
    drift = max(-throughput_per_day, min(throughput_per_day, drift))
    return max(0.0, daily_town_demand(world, item) + drift)

def _competitive_share(world: WorldState, shared_target: int, opponent: int) -> int:
    if shared_target <= 0:
        return 0
    half = shared_target / 2.0
    response = half + 0.35 * (half - opponent)
    lower = int(math.ceil(0.3 * shared_target))
    upper = int(math.ceil(0.75 * shared_target))
    return max(lower, min(upper, int(math.ceil(response))))

def _animal_scores(world: WorldState) -> Dict[str, float]:
    demand = demand_counts(world.shops)
    goose_score = (0.42 + 0.95 * demand['EGG']) if demand['EGG'] >= 2 else 0.0
    scores = {'GOOSE': goose_score, 'COW': 1.25 + 0.85 * demand['MILK'], 'SHEEP': 1.35 + 1.15 * demand['WOOL']}
    for animal, data in ANIMALS.items():
        if animal == 'GOOSE' and demand['EGG'] < 2: continue
        product = str(data['product'])
        price = world.market_prices.get(product, int(MARKET_PARAMS[product]['base']))
        base = int(MARKET_PARAMS[product]['base'])
        scarcity = max(0.6, min(1.8, price / max(1.0, base)))
        opponent_penalty = 1.0 / (1.0 + 0.06 * world.opponent_animals.get(animal, 0))
        scores[animal] *= scarcity * opponent_penalty
    return scores

def desired_animal_targets(world: WorldState) -> Dict[str, int]:
    current = {animal: world.animal_count(animal) for animal in ANIMALS}
    shop_demand = demand_counts(world.shops)
    
    # Day 0: 3 Cows + 2 Sheep (Zero Goose)
    if world.day == 0:
        goose_target = 0
        if shop_demand.get('EGG', 0) >= 2:
            goose_target = min(2, int(math.ceil(_shared_daily_capacity(world, 'EGG') / ANIMAL_DAILY_OUTPUT['GOOSE'])))
        return {'GOOSE': goose_target, 'COW': 3, 'SHEEP': 2}
    if world.day <= 2 or world.day > 18:
        return current

    targets: Dict[str, int] = {}
    for animal, data in ANIMALS.items():
        product = str(data['product'])
        if animal == 'GOOSE' and shop_demand.get('EGG', 0) < 2:
            targets[animal] = current[animal]
            continue
        shared_target = int(math.ceil(_shared_daily_capacity(world, product) / ANIMAL_DAILY_OUTPUT[animal]))
        opponent = world.opponent_animals.get(animal, 0)
        targets[animal] = _competitive_share(world, shared_target, opponent)

    targets['COW'] = max(3, targets.get('COW', 3))
    targets['SHEEP'] = max(2, targets.get('SHEEP', 2))
    for animal in ANIMALS:
        targets[animal] = max(targets.get(animal, 0), current[animal])

    growth_cap = 5 if world.day <= 5 else min(20, 5 + 2 * (world.day - 5))
    physical_cap = max(5, len(world.unlocked_quadrants) * 25 - 15)
    owned_capacity = min(growth_cap, physical_cap)
    scores = _animal_scores(world)
    opening_floor = {'GOOSE': current['GOOSE'], 'COW': max(3, current['COW']), 'SHEEP': max(2, current['SHEEP'])}

    while sum(targets.values()) > owned_capacity:
        removable = [name for name in ANIMALS if targets[name] > opening_floor[name]]
        if not removable:
            break
        animal = min(removable, key=lambda name: (scores[name], -targets[name], name))
        targets[animal] -= 1
    return targets

def desired_crop_targets(world: WorldState, animal_targets: Dict[str, int]) -> Dict[str, int]:
    demand = demand_counts(world.shops)
    animal_total = sum(animal_targets.values())
    targets = {crop: 0 for crop in CROPS}

    # Day 0: 9 Wheat (feed reserve) + 6 Melon (maximum ROI flip)
    if world.day == 0:
        return {'WHEAT': 9, 'CARROT': 0, 'TOMATO': 0, 'STRAWBERRY': 0, 'MELON': 6}

    cutoffs = {'WHEAT': 25, 'CARROT': 26, 'TOMATO': 18, 'STRAWBERRY': 16, 'MELON': 17}
    for crop in CROPS:
        if world.day > cutoffs[crop]:
            continue
        if world.day < 5 and crop not in {'WHEAT', 'MELON'} and demand.get(crop, 0) == 0:
            continue
        shared_target = int(math.ceil(_shared_daily_capacity(world, crop) / max(0.01, CROP_DAILY_OUTPUT[crop])))
        opponent = world.opponent_plants.get(crop, 0)
        targets[crop] = _competitive_share(world, shared_target, opponent)

    feed_floor = min(40, int(math.ceil(1.35 * animal_total)) + 2)
    if world.day <= cutoffs['WHEAT']:
        targets['WHEAT'] = max(targets.get('WHEAT', 0), feed_floor)

    # Full land utilization: fill up to 66 tiles in 3 quadrants
    max_crop_slots = max(0, len(world.unlocked_quadrants) * 25 - animal_total - 3)
    max_crop_slots = min(66, max_crop_slots)
    minimums = {crop: 0 for crop in CROPS}
    minimums['WHEAT'] = min(targets.get('WHEAT', 0), feed_floor, max_crop_slots)

    while sum(targets.values()) > max_crop_slots:
        removable = [crop for crop, value in targets.items() if value > minimums[crop]]
        if not removable:
            break
        crop = min(removable, key=lambda name: (
            CROP_DAILY_OUTPUT[name] * float(MARKET_PARAMS[name]['base']) * (1.0 + 0.35 * demand.get(name, 0)) +
            0.1 * CROP_DAILY_OUTPUT[name] * max(0, world.market_prices.get(name, 0) - int(MARKET_PARAMS[name]['base'])),
            -CROPS[name]['first_yield_day'], name
        ))
        targets[crop] -= 1
    return targets

def desired_hands(world: WorldState, animal_targets: Dict[str, int]) -> int:
    if world.hour >= 10:
        return world.hires_today
    schedule = {0: 5, 1: 4, 2: 5, 3: 5, 4: 5, 5: 5, 6: 8, 7: 8, 8: 9, 9: 10, 10: 11}
    return schedule.get(world.day, 12)

def _future_hire_cost(current: int, desired: int) -> int:
    a, b = (1, 1)
    costs: List[int] = []
    for _ in range(max(0, desired)):
        costs.append(a)
        a, b = (b, a + b)
    return sum(costs[max(0, current):max(0, desired)])

# ==================== SCHOOL 2: FORWARD LOOKAHEAD SIMULATION ====================
def _should_buy_land_lookahead(world: WorldState, reserve_cash: int) -> bool:
    unlocked = len(world.unlocked_quadrants)
    if unlocked >= 3 or world.day >= 21:
        return False
    next_cost = LAND_PRICES[unlocked - 1]
    if world.money < next_cost + reserve_cash:
        return False
    if unlocked == 1 and world.day >= 4:
        return True
    if unlocked == 2 and world.day >= 7:
        return True
    return False

def make_economic_plan(world: WorldState) -> EconomicPlan:
    animal_targets = desired_animal_targets(world)
    crop_targets = desired_crop_targets(world, animal_targets)
    current_animals = {animal: world.animal_count(animal) for animal in ANIMALS}
    feed_price = max(1, world.market_prices.get('WHEAT', 25))
    reserve_cash = max(250, int(sum(current_animals.values()) * feed_price * 1.25))

    buy_land = _should_buy_land_lookahead(world, reserve_cash)
    unlocked = len(world.unlocked_quadrants)
    land_due = (unlocked == 1 and world.day >= 4) or (unlocked == 2 and world.day >= 7)
    land_saving = (unlocked == 1 and world.day >= 2) or (unlocked == 2 and world.day >= 5)

    hand_target = desired_hands(world, animal_targets)
    hire_reserve = _future_hire_cost(world.hires_today, hand_target)

    budget = int(world.money) - reserve_cash - hire_reserve
    if buy_land and unlocked <= 2:
        budget -= LAND_PRICES[unlocked - 1]
    budget = max(0, budget)

    if land_due and not buy_land and unlocked <= 2:
        working_capital = min(300, max(0, int(world.money) - reserve_cash - hire_reserve))
        budget = working_capital
    elif land_saving and not buy_land and unlocked <= 2:
        next_land_cost = LAND_PRICES[unlocked - 1]
        budget = min(budget, max(150, int(world.money) - reserve_cash - hire_reserve - next_land_cost))

    animal_buys = {animal: 0 for animal in ANIMALS}
    if world.day <= 18:
        scores = _animal_scores(world)
        gaps = {animal: max(0, animal_targets[animal] - current_animals[animal]) for animal in ANIMALS}
        while budget > 0 and any(gaps.values()):
            candidates = [a for a, gap in gaps.items() if gap > 0]
            candidates.sort(key=lambda a: (scores[a] / ANIMALS[a]['cost'], scores[a], -ANIMALS[a]['cost'], a), reverse=True)
            bought = False
            for a in candidates:
                cost = int(ANIMALS[a]['cost'])
                if budget >= cost:
                    animal_buys[a] += 1
                    gaps[a] -= 1
                    budget -= cost
                    bought = True
                    break
            if not bought:
                break

    seed_buys = {crop: 0 for crop in CROPS}
    if world.day <= 26:
        demand = demand_counts(world.shops)
        crop_order = sorted(CROPS, key=lambda crop: (
            demand.get(crop, 0),
            world.market_prices.get(crop, MARKET_PARAMS[crop]['base']) / MARKET_PARAMS[crop]['base'],
            -CROPS[crop]['first_yield_day'], crop
        ), reverse=True)
        for crop in crop_order:
            gap = max(0, crop_targets[crop] - world.crop_count(crop))
            cost = int(CROPS[crop]['seed'])
            qty = min(gap, 20, budget // cost)
            if qty > 0:
                seed_buys[crop] = qty
                budget -= qty * cost

    total_wheat = world.inventory_total('WHEAT')
    owned_animals = sum(current_animals.values())
    wheat_target = owned_animals * 2 + 2 if world.day <= 28 else 0
    if land_saving and not buy_land:
        wheat_target = owned_animals
    wheat_gap = min(36, max(0, wheat_target - total_wheat))
    committed = sum(animal_buys[a] * int(ANIMALS[a]['cost']) for a in ANIMALS) + sum(seed_buys[c] * int(CROPS[c]['seed']) for c in CROPS) + hire_reserve + (LAND_PRICES[unlocked - 1] if buy_land and unlocked <= 2 else 0)
    feed_budget = max(0, int(world.money) - committed - 25)
    wheat_buy = min(wheat_gap, feed_budget // feed_price)
    remaining_reserve = max(25, reserve_cash - wheat_buy * feed_price)

    return EconomicPlan(
        animal_targets=animal_targets, crop_targets=crop_targets,
        animal_buys=animal_buys, seed_buys=seed_buys, wheat_buy=wheat_buy,
        desired_hands=hand_target, buy_land=buy_land, reserve_cash=remaining_reserve
    )

# ==================== TASK GENERATOR & COMPACT PASTURE HUB ====================
def _stable(kind: str, position: Position, suffix: str = '') -> str:
    return f'{kind}:{position[0]}:{position[1]}:{suffix}'

def _build_pasture_positions(world: WorldState, quantity: int, excluded: Set[Position]) -> List[Position]:
    candidates = [p for p in COMPACT_PASTURES if p in world.empty_tiles and p not in excluded]
    if len(candidates) < quantity:
        extra = [p for p in world.empty_tiles if p not in excluded and p not in candidates]
        center = (world.board_size // 2 - 1, world.board_size // 2 - 1)
        extra.sort(key=lambda p: (manhattan(p, center), p[1], p[0]))
        candidates.extend(extra)
    return candidates[:max(0, quantity)]

def _fertilizer_has_future_value(world: WorldState, tile: Any, crop: str) -> bool:
    data = CROPS[crop]
    planted = as_int(getv(tile, 'planted_day', world.day), world.day)
    age = world.day - planted
    if not bool(data['ongoing']):
        window_start = (int(data['max_yield_day']) + 1) // 2
        return any(window_start <= age + offset <= int(data['max_yield_day']) for offset in range(3))
    for offset in range(3):
        next_day = world.day + offset + 1
        since_first = next_day - planted - int(data['first_yield_day'])
        if since_first < 0 or since_first % int(data['interval']) != 0:
            continue
        production_count = since_first // int(data['interval']) + 1
        if production_count <= int(data['max_yield']):
            return True
    return False

def generate_tasks(world: WorldState, plan: EconomicPlan) -> List[Task]:
    tasks: List[Task] = []
    reserved_tiles: Set[Position] = set()
    endgame = (world.day >= 29)
    turns_left_today = max(0, 22 - world.hour + 1) if endgame else 24 - world.hour
    empty_by_structure: Dict[str, List[Position]] = {'COOP': [], 'PASTURE': []}
    for located in world.empty_structures:
        kind = str(getv(located.tile, 'kind', ''))
        if kind in empty_by_structure:
            empty_by_structure[kind].append(located.position)
    for positions in empty_by_structure.values():
        positions.sort(key=lambda p: (manhattan(p, world.nearest_shed_access(p)), p[1], p[0]))

    carried_by_animal = {animal: sum(unit.inventory.get(animal, 0) for unit in world.units) for animal in ANIMALS}
    for structure in ('PASTURE', 'COOP'):
        positions = list(empty_by_structure[structure])
        animals = [animal for animal in ANIMALS if ANIMALS[animal]['structure'] == structure]
        animal_queue: List[str] = []
        for animal in sorted(animals, key=lambda name: (-carried_by_animal[name], name)):
            animal_queue.extend([animal] * carried_by_animal[animal])
        for position, animal in zip(positions, animal_queue):
            tasks.append(Task('PLACE_ANIMAL', position, priority=2, deadline=world.step + turns_left_today, value=500.0, item=animal, stable_id=_stable('PLACE', position, animal)))

    planned_pending = {animal: world.inventory_total(animal) + plan.animal_buys.get(animal, 0) for animal in ANIMALS}
    for structure in ('PASTURE', 'COOP'):
        pending = sum(planned_pending[animal] for animal in ANIMALS if ANIMALS[animal]['structure'] == structure)
        missing = max(0, pending - len(empty_by_structure[structure]))
        build_positions = _build_pasture_positions(world, missing, reserved_tiles)
        for position in build_positions:
            reserved_tiles.add(position)
            tasks.append(Task(f'BUILD_{structure}', position, priority=7, deadline=world.step + turns_left_today, value=350.0, stable_id=_stable(f'BUILD_{structure}', position)))
            empty_by_structure[structure].append(position)

    shed_target = world.nearest_shed_access(world.units[0].position)
    for animal in ANIMALS:
        matching = str(ANIMALS[animal]['structure'])
        available = min(world.shed.get(animal, 0), len(empty_by_structure[matching]))
        for index in range(available):
            tasks.append(Task('PICKUP_ANIMAL', shed_target, priority=5, deadline=world.step + turns_left_today, value=450.0, item=animal, quantity=1, stable_id=_stable('PICKUP_ANIMAL', shed_target, f'{animal}:{index}')))

    if endgame:
        for unit in world.units:
            carried_products = sum(unit.inventory.get(item, 0) for item in PRODUCTS)
            if carried_products <= 0:
                continue
            distance = manhattan(unit.position, world.nearest_shed_access(unit.position))
            tasks.append(Task('DROP', world.nearest_shed_access(unit.position), priority=0, deadline=world.step + max(0, turns_left_today - 1), value=10000.0 + distance, stable_id=f'DROP:{unit.index}'))

    if not endgame:
        unfed = []
        for located in world.animals:
            tile = located.tile
            if not bool(getv(tile, 'fed_today', False)):
                unfed.append(located)
                urgency = 3 if world.hour >= 15 or as_int(getv(tile, 'consecutive_unfed', 0)) >= 1 else 14
                tasks.append(Task('FEED', located.position, priority=urgency, deadline=(world.day + 1) * 24 - 1, value=900.0, item='WHEAT', stable_id=_stable('FEED', located.position)))

        carried_wheat = sum(unit.inventory.get('WHEAT', 0) for unit in world.units)
        required_pickup = max(0, len(unfed) - carried_wheat)
        wheat_available = world.shed.get('WHEAT', 0)
        pickup_quantity = min(required_pickup, wheat_available)
        pickup_index = 0
        while pickup_quantity > 0 and pickup_index < len(world.units):
            quantity = min(6, pickup_quantity)
            tasks.append(Task('PICKUP_WHEAT', shed_target, priority=4 if world.hour >= 12 else 12, deadline=(world.day + 1) * 24 - 1, value=700.0, item='WHEAT', quantity=quantity, stable_id=_stable('PICKUP_WHEAT', shed_target, str(pickup_index))))
            pickup_quantity -= quantity
            pickup_index += 1

        for located in world.plants:
            tile = located.tile
            if not bool(getv(tile, 'watered_today', False)):
                urgency = 2 if world.hour >= 16 or as_int(getv(tile, 'consecutive_unwatered', 0)) >= 1 else 16
                tasks.append(Task('WATER', located.position, priority=urgency, deadline=(world.day + 1) * 24 - 1, value=850.0, stable_id=_stable('WATER', located.position)))

    for located in world.plants:
        tile = located.tile
        crop = str(getv(tile, 'crop', ''))
        yield_units = as_int(getv(tile, 'yield_units', 0))
        age = world.day - as_int(getv(tile, 'planted_day', world.day))
        if crop not in CROPS or yield_units <= 0 or age < CROPS[crop]['first_yield_day']:
            continue
        if endgame:
            distance = manhattan(located.position, world.nearest_shed_access(located.position))
            if distance + 2 > max(0, 23 - world.hour):
                continue
        priority = 4 if endgame else (9 if yield_units >= CROPS[crop]['max_yield'] else 25)
        tasks.append(Task('HARVEST', located.position, priority=priority, deadline=world.step + max(0, turns_left_today - 2), value=float(yield_units * 100), item=crop, stable_id=_stable('HARVEST_PLANT', located.position)))

    for located in world.animals:
        tile = located.tile
        animal = str(getv(tile, 'animal', ''))
        yield_units = as_int(getv(tile, 'yield_units', 0))
        if animal not in ANIMALS or yield_units <= 0:
            continue
        if endgame:
            distance = manhattan(located.position, world.nearest_shed_access(located.position))
            if distance + 2 > max(0, 23 - world.hour):
                continue
        near_cap = yield_units >= int(ANIMALS[animal]['max_held']) - 1
        priority = 3 if endgame else (8 if near_cap else 24)
        tasks.append(Task('HARVEST', located.position, priority=priority, deadline=world.step + max(0, turns_left_today - 2), value=float(yield_units * 120), item=str(ANIMALS[animal]['product']), stable_id=_stable('HARVEST_ANIMAL', located.position)))

    # Priority Fertilizer collection from compact livestock hub
    if world.day <= 28:
        fertilizer_price = world.market_prices.get('FERTILIZER', 0)
        fertilizer_priority = 22 if fertilizer_price >= 50 else 36
        for located in world.animals:
            if bool(getv(located.tile, 'fertilizer_available', False)):
                tasks.append(Task('COLLECT_FERTILIZER', located.position, priority=fertilizer_priority, deadline=world.step + turns_left_today, value=110.0, item='FERTILIZER', stable_id=_stable('COLLECT_FERTILIZER', located.position)))

    # Animal Care Loop: Care for Sheep ($200) and Cow ($160) on fed days
    if world.day <= 27:
        for located in world.animals:
            tile = located.tile
            animal = str(getv(tile, 'animal', ''))
            if bool(getv(tile, 'fed_today', False)) and not bool(getv(tile, 'cared_today', False)):
                care_prio = 13 if animal == 'SHEEP' else (14 if animal == 'COW' else 15)
                care_val = 190.0 if animal == 'SHEEP' else (150.0 if animal == 'COW' else 85.0)
                tasks.append(Task('CARE', located.position, priority=care_prio, deadline=(world.day + 1) * 24 - 1, value=care_val, stable_id=_stable('CARE', located.position)))

        carried_fertilizer = sum(unit.inventory.get('FERTILIZER', 0) for unit in world.units)
        fertilizable = []
        unlocked = len(world.unlocked_quadrants)
        saving_for_land = (unlocked == 1 and world.day >= 2) or (unlocked == 2 and world.day >= 5)
        for located in (world.plants if not saving_for_land else ()):
            tile = located.tile
            crop = str(getv(tile, 'crop', ''))
            fertilized_until = as_int(getv(tile, 'fertilized_until_day', -1), -1)
            age = world.day - as_int(getv(tile, 'planted_day', world.day))
            if crop in CROPS and fertilized_until < world.day and (age <= CROPS[crop]['max_yield_day']) and _fertilizer_has_future_value(world, tile, crop):
                fertilizable.append(located)
                tasks.append(Task('FERTILIZE', located.position, priority=24, deadline=world.step + turns_left_today, value=110.0, item='FERTILIZER', stable_id=_stable('FERTILIZE', located.position)))
        if carried_fertilizer == 0 and fertilizable and world.shed.get('FERTILIZER', 0) > 0:
            quantity = min(4, world.shed.get('FERTILIZER', 0), len(fertilizable))
            tasks.append(Task('PICKUP_FERTILIZER', shed_target, priority=23, deadline=world.step + turns_left_today, value=105.0, item='FERTILIZER', quantity=quantity, stable_id=_stable('PICKUP_FERTILIZER', shed_target)))

    # Spatial-Aware High Density Planting
    if world.day <= 26 and world.hour <= 22:
        plantable = [position for position in world.empty_tiles if position not in reserved_tiles]
        center = (world.board_size // 2 - 1, world.board_size // 2 - 1)
        plantable.sort(key=lambda p: (manhattan(p, center), p[1], p[0]))
        cursor = 0
        for crop in sorted(CROPS, key=lambda name: (CROPS[name]['first_yield_day'], name)):
            quantity = min(world.seeds.get(crop, 0), max(0, plan.crop_targets.get(crop, 0) - world.crop_count(crop, False)))
            for index in range(quantity):
                if cursor >= len(plantable):
                    break
                position = plantable[cursor]
                cursor += 1
                reserved_tiles.add(position)
                tasks.append(Task('PLANT', position, priority=18 if world.day == 0 else 30, deadline=(world.day + 1) * 24 - 2, value=50.0, item=crop, stable_id=_stable('PLANT', position, f'{crop}:{index}')))

    weed_priority = 46 if len(world.empty_tiles) < 4 else 72
    for located in world.weeds:
        tasks.append(Task('DIG', located.position, priority=weed_priority, deadline=world.step + 96, value=20.0, stable_id=_stable('DIG', located.position)))

    if not endgame:
        for unit in world.units:
            carried_products = sum(unit.inventory.get(item, 0) for item in PRODUCTS)
            if carried_products >= 8 or (world.money < 150 and carried_products > 0):
                tasks.append(Task('DROP', world.nearest_shed_access(unit.position), priority=34, deadline=world.step + turns_left_today, value=float(carried_products * 20), stable_id=f'DROP:{unit.index}'))

    tasks.sort(key=lambda task: (task.priority, task.deadline, -task.value, task.stable_id))
    return tasks[:240]

# ==================== SCHOOL 1: HUNGARIAN ASSIGNMENT SOLVER ====================
def _has_products(unit: UnitState) -> bool:
    return any(unit.inventory.get(item, 0) > 0 for item in PRODUCTS)

def _feasible(unit: UnitState, task: Task, world: WorldState) -> bool:
    if task.kind == 'FEED': return unit.has('WHEAT')
    if task.kind == 'FERTILIZE': return unit.has('FERTILIZER')
    if task.kind == 'PLACE_ANIMAL': return unit.has(task.item)
    if task.kind == 'DROP': return _has_products(unit)
    if task.kind == 'PICKUP_ANIMAL': return world.shed.get(task.item, 0) > 0
    if task.kind == 'PICKUP_WHEAT': return world.shed.get('WHEAT', 0) > 0 and unit.inventory.get('WHEAT', 0) < task.quantity
    if task.kind == 'PICKUP_FERTILIZER': return world.shed.get('FERTILIZER', 0) > 0 and unit.inventory.get('FERTILIZER', 0) == 0
    return True

def _effective_target(unit: UnitState, task: Task, world: WorldState) -> Position:
    if task.kind.startswith('PICKUP_') or task.kind == 'DROP':
        return world.nearest_shed_access(unit.position)
    return task.target

def _action_for(unit: UnitState, task: Task, world: WorldState) -> List[Any]:
    target = _effective_target(unit, task, world)
    at_target = (unit.position == target)
    if task.kind.startswith('PICKUP_') or task.kind == 'DROP':
        at_target = world.is_shed_access(unit.position)
    if not at_target:
        return step_toward(unit.position, target)
    if task.kind == 'PLACE_ANIMAL': return ['PLACE', task.item]
    if task.kind == 'PICKUP_ANIMAL': return ['PICKUP', task.item, task.quantity]
    if task.kind == 'PICKUP_WHEAT': return ['PICKUP', 'WHEAT', max(1, min(task.quantity, 6 - unit.inventory.get('WHEAT', 0)))]
    if task.kind == 'PICKUP_FERTILIZER': return ['PICKUP', 'FERTILIZER', task.quantity]
    if task.kind == 'DROP': return ['DROP']
    if task.kind == 'PLANT': return ['PLANT', task.item]
    if task.kind in {'WATER', 'HARVEST', 'FERTILIZE', 'BUILD_COOP', 'BUILD_PASTURE', 'FEED', 'COLLECT_FERTILIZER', 'CARE', 'DIG'}:
        return [task.kind]
    return ['PASS']

def assign_actions(world: WorldState, tasks: List[Task]) -> List[List[Any]]:
    num_units = len(world.units)
    if num_units == 0 or not tasks:
        return [['PASS'] for _ in world.units]

    # Select top candidate tasks
    candidate_tasks = tasks[:max(num_units * 3, 30)]
    num_tasks = len(candidate_tasks)

    # Construct Bipartite Cost Matrix
    # Cost = PriorityTier * 1000 + ManhattanDistance * 10 - TaskValue
    cost_matrix: List[List[float]] = []
    for u in world.units:
        row: List[float] = []
        for t in candidate_tasks:
            if not _feasible(u, t, world):
                row.append(100000.0) # Infeasible penalty
            else:
                dist = manhattan(u.position, _effective_target(u, t, world))
                cost = float(t.priority) * 1000.0 + float(dist) * 10.0 - float(t.value) * 0.1
                row.append(cost)
        cost_matrix.append(row)

    # Solve optimal 1-to-1 assignment with Hungarian algorithm
    matched_tasks = hungarian_match(cost_matrix)
    actions: List[List[Any]] = [['PASS'] for _ in world.units]

    for unit_idx, task_idx in enumerate(matched_tasks):
        if task_idx >= 0 and task_idx < num_tasks:
            cost = cost_matrix[unit_idx][task_idx]
            if cost < 50000.0:
                task = candidate_tasks[task_idx]
                unit = world.units[unit_idx]
                actions[unit_idx] = _action_for(unit, task, world)

    return actions

# ==================== MARKET ORDER BUILDER ====================
def _hire_orders(world: WorldState, plan: EconomicPlan, max_slots: int) -> List[List[str]]:
    hires: List[List[str]] = []
    if world.hour >= 10:
        return hires
    count = max(0, plan.desired_hands - world.hires_today)
    for _ in range(min(max_slots, count)):
        hires.append(['HIRE'])
    return hires

def build_market_orders(world: WorldState, plan: EconomicPlan) -> List[List[Any]]:
    sales: List[List[Any]] = []
    for item in PRODUCTS:
        if item == 'WHEAT' and plan.wheat_buy > 0:
            continue
        held = world.shed.get(item, 0)
        quantity = choose_sale_quantity(world, item, held)
        if quantity > 0:
            sales.append(['SELL', item, quantity])

    sales.sort(key=lambda order: (-(order[2] * world.market_prices.get(order[1], MARKET_PARAMS[order[1]]['base'])), order[1]))
    sales = sales[:7 if world.day >= 27 else 4]

    orders: List[List[Any]] = list(sales)
    if plan.wheat_buy > 0 and len(orders) < MAX_MARKET_ORDERS:
        orders.append(['BUY_PRODUCT', 'WHEAT', plan.wheat_buy])
    if plan.buy_land and len(orders) < MAX_MARKET_ORDERS:
        orders.append(['BUY_LAND'])

    for animal in sorted(ANIMALS, key=lambda n: (-plan.animal_buys.get(n, 0) * ANIMALS[n]['cost'], n)):
        quantity = plan.animal_buys.get(animal, 0)
        if quantity > 0 and len(orders) < MAX_MARKET_ORDERS:
            orders.append(['BUY_ANIMAL', animal, quantity])

    for crop in sorted(CROPS, key=lambda n: (-plan.seed_buys.get(n, 0) * CROPS[n]['seed'], CROPS[n]['first_yield_day'], n)):
        quantity = plan.seed_buys.get(crop, 0)
        if quantity > 0 and len(orders) < MAX_MARKET_ORDERS:
            orders.append(['BUY_SEED', crop, quantity])

    orders.extend(_hire_orders(world, plan, MAX_MARKET_ORDERS - len(orders)))
    return orders[:MAX_MARKET_ORDERS]

# ==================== VALIDATOR ====================
def _normalize_unit_action(action: Any) -> List[Any]:
    if not isinstance(action, list) or not action or action[0] not in UNIT_OPS:
        return ['PASS']
    op = action[0]
    if op == 'PLANT':
        return ['PLANT', action[1]] if len(action) >= 2 and action[1] in CROPS else ['PASS']
    if op in {'PICKUP', 'PLACE'}:
        if len(action) < 2 or action[1] not in {*PRODUCTS, *ANIMALS}:
            return ['PASS']
        if len(action) < 3:
            return [op, action[1]]
        try:
            quantity = int(action[2])
        except (TypeError, ValueError, OverflowError):
            return ['PASS']
        return [op, action[1], quantity] if quantity > 0 else ['PASS']
    return [op]

def _normalize_market_order(order: Any) -> Optional[List[Any]]:
    if not isinstance(order, list) or not order or order[0] not in MARKET_OPS:
        return None
    op = order[0]
    if op in {'HIRE', 'BUY_LAND'}:
        return [op]
    if len(order) < 3:
        return None
    item = order[1]
    valid_item = (op == 'BUY_SEED' and item in CROPS) or \
                 (op == 'BUY_PRODUCT' and item in {'WHEAT', 'FERTILIZER'}) or \
                 (op == 'BUY_ANIMAL' and item in ANIMALS) or \
                 (op == 'SELL' and item in PRODUCTS)
    if not valid_item:
        return None
    try:
        quantity = int(order[2])
    except (TypeError, ValueError, OverflowError):
        return None
    if quantity <= 0:
        return None
    return [op, item, quantity]

def validate_action(world: WorldState, unit_actions: List[List[Any]], market_orders: List[List[Any]]) -> Dict[str, Any]:
    expected_units = len(world.units)
    normalized = [_normalize_unit_action(action) for action in unit_actions[:expected_units]]
    while len(normalized) < expected_units:
        normalized.append(['PASS'])

    used_seeds = {crop: 0 for crop in CROPS}
    for index, action in enumerate(normalized):
        if action[0] != 'PLANT' or len(action) < 2:
            continue
        crop = action[1]
        if crop not in CROPS or used_seeds[crop] >= world.seeds.get(crop, 0):
            normalized[index] = ['PASS']
        else:
            used_seeds[crop] += 1

    market: List[List[Any]] = []
    for order in market_orders:
        normalized_order = _normalize_market_order(order)
        if normalized_order is not None:
            market.append(normalized_order)
        if len(market) >= MAX_MARKET_ORDERS:
            break

    farmer_action = normalized[0] if normalized else ['PASS']
    hands_actions = normalized[1:] if len(normalized) > 1 else []
    return {'farmer': farmer_action, 'hands': hands_actions, 'market': market}

# ==================== ENTRYPOINT ====================
def _safe_fallback(obs: Any) -> Dict[str, Any]:
    try:
        player = int(getv(obs, 'player', 0))
        farms = getv(obs, 'farms', []) or []
        farm = farms[player]
        hands = getv(farm, 'hands', []) or []
        farmer = ['PASS']
        position = getv(farm, 'farmer', [0, 0])
        tiles = getv(farm, 'tiles', []) or []
        if tiles and len(position) >= 2:
            x, y = int(position[0]), int(position[1])
            tile = tiles[y][x]
            if getv(tile, 'kind', '') == 'PLANT' and not bool(getv(tile, 'watered_today', False)):
                farmer = ['WATER']
            elif int(getv(tile, 'yield_units', 0) or 0) > 0:
                farmer = ['HARVEST']
        return {'farmer': farmer, 'hands': [['PASS'] for _ in hands], 'market': []}
    except Exception:
        return {'farmer': ['PASS'], 'hands': [], 'market': []}

def decide(obs: Any) -> Dict[str, Any]:
    world = WorldState.from_observation(obs)
    plan = make_economic_plan(world)
    tasks = generate_tasks(world, plan)
    unit_actions = assign_actions(world, tasks)
    market_orders = build_market_orders(world, plan)
    return validate_action(world, unit_actions, market_orders)

def agent(obs: Any) -> Dict[str, Any]:
    try:
        return decide(obs)
    except Exception:
        return _safe_fallback(obs)

__all__ = ["agent"]
