from enum import Enum
from config import *

class Direction(Enum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3
    def to_vector(self):
        vectors = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        return vectors[self.value]

class ItemType(Enum):
    IRON_ORE = 1
    COPPER_ORE = 2
    COAL_ORE = 3
    WOOD = 4
    IRON_INGOT = 10
    COPPER_INGOT = 11
    IRON_GEAR = 20
    COPPER_WIRE = 21
    CIRCUIT = 22
    SCIENCE_PACK_1 = 90
    
    CONVEYOR = 100
    MINER = 101
    SMELTER = 102
    BOX = 103
    SELL_NODE = 104
    SPLITTER = 105
    ASSEMBLER = 106
    LAB = 107
    
    FAST_CONVEYOR = 200
    HEAVY_MINER = 201

    # 디미고 아이템 추가
    DIMIGO_TICKET = 1000
    DIMIGO_PRESIDENT = 1001
    DIMIGO_TEACHER = 1002
    DIMIGO_PRINCIPAL = 1003
    DIMIGO_CHAIRMAN = 1004

ITEM_DATA = {
    ItemType.IRON_ORE: {"name": "철광석", "color": COLOR_IRON_ORE, "value": 2, "fuel_value": 0, "desc": "기본 광석", "tile_image": "iron_ore_patch.png"},
    ItemType.COPPER_ORE: {"name": "구리광석", "color": COLOR_COPPER_ORE, "value": 2, "fuel_value": 0, "desc": "전도성 광석", "tile_image": "copper_ore_patch.png"},
    ItemType.COAL_ORE: {"name": "석탄", "color": (10, 10, 10), "value": 5, "fuel_value": 300, "desc": "연료 (10초)", "tile_image": "coal_ore_patch.png"},
    ItemType.WOOD: {"name": "통나무", "color": COLOR_WOOD, "value": 1, "fuel_value": 60, "desc": "연료 (2초)", "tile_image": "wood_patch.png"},
    
    ItemType.IRON_INGOT: {"name": "철 주괴", "color": (200, 200, 200), "value": 15, "fuel_value": 0, "desc": "철 가공품"},
    ItemType.COPPER_INGOT: {"name": "구리 주괴", "color": (205, 127, 50), "value": 15, "fuel_value": 0, "desc": "구리 가공품"},
    ItemType.IRON_GEAR: {"name": "철 톱니바퀴", "color": (150, 150, 170), "value": 35, "fuel_value": 0, "desc": "기계 부품"},
    ItemType.COPPER_WIRE: {"name": "구리 전선", "color": (255, 150, 100), "value": 20, "fuel_value": 0, "desc": "전기 부품"},
    ItemType.CIRCUIT: {"name": "전자 회로", "color": (50, 200, 50), "value": 100, "fuel_value": 0, "desc": "고급 부품"},
    ItemType.SCIENCE_PACK_1: {"name": "자동화 팩", "color": (255, 50, 50), "value": 200, "fuel_value": 0, "desc": "연구소에 넣어 기술을 잠금 해제하세요."},

    ItemType.CONVEYOR: {"name": "컨베이어", "color": (100, 100, 255), "cost": 5, "is_building": True, "desc": "속도: 1x"},
    ItemType.MINER: {"name": "채굴기", "color": (150, 150, 150), "cost": 100, "is_building": True, "desc": "속도: 1.0/s, 범위: 1x1"},
    ItemType.SMELTER: {"name": "용해로", "color": (80, 80, 80), "cost": 200, "is_building": True, "desc": "광석을 제련합니다."},
    ItemType.BOX: {"name": "보관함", "color": (139, 105, 20), "cost": 50, "is_building": True, "desc": "아이템 보관"},
    ItemType.SELL_NODE: {"name": "판매기", "color": (255, 215, 0), "cost": 500, "is_building": True, "desc": "자원 판매"},
    ItemType.SPLITTER: {"name": "분배기", "color": (100, 200, 255), "cost": 150, "is_building": True, "desc": "물류 분배"},
    ItemType.ASSEMBLER: {"name": "제작기", "color": (100, 150, 100), "cost": 500, "is_building": True, "desc": "부품 조립"},
    ItemType.LAB: {"name": "연구소", "color": (50, 50, 200), "cost": 1000, "is_building": True, "desc": "자동화 팩을 소모해 기술을 연구합니다."},

    ItemType.FAST_CONVEYOR: {"name": "고속 컨베이어", "color": (255, 50, 255), "cost": 20, "is_building": True, "desc": "속도: 2x (매우 빠름)"},
    ItemType.HEAVY_MINER: {"name": "산업용 채굴기", "color": (200, 50, 50), "cost": 500, "is_building": True, "desc": "속도: 2.5/s, 범위: 3x3"},
    
    # 디미고 아이템 데이터 추가 (is_upgrade 플래그와 passive_income 추가)
    ItemType.DIMIGO_TICKET: {"name": "디미고 입학권", "color": (255, 100, 100), "cost": 500, "is_upgrade": True, "desc": "디미고에 발을 들입니다. [초당 +1 Cr]", "passive_income": 1},
    ItemType.DIMIGO_PRESIDENT: {"name": "디미고 학생회장", "color": (100, 100, 255), "cost": 10000, "is_upgrade": True, "desc": "학생들의 정점. [초당 +20 Cr]", "passive_income": 20},
    ItemType.DIMIGO_TEACHER: {"name": "디미고 교사", "color": (100, 255, 100), "cost": 200000, "is_upgrade": True, "desc": "학생들을 가르칩니다. [초당 +500 Cr]", "passive_income": 500},
    ItemType.DIMIGO_PRINCIPAL: {"name": "디미고 교장", "color": (255, 215, 0), "cost": 1000000, "is_upgrade": True, "desc": "학교의 1짱. [초당 +3000 Cr]", "passive_income": 3000},
    ItemType.DIMIGO_CHAIRMAN: {"name": "디미고 이사장", "color": (200, 0, 255), "cost": 10000000, "is_upgrade": True, "desc": "진정한 학교의 주인. [초당 +20000 Cr]", "passive_income": 20000},
}

class BuildingType(Enum):
    CONVEYOR = 1
    MINER = 2
    SMELTER = 3
    BOX = 4
    SELL_NODE = 5
    SPLITTER = 6
    ASSEMBLER = 7
    LAB = 8
    FAST_CONVEYOR = 9
    HEAVY_MINER = 10

ITEM_TO_BUILDING = {
    ItemType.CONVEYOR: BuildingType.CONVEYOR,
    ItemType.MINER: BuildingType.MINER,
    ItemType.SMELTER: BuildingType.SMELTER,
    ItemType.BOX: BuildingType.BOX,
    ItemType.SELL_NODE: BuildingType.SELL_NODE,
    ItemType.SPLITTER: BuildingType.SPLITTER,
    ItemType.ASSEMBLER: BuildingType.ASSEMBLER,
    ItemType.LAB: BuildingType.LAB,
    ItemType.FAST_CONVEYOR: BuildingType.FAST_CONVEYOR,
    ItemType.HEAVY_MINER: BuildingType.HEAVY_MINER,
}
BUILDING_TO_ITEM = {v: k for k, v in ITEM_TO_BUILDING.items()}

BUILDING_DATA = {
    BuildingType.CONVEYOR: {"name": "컨베이어", "size": (1, 1), "has_dir": True, "image": "building_conveyor.png", "speed": 0.1},
    BuildingType.FAST_CONVEYOR: {"name": "고속 컨베이어", "size": (1, 1), "has_dir": True, "image": "building_fast_conveyor.png", "speed": 0.25},
    
    BuildingType.MINER: {"name": "채굴기", "size": (1, 1), "has_dir": True, "image": "building_miner.png", "rate": 60, "radius": 0},
    BuildingType.HEAVY_MINER: {"name": "산업용 채굴기", "size": (1, 1), "has_dir": True, "image": "building_heavy_miner.png", "rate": 24, "radius": 1},
    
    BuildingType.SMELTER: {"name": "용해로", "size": (1, 1), "has_dir": True, "image": "building_smelter.png", "image_active": "building_smelter_active.png"},
    BuildingType.BOX: {"name": "보관함", "size": (1, 1), "has_dir": False, "image": "building_box.png"},
    BuildingType.SELL_NODE: {"name": "판매기", "size": (1, 1), "has_dir": False, "image": "building_sell_node.png"},
    BuildingType.SPLITTER: {"name": "분배기", "size": (1, 1), "has_dir": True, "image": "building_splitter.png"},
    BuildingType.ASSEMBLER: {"name": "제작기", "size": (2, 2), "has_dir": True, "image": "building_assembler.png", "image_active": "building_assembler_active.png"},
    BuildingType.LAB: {"name": "연구소", "size": (2, 2), "has_dir": False, "image": "building_lab.png", "image_active": "building_lab_active.png"},
}

SHOP_ITEMS = [
    ItemType.CONVEYOR, ItemType.MINER, ItemType.SMELTER, 
    ItemType.SPLITTER, ItemType.ASSEMBLER, ItemType.BOX, 
    ItemType.SELL_NODE, ItemType.LAB,
    ItemType.FAST_CONVEYOR, ItemType.HEAVY_MINER,
    # 디미고 아이템 상점 목록에 추가
    ItemType.DIMIGO_TICKET, ItemType.DIMIGO_PRESIDENT,
    ItemType.DIMIGO_TEACHER, ItemType.DIMIGO_PRINCIPAL,
    ItemType.DIMIGO_CHAIRMAN
]

SMELTER_RECIPES = {
    ItemType.IRON_ORE: {"output": ItemType.IRON_INGOT, "time": 60},
    ItemType.COPPER_ORE: {"output": ItemType.COPPER_INGOT, "time": 60},
}

ASSEMBLER_RECIPES = {
    ItemType.IRON_GEAR: {"inputs": {ItemType.IRON_INGOT: 2}, "time": 30, "name": "철 톱니바퀴"},
    ItemType.COPPER_WIRE: {"inputs": {ItemType.COPPER_INGOT: 1}, "time": 30, "name": "구리 전선"},
    ItemType.CIRCUIT: {"inputs": {ItemType.IRON_INGOT: 1, ItemType.COPPER_WIRE: 3}, "time": 90, "name": "전자 회로"},
    ItemType.SCIENCE_PACK_1: {"inputs": {ItemType.IRON_GEAR: 1, ItemType.COPPER_INGOT: 1}, "time": 150, "name": "자동화 팩"},
}

TECH_DATA = {
    "logistics": {
        "name": "고속 물류",
        "desc": "2배 빠른 컨베이어 벨트를 해금합니다.",
        "cost": 10, 
        "unlocks": [ItemType.FAST_CONVEYOR],
        "req": None
    },
    "mining": {
        "name": "산업용 채굴",
        "desc": "3x3 범위를 채굴하는 고속 드릴을 해금합니다.",
        "cost": 20,
        "unlocks": [ItemType.HEAVY_MINER],
        "req": "logistics"
    }
}

class MissionType(Enum):
    START_UP = 1
    EXPAND_1 = 2
    AUTOMATION_1 = 3
    EXPAND_2 = 4
    CIRCUITS = 5

MISSION_DATA = {
    MissionType.START_UP: {
        "name": "첫걸음 (튜토리얼)",
        "desc": "기본 자원을 확보하여 공장 건설을 준비합니다.",
        "requirements": { ItemType.WOOD: 10, ItemType.IRON_ORE: 5, ItemType.COAL_ORE: 5 },
        "rewards": { "money": 1000 },
        "unlocks": [MissionType.EXPAND_1, MissionType.AUTOMATION_1]
    },
    MissionType.EXPAND_1: {
        "name": "영토 확장 (1)",
        "desc": "영토를 확장하여 더 많은 공간을 확보합니다.",
        "requirements": { ItemType.WOOD: 50 },
        "rewards": { "expand": 3 },
        "unlocks": [MissionType.EXPAND_2]
    },
    MissionType.AUTOMATION_1: {
        "name": "철 자동화",
        "desc": "철 주괴 생산을 자동화하여 부품 생산을 준비합니다.",
        "requirements": { ItemType.IRON_INGOT: 50, ItemType.IRON_GEAR: 20 },
        "rewards": { "money": 5000 },
        "unlocks": [MissionType.CIRCUITS]
    },
    MissionType.EXPAND_2: {
        "name": "영토 확장 (2)",
        "desc": "더 복잡한 공장을 위해 영토를 추가로 확장합니다.",
        "requirements": { ItemType.IRON_GEAR: 50, ItemType.COPPER_INGOT: 50 },
        "rewards": { "expand": 3 },
        "unlocks": []
    },
    MissionType.CIRCUITS: {
        "name": "전자 공학",
        "desc": "구리 가공 및 전자 회로 생산을 시작합니다.",
        "requirements": { ItemType.COPPER_WIRE: 100, ItemType.CIRCUIT: 50 },
        "rewards": { "money": 10000 },
        "unlocks": []
    },
}