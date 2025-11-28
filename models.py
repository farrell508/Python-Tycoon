import random
import pygame
from config import *
from gamedata import *

class ItemStack:
    def __init__(self, item_type, count=1):
        self.item_type = item_type
        self.count = count
        self.max_stack = 64

class Inventory:
    def __init__(self, size):
        self.slots = [None] * size

    # [수정 1] 핫바 우선순위 적용된 add_item
    def add_item(self, item_type, count=1):
        # 플레이어 인벤토리(크기 36)인지 확인
        is_player_inv = len(self.slots) == 36

        if is_player_inv:
            # --- 플레이어 인벤토리 우선순위 로직 ---
            hotbar_indices = range(27, 36)
            main_inv_indices = range(0, 27)

            # 1. 핫바에 기존 스택이 있는지 확인
            for i in hotbar_indices:
                stack = self.slots[i]
                if stack and stack.item_type == item_type and stack.count < stack.max_stack:
                    needed = stack.max_stack - stack.count
                    added = min(needed, count)
                    stack.count += added
                    count -= added
                    if count <= 0: return True
            
            # 2. 메인 인벤토리에 기존 스택이 있는지 확인
            for i in main_inv_indices:
                stack = self.slots[i]
                if stack and stack.item_type == item_type and stack.count < stack.max_stack:
                    needed = stack.max_stack - stack.count
                    added = min(needed, count)
                    stack.count += added
                    count -= added
                    if count <= 0: return True

            # 3. 핫바에 빈 슬롯이 있는지 확인
            for i in hotbar_indices:
                if not self.slots[i]:
                    self.slots[i] = ItemStack(item_type, count)
                    return True # 남은 아이템 전부를 새 슬롯에 추가

            # 4. 메인 인벤토리에 빈 슬롯이 있는지 확인
            for i in main_inv_indices:
                if not self.slots[i]:
                    self.slots[i] = ItemStack(item_type, count)
                    return True # 남은 아이템 전부를 새 슬롯에 추가
        
        else:
            # --- 기존 로직 (상자, 기계 등) ---
            for stack in self.slots:
                if stack and stack.item_type == item_type and stack.count < stack.max_stack:
                    needed = stack.max_stack - stack.count
                    added = min(needed, count)
                    stack.count += added
                    count -= added
                    if count <= 0: return True
            for i, stack in enumerate(self.slots):
                if not stack:
                    self.slots[i] = ItemStack(item_type, count)
                    return True
        
        return False # 공간 없음

    def add_stack(self, other_stack, slot_range=None):
        if slot_range is None: slot_range = range(len(self.slots))
        for i in slot_range:
            if i >= len(self.slots): break
            stack = self.slots[i]
            if stack and stack.item_type == other_stack.item_type and stack.count < stack.max_stack:
                needed = stack.max_stack - stack.count
                to_add = min(needed, other_stack.count)
                stack.count += to_add
                other_stack.count -= to_add
                if other_stack.count <= 0: return True
        for i in slot_range:
            if i >= len(self.slots): break
            if not self.slots[i]:
                self.slots[i] = ItemStack(other_stack.item_type, other_stack.count)
                other_stack.count = 0
                return True
        return False

    def add_item_to_slot(self, slot_idx, item_type, count=1):
        if 0 <= slot_idx < len(self.slots):
            stack = self.slots[slot_idx]
            if not stack:
                self.slots[slot_idx] = ItemStack(item_type, count)
                return True
            elif stack.item_type == item_type and stack.count + count <= stack.max_stack:
                stack.count += count
                return True
        return False

    def has_items(self, req_dict):
        for req_type, req_count in req_dict.items():
            if self.count_items(req_type) < req_count: return False
        return True

    def remove_items(self, req_dict):
        if not self.has_items(req_dict): return False
        for req_type, req_count in req_dict.items():
            self.remove_item(req_type, req_count)
        return True

    def remove_item(self, item_type, count=1):
        total = self.count_items(item_type)
        if total < count: return False
        removed = 0
        for i, stack in enumerate(self.slots):
            if stack and stack.item_type == item_type:
                take = min(count - removed, stack.count)
                stack.count -= take
                removed += take
                if stack.count <= 0: self.slots[i] = None
                if removed >= count: return True
        return False

    def remove_from_slot(self, slot_idx, count=1):
        if 0 <= slot_idx < len(self.slots) and self.slots[slot_idx]:
            stack = self.slots[slot_idx]
            if stack.count >= count:
                stack.count -= count
                if stack.count <= 0: self.slots[slot_idx] = None
                return True
        return False

    def count_items(self, item_type):
        return sum(s.count for s in self.slots if s and s.item_type == item_type)

class ItemEntity:
    def __init__(self, item_type, x, y):
        self.type = item_type
        self.x, self.y = x, y
        self.target_x, self.target_y = x, y
        self.progress = 0.0
        self.render_offset_x = random.uniform(-5, 5)
        self.render_offset_y = random.uniform(-5, 5)

    def update(self, speed):
        if self.x != self.target_x or self.y != self.target_y:
            self.progress += speed
            if self.progress >= 1.0:
                self.progress = 0.0
                self.x, self.y = self.target_x, self.target_y
            return True
        return False

    def get_render_pos(self):
        rx = self.x + (self.target_x - self.x) * self.progress
        ry = self.y + (self.target_y - self.y) * self.progress
        return rx * TILE_SIZE + TILE_SIZE // 2 + self.render_offset_x, \
               ry * TILE_SIZE + TILE_SIZE // 2 + self.render_offset_y

class Building:
    def __init__(self, b_type, gx, gy, direction=Direction.DOWN):
        self.type = b_type
        self.gx, self.gy = gx, gy
        self.direction = direction
        self.data = BUILDING_DATA[b_type]
        self.width, self.height = self.data["size"]
        self.timer = 0
        
        if self.type == BuildingType.BOX:
            self.inv = Inventory(27)
        elif self.type == BuildingType.SMELTER:
            self.inv = Inventory(3)
            self.fuel_left, self.max_fuel_time, self.progress = 0, 1, 0
        elif self.type == BuildingType.SPLITTER:
            self.out_index = 0
        elif self.type == BuildingType.ASSEMBLER:
            self.inv = Inventory(5)
            self.recipe = None
            self.progress = 0
        elif self.type == BuildingType.LAB:
            self.inv = Inventory(1) 
            self.progress = 0 
            self.active = False

    def get_rect(self):
        return pygame.Rect(self.gx * TILE_SIZE, self.gy * TILE_SIZE, self.width * TILE_SIZE, self.height * TILE_SIZE)

    def get_info_text(self):
        info = [f"[ {self.data['name']} ]"]
        if self.type in [BuildingType.MINER, BuildingType.HEAVY_MINER]:
             info.append(f"작업: {int(self.timer/self.data['rate']*100)}%")
        elif self.type == BuildingType.SMELTER:
            status = "대기 중"
            if self.fuel_left > 0: status = f"작업 중 ({int(self.progress/60*100)}%)" if self.progress>0 else "연소 중"
            info.append(f"상태: {status}")
        elif self.type == BuildingType.ASSEMBLER:
            if self.recipe:
                r_data = ASSEMBLER_RECIPES[self.recipe]
                info.append(f"레시피: {r_data['name']}")
                info.append(f"진행도: {int(self.progress/r_data['time']*100)}%")
            else: info.append("레시피 미설정")
        elif self.type == BuildingType.BOX:
            info.append(f"저장: {sum(1 for s in self.inv.slots if s)} / 27")
        elif self.type == BuildingType.LAB:
            info.append(f"자동화 팩: {self.inv.slots[0].count if self.inv.slots[0] else 0}")
            info.append("연구 진행 중..." if self.active else "대기 중")
        return info

    def tick(self, world):
        if self.type in [BuildingType.MINER, BuildingType.HEAVY_MINER]: self._tick_miner(world)
        elif self.type == BuildingType.SMELTER: self._tick_smelter(world)
        elif self.type == BuildingType.ASSEMBLER: self._tick_assembler(world)
        elif self.type == BuildingType.LAB: self._tick_lab(world)

    def _tick_miner(self, world):
        radius = self.data.get("radius", 0)
        found_res = None
        for dy in range(-radius, radius+1):
            for dx in range(-radius, radius+1):
                res = world.get_tile_resource(self.gx + dx, self.gy + dy)
                if res: 
                    found_res = res
                    break
            if found_res: break

        if found_res:
            self.timer += 1
            if self.timer >= self.data["rate"]:
                self.timer = 0
                dx, dy = self.direction.to_vector()
                tx, ty = self.gx + dx, self.gy + dy
                if not (world.min_x <= tx < world.max_x and world.min_y <= ty < world.max_y): return
                world.add_item(ItemEntity(found_res, tx, ty))

    def _tick_smelter(self, world):
        inv = self.inv.slots
        in_s, fuel_s, out_s = inv[0], inv[1], inv[2]
        if self.fuel_left <= 0 and fuel_s and ITEM_DATA[fuel_s.item_type]["fuel_value"] > 0:
            if in_s and in_s.item_type in SMELTER_RECIPES:
                r = SMELTER_RECIPES[in_s.item_type]
                if not out_s or (out_s.item_type == r["output"] and out_s.count < out_s.max_stack):
                    self.max_fuel_time = ITEM_DATA[fuel_s.item_type]["fuel_value"]
                    self.fuel_left = self.max_fuel_time
                    fuel_s.count -= 1
                    if fuel_s.count <= 0: inv[1] = None

        if self.fuel_left > 0:
            self.fuel_left -= 1
            if in_s and in_s.item_type in SMELTER_RECIPES:
                self.progress += 1
                r = SMELTER_RECIPES[in_s.item_type]
                if self.progress >= r["time"]:
                    self.progress = 0
                    res = r["output"]
                    if not out_s: inv[2] = ItemStack(res, 1)
                    else: out_s.count += 1
                    in_s.count -= 1
                    if in_s.count <= 0: inv[0] = None
            else: self.progress = 0
        else: self.progress = 0
        if inv[2]: self._try_output(world, inv[2], 2)

    def _tick_assembler(self, world):
        if not self.recipe: return
        r_data = ASSEMBLER_RECIPES[self.recipe]
        out_s = self.inv.slots[4]
        if out_s and (out_s.item_type != self.recipe or out_s.count >= out_s.max_stack):
            self.progress = 0
            return
        if self.inv.has_items(r_data["inputs"]):
            self.progress += 1
            if self.progress >= r_data["time"]:
                self.progress = 0
                self.inv.remove_items(r_data["inputs"])
                if not out_s: self.inv.slots[4] = ItemStack(self.recipe, 1)
                else: out_s.count += 1
        else: self.progress = 0
        if self.inv.slots[4]: self._try_output(world, self.inv.slots[4], 4)

    def _tick_lab(self, world):
        self.active = False
        if world.current_research is None: return 

        tech_id = world.current_research
        tech = TECH_DATA[tech_id]
        
        if world.research_progress >= tech["cost"]:
            world.complete_research()
            return

        pack_slot = self.inv.slots[0]
        if pack_slot and pack_slot.item_type == ItemType.SCIENCE_PACK_1:
            self.active = True
            self.progress += 1
            if self.progress >= 60:
                self.progress = 0
                pack_slot.count -= 1
                if pack_slot.count <= 0: self.inv.slots[0] = None
                world.research_progress += 1

    def _try_output(self, world, output_stack, slot_idx):
        ox, oy = self.gx, self.gy
        if self.width == 2:
             if self.direction == Direction.UP: ox += 0; oy -= 1
             elif self.direction == Direction.DOWN: ox += 1; oy += 2
             elif self.direction == Direction.LEFT: ox -= 1; oy += 1
             elif self.direction == Direction.RIGHT: ox += 2; oy += 0
        else:
            dx, dy = self.direction.to_vector()
            ox += dx; oy += dy
        
        # [수정 2] self.max_y -> world.max_y 로 오타 수정
        if not (world.min_x <= ox < world.max_x and world.min_y <= oy < world.max_y): return

        if world.add_item(ItemEntity(output_stack.item_type, ox, oy)):
            output_stack.count -= 1
            if output_stack.count <= 0: self.inv.slots[slot_idx] = None

class World:
    def __init__(self):
        self.max_width, self.max_height = GRID_WIDTH, GRID_HEIGHT
        
        start_size = 9
        self.min_x = (self.max_width - start_size) // 2 
        self.min_y = (self.max_height - start_size) // 2
        self.max_x = self.min_x + start_size             
        self.max_y = self.min_y + start_size             
        
        self.tiles = [[None for _ in range(self.max_width)] for _ in range(self.max_height)]
        self.buildings = {}
        self.items = []
        self.money = 1000
        self.player_inv = Inventory(36)
        
        self.player_inv.add_item(ItemType.MINER, 1)
        self.player_inv.add_item(ItemType.CONVEYOR, 10)
        
        self.missions = {}
        self.available_missions = [MissionType.START_UP]
        self.mission_alert = False

        self.unlocked_techs = set()
        self.current_research = None 
        self.research_progress = 0   

        # 구매한 업그레이드 및 패시브 인컴 추가
        self.purchased_upgrades = set() 
        self.passive_income_per_sec = 0 

        self.generate_map()

    def generate_map(self):
        start_box = (self.min_x, self.min_y, self.max_x, self.max_y)
        self._spawn_exact_patch(ItemType.IRON_ORE, *start_box)
        self._spawn_exact_patch(ItemType.IRON_ORE, *start_box)
        self._spawn_exact_patch(ItemType.IRON_ORE, *start_box)
        self._spawn_exact_patch(ItemType.COPPER_ORE, *start_box)
        self._spawn_exact_patch(ItemType.COPPER_ORE, *start_box)
        self._spawn_exact_patch(ItemType.COPPER_ORE, *start_box)
        self._spawn_exact_patch(ItemType.COAL_ORE, *start_box)
        self._spawn_exact_patch(ItemType.WOOD, *start_box)
        self._spawn_exact_patch(ItemType.WOOD, *start_box)
        self._spawn_exact_patch(ItemType.WOOD, *start_box)

        for _ in range(6): self._spawn_cluster(ItemType.IRON_ORE, 0.7, exclude_box=start_box)
        for _ in range(4): self._spawn_cluster(ItemType.COPPER_ORE, 0.6, exclude_box=start_box)
        for _ in range(5): self._spawn_cluster(ItemType.COAL_ORE, 0.65, exclude_box=start_box)
        for _ in range(8): self._spawn_cluster(ItemType.WOOD, 0.8, exclude_box=start_box)

    def _spawn_exact_patch(self, item_type, min_x, min_y, max_x, max_y):
        available_spots = []
        for y in range(min_y, max_y):
            for x in range(min_x, max_x):
                if 0 <= x < self.max_width and 0 <= y < self.max_height:
                    if self.tiles[y][x] is None:
                        available_spots.append((x, y))
        if not available_spots: return False
        x, y = random.choice(available_spots)
        self.tiles[y][x] = item_type
        return True

    def _spawn_cluster(self, item_type, chance, min_x=0, min_y=0, max_x=None, max_y=None, exclude_box=None):
        if max_x is None: max_x = self.max_width
        if max_y is None: max_y = self.max_height
        padding = 3
        cx_min, cx_max = 0 + padding, self.max_width - padding - 1
        cy_min, cy_max = 0 + padding, self.max_height - padding - 1
        cx, cy = random.randint(cx_min, cx_max), random.randint(cy_min, cy_max)

        for y in range(cy-3, cy+3):
            for x in range(cx-3, cx+3):
                if min_x <= x < max_x and min_y <= y < max_y:
                    if exclude_box:
                        ex_min_x, ex_min_y, ex_max_x, ex_max_y = exclude_box
                        if (ex_min_x <= x < ex_max_x and ex_min_y <= y < ex_max_y): continue     
                    if 0 <= x < self.max_width and 0 <= y < self.max_height:
                        if self.tiles[y][x] is None and random.random() > (1.0 - chance): 
                                self.tiles[y][x] = item_type

    def get_tile_resource(self, x, y):
        if 0 <= x < self.max_width and 0 <= y < self.max_height: return self.tiles[y][x]
        return None

    def can_place_building(self, gx, gy, width, height):
        for y in range(gy, gy + height):
            for x in range(gx, gx + width):
                if not (self.min_x <= x < self.max_x and self.min_y <= y < self.max_y): return False
                if (x, y) in self.buildings: return False
        return True

    def place_building(self, building):
        for y in range(building.gy, building.gy + building.height):
            for x in range(building.gx, building.gx + building.width):
                self.buildings[(x, y)] = building

    def remove_building(self, gx, gy):
        b = self.buildings.get((gx, gy))
        if b:
            if not (self.min_x <= gx < self.max_x and self.min_y <= gy < self.max_y): return False
            for y in range(b.gy, b.gy + b.height):
                for x in range(b.gx, b.gx + b.width):
                     if (x,y) in self.buildings: del self.buildings[(x,y)]
            self.player_inv.add_item(BUILDING_TO_ITEM[b.type], 1)
            if hasattr(b, 'inv'):
                for stack in b.inv.slots:
                    if stack: self.player_inv.add_item(stack.item_type, stack.count)
            return True
        return False

    def get_building_at(self, x, y): return self.buildings.get((x, y))
    
    def add_item(self, item_entity):
        if len(self.items) >= MAX_ITEMS: return False
        self.items.append(item_entity)
        return True

    def start_research(self, tech_id):
        if tech_id not in self.unlocked_techs and tech_id != self.current_research:
            self.current_research = tech_id
            self.research_progress = 0

    def complete_research(self):
        if self.current_research:
            self.unlocked_techs.add(self.current_research)
            tech = TECH_DATA[self.current_research]
            print(f"연구 완료: {tech['name']}")
            self.current_research = None
            self.research_progress = 0

    # 업그레이드 구매 메서드 추가
    def buy_upgrade(self, item_type):
        if item_type in self.purchased_upgrades:
            return False # 이미 구매함
        
        data = ITEM_DATA.get(item_type)
        if not data or not data.get("is_upgrade"):
            return False # 업그레이드 아이템이 아님
        
        cost = data.get("cost", 0)
        if self.money >= cost:
            self.money -= cost
            self.purchased_upgrades.add(item_type)
            self.passive_income_per_sec += data.get("passive_income", 0)
            print(f"업그레이드 구매: {data['name']}. 현재 초당 수입: {self.passive_income_per_sec}/sec")
            return True
        return False

    def tick(self):
        self.update_mission_status()

        # 패시브 인컴 적용
        if self.passive_income_per_sec > 0:
            self.money += self.passive_income_per_sec / LOGIC_TICK_RATE

        for b in set(self.buildings.values()): b.tick(self)
        items_to_remove = []
        for item in self.items:
            if item.progress > 0: continue
            ix, iy = int(item.x), int(item.y)
            b = self.get_building_at(ix, iy)
            
            speed_mult = 0.1
            
            if b:
                if b.type in [BuildingType.CONVEYOR, BuildingType.FAST_CONVEYOR]:
                    speed_mult = b.data.get("speed", 0.1)
                    dx, dy = b.direction.to_vector()
                    target_x, target_y = ix + dx, iy + dy
                
                elif b.type == BuildingType.SPLITTER:
                    dirs = [Direction((b.direction.value - 1) % 4), Direction((b.direction.value + 1) % 4)]
                    dx, dy = dirs[b.out_index].to_vector()
                    target_x, target_y = ix + dx, iy + dy
                    b.out_index = (b.out_index + 1) % 2
                else:
                    target_x, target_y = ix, iy

                if not (self.min_x <= target_x < self.max_x and self.min_y <= target_y < self.max_y):
                     item.target_x, item.target_y = ix, iy
                else:
                    item.target_x, item.target_y = target_x, target_y

                if b.type == BuildingType.SELL_NODE:
                    self.money += ITEM_DATA[item.type].get("value", 0)
                    items_to_remove.append(item)
                elif b.type == BuildingType.BOX:
                     if b.inv.add_item(item.type, 1): items_to_remove.append(item)
                elif b.type == BuildingType.SMELTER:
                    is_fuel = ITEM_DATA[item.type].get("fuel_value", 0) > 0
                    target = 1 if is_fuel else 0
                    if b.inv.add_item_to_slot(target, item.type, 1): items_to_remove.append(item)
                elif b.type == BuildingType.ASSEMBLER:
                    if b.recipe and item.type in ASSEMBLER_RECIPES[b.recipe]["inputs"]:
                         for i in range(4):
                             if b.inv.add_item_to_slot(i, item.type, 1):
                                 items_to_remove.append(item)
                                 break
                elif b.type == BuildingType.LAB:
                    if item.type == ItemType.SCIENCE_PACK_1:
                         if b.inv.add_item_to_slot(0, item.type, 1):
                            items_to_remove.append(item)

            item.update(speed_mult)

        for item in items_to_remove:
            if item in self.items: self.items.remove(item)
        for item in self.items: item.update(0.1)

    def update_mission_status(self):
        alert = False
        for mission_id in self.available_missions:
            if self.missions.get(mission_id) in ["completed", "ready"]:
                if self.missions.get(mission_id) == "ready": alert = True 
                continue

            reqs = MISSION_DATA[mission_id]["requirements"]
            if self.player_inv.has_items(reqs):
                self.missions[mission_id] = "ready"
                alert = True
        self.mission_alert = alert

    def complete_mission(self, mission_id):
        if self.missions.get(mission_id) != "ready": return False
        data = MISSION_DATA[mission_id]
        reqs = data["requirements"]

        if not self.player_inv.remove_items(reqs): return False

        rewards = data["rewards"]
        if "money" in rewards: self.money += rewards["money"]
        if "expand" in rewards:
            expand_by = rewards["expand"]
            self.min_x = max(0, self.min_x - expand_by // 2)
            self.min_y = max(0, self.min_y - expand_by // 2)
            self.max_x = min(self.max_width, self.max_x + (expand_by - expand_by // 2))
            self.max_y = min(self.max_height, self.max_y + (expand_by - expand_by // 2))

        self.missions[mission_id] = "completed"
        if mission_id in self.available_missions: self.available_missions.remove(mission_id)

        if "unlocks" in data:
            for next_mission_id in data["unlocks"]:
                if next_mission_id not in self.missions:
                    self.available_missions.append(next_mission_id)
                    self.missions[next_mission_id] = "pending"
        
        self.update_mission_status()
        return True