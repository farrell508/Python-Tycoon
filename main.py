import pygame
import sys
import math
from enum import Enum, auto
from config import *
from gamedata import *
from models import *
import os

import sys, os
def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class GameState(Enum):
    PLAY = auto()
    SHOP = auto()
    CONTAINER = auto()
    MISSIONS = auto()
    TECH_TREE = auto()

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Factory Tycoon v2.1: Minecraft Style Controls")
        self.clock = pygame.time.Clock()
        fonts = ["malgungothic", "applesdgothicneo", "arialunicode", "arial"]
        self.font = None
        for f in fonts:
            try:
                self.font = pygame.font.SysFont(f, 16)
                self.font_small = pygame.font.SysFont(f, 12)
                self.font_big = pygame.font.SysFont(f, 24)
                break
            except: continue
        if not self.font: self.font = pygame.font.Font(None, 20)

        self.item_images = {}       
        self.tile_images = {}       
        self.building_images = {}   
        self.asset_folder = "assets"
        self.grass_tile = None      
        self.load_assets()

        self.world = World()
        center_world_x = (self.world.min_x + self.world.max_x) // 2 * TILE_SIZE
        center_world_y = (self.world.min_y + self.world.max_y) // 2 * TILE_SIZE
        self.camera_x = center_world_x - SCREEN_WIDTH // 2
        self.camera_y = center_world_y - SCREEN_HEIGHT // 2
        
        self.logic_timer = 0
        self.state = GameState.PLAY
        self.build_rot = Direction.RIGHT
        self.selected_hotbar_idx = 0
        self.delete_mode = False
        
        self.opened_container = None
        self.held_item = None
        self.inspected_info = None

        self.shop_buy_scroll = 0
        self.shop_sell_scroll = 0
        self.mission_scroll = 0

    def _load_scaled_image(self, file_name, size):
        file_path = resource_path(os.path.join(self.asset_folder, file_name))
        try:
            image = pygame.image.load(file_path).convert_alpha()
            if size: image = pygame.transform.scale(image, size)
            return image
        except Exception: return None

    def load_assets(self):
        print("--- 에셋 로드 ---")
        self.grass_tile = self._load_scaled_image("grass_tile.png", (TILE_SIZE, TILE_SIZE))
        
        icon_size = (32, 32)
        name_map = {
            ItemType.SCIENCE_PACK_1: "science_pack_1.png",
            ItemType.LAB: "lab.png",
            ItemType.FAST_CONVEYOR: "fast_conveyor.png",
            ItemType.HEAVY_MINER: "heavy_miner.png"
        }
        for item_type in ItemType:
            fname = name_map.get(item_type, f"{item_type.name.lower()}.png")
            img = self._load_scaled_image(fname, icon_size)
            if img: self.item_images[item_type] = img

        for item_type, data in ITEM_DATA.items():
            if "tile_image" in data:
                img = self._load_scaled_image(data["tile_image"], (TILE_SIZE, TILE_SIZE))
                if img: self.tile_images[item_type] = img

        for b_type, data in BUILDING_DATA.items():
            size_x = data["size"][0] * TILE_SIZE
            size_y = data["size"][1] * TILE_SIZE
            if "image" in data:
                img = self._load_scaled_image(data["image"], (size_x, size_y))
                if img: 
                    if b_type not in self.building_images: self.building_images[b_type] = {}
                    self.building_images[b_type]['default'] = img
            if "image_active" in data:
                img_active = self._load_scaled_image(data["image_active"], (size_x, size_y))
                if img_active:
                    if b_type not in self.building_images: self.building_images[b_type] = {}
                    self.building_images[b_type]['active'] = img_active

    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            self.handle_events()
            if self.state in [GameState.PLAY, GameState.CONTAINER, GameState.SHOP, GameState.TECH_TREE]:
                self.logic_timer += dt
                while self.logic_timer >= 1000 / LOGIC_TICK_RATE:
                    self.logic_timer -= 1000 / LOGIC_TICK_RATE
                    self.world.tick()
            self.render()
            pygame.display.flip()

    def handle_events(self):
        mx, my = pygame.mouse.get_pos()
        max_cam_x = self.world.max_width * TILE_SIZE - SCREEN_WIDTH
        max_cam_y = self.world.max_height * TILE_SIZE - SCREEN_HEIGHT
        self.camera_x = max(0, min(self.camera_x, max_cam_x))
        self.camera_y = max(0, min(self.camera_y, max_cam_y))

        gx = (mx + self.camera_x) // TILE_SIZE
        gy = (my + self.camera_y) // TILE_SIZE

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if pygame.K_1 <= event.key <= pygame.K_9:
                    self.selected_hotbar_idx = event.key - pygame.K_1
                
                if event.key == pygame.K_e:
                    if self.state == GameState.CONTAINER: self.close_container()
                    else: self.open_container(None)
                elif event.key == pygame.K_b:
                    if self.state == GameState.SHOP: self.state = GameState.PLAY
                    else: 
                        self.close_container()
                        self.state = GameState.SHOP
                elif event.key == pygame.K_m:
                    if self.state == GameState.MISSIONS: self.state = GameState.PLAY
                    else:
                        self.close_container()
                        self.state = GameState.MISSIONS
                elif event.key == pygame.K_t:
                    # 수정: T 키는 이제 닫기 기능만 수행 (여는 기능 제거)
                    if self.state == GameState.TECH_TREE: self.close_container()
                elif event.key == pygame.K_ESCAPE:
                    if self.state != GameState.PLAY:
                        self.close_container()
                        self.state = GameState.PLAY
                    else:
                        self.delete_mode = False
                
                if self.state == GameState.PLAY:
                    if event.key == pygame.K_r: self.build_rot = Direction((self.build_rot.value + 1) % 4)
                    elif event.key == pygame.K_f: self.pickup_items(mx + self.camera_x, my + self.camera_y)
                    elif event.key == pygame.K_x:
                        self.delete_mode = not self.delete_mode
                        self.inspected_info = None

            if event.type == pygame.MOUSEWHEEL:
                if self.state == GameState.SHOP:
                    if 50 <= mx <= 350: self.shop_buy_scroll = max(0, self.shop_buy_scroll - event.y * 30)
                    elif 400 <= mx <= 700: self.shop_sell_scroll = max(0, self.shop_sell_scroll - event.y * 30)
                elif self.state == GameState.MISSIONS:
                    self.mission_scroll = max(0, self.mission_scroll - event.y * 30)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == GameState.PLAY:
                    in_bounds = (self.world.min_x <= gx < self.world.max_x and self.world.min_y <= gy < self.world.max_y)

                    if event.button == 1:
                        if not in_bounds: continue

                        if self.delete_mode:
                            if self.world.remove_building(gx, gy): 
                                self.inspected_info = None
                        else:
                            slot_idx = 27 + self.selected_hotbar_idx
                            stack = self.world.player_inv.slots[slot_idx]
                            is_holding_building = stack and ITEM_DATA[stack.item_type].get("is_building")

                            if is_holding_building:
                                b_type = ITEM_TO_BUILDING[stack.item_type]
                                b_data = BUILDING_DATA[b_type]
                                if self.world.can_place_building(gx, gy, b_data["size"][0], b_data["size"][1]):
                                    if self.world.player_inv.remove_from_slot(slot_idx, 1):
                                        self.world.place_building(Building(b_type, gx, gy, self.build_rot))
                                        self.inspected_info = None
                            else:
                                pass

                    elif event.button == 3:
                        b = self.world.get_building_at(gx, gy)
                        if b:
                            # 수정: 연구소를 우클릭하면 바로 연구 트리(TECH_TREE) UI를 엽니다.
                            if b.type == BuildingType.LAB:
                                self.open_tech_tree(b)
                                self.inspected_info = None
                            elif hasattr(b, 'inv'):
                                self.open_container(b)
                                self.inspected_info = None
                            else:
                                self.inspected_info = b.get_info_text()
                        else:
                            res = self.world.get_tile_resource(gx, gy)
                            if res: self.inspected_info = [f"[ {ITEM_DATA[res]['name']} ]", ITEM_DATA[res].get("desc", "")]
                            else: self.inspected_info = None

                elif self.state == GameState.CONTAINER: self.handle_inventory_click(event.button, mx, my)
                elif self.state == GameState.SHOP: 
                    if event.button == 1: self.handle_shop_click(mx, my)
                elif self.state == GameState.MISSIONS: 
                    if event.button == 1: self.handle_mission_click(mx, my)
                elif self.state == GameState.TECH_TREE:
                    # 수정: 연구 트리 상태에서도 인벤토리 클릭(투입)과 연구 선택이 모두 가능해야 함
                    if event.button == 1: self.handle_tech_click(mx, my)
                    self.handle_inventory_click(event.button, mx, my)

        if self.state == GameState.PLAY:
            keys = pygame.key.get_pressed()
            spd = 15
            if keys[pygame.K_w]: self.camera_y -= spd
            if keys[pygame.K_s]: self.camera_y += spd
            if keys[pygame.K_a]: self.camera_x -= spd
            if keys[pygame.K_d]: self.camera_x += spd
            
            max_cam_x = self.world.max_width * TILE_SIZE - SCREEN_WIDTH
            max_cam_y = self.world.max_height * TILE_SIZE - SCREEN_HEIGHT
            self.camera_x = max(0, min(self.camera_x, max_cam_x))
            self.camera_y = max(0, min(self.camera_y, max_cam_y))

    def open_container(self, container):
        self.state = GameState.CONTAINER
        self.opened_container = container

    def open_tech_tree(self, container):
        self.state = GameState.TECH_TREE
        self.opened_container = container

    def close_container(self):
        self.state = GameState.PLAY
        self.opened_container = None
        if self.held_item:
                if not self.world.player_inv.add_item(self.held_item.item_type, self.held_item.count):
                    cx = (self.world.min_x + self.world.max_x) // 2
                    cy = (self.world.min_y + self.world.max_y) // 2
                    for _ in range(self.held_item.count):
                        self.world.add_item(ItemEntity(self.held_item.item_type, cx, cy))
                self.held_item = None

    def handle_inventory_click(self, button, mx, my):
        # 조립기 레시피 선택 로직 (CONTAINER 상태일 때만 동작)
        if self.state == GameState.CONTAINER and button == 1 and self.opened_container and self.opened_container.type == BuildingType.ASSEMBLER:
            c_x, c_y = SCREEN_WIDTH // 2, 100
            rx, ry = c_x + 120, c_y
            for r_type, r_data in ASSEMBLER_RECIPES.items():
                if pygame.Rect(rx, ry, 150, 35).collidepoint(mx, my):
                    self.opened_container.recipe = r_type
                    self.opened_container.progress = 0
                    return
                ry += 45

        slot_info = self.get_slot_under_mouse(mx, my)
        if not slot_info: return
        inv, idx = slot_info
        stack = inv.slots[idx]
        
        mods = pygame.key.get_mods()
        if button == 1 and (mods & pygame.KMOD_SHIFT) and stack and not self.held_item:
            if self.opened_container:
                if inv == self.world.player_inv:
                    target_range = None
                    if self.opened_container.type == BuildingType.ASSEMBLER: target_range = range(4)
                    elif self.opened_container.type == BuildingType.LAB: target_range = range(1)
                    elif self.opened_container.type == BuildingType.SMELTER: target_range = range(2)
                    if self.opened_container.inv.add_stack(stack, target_range):
                            if stack.count <= 0: inv.slots[idx] = None
                else:
                    if self.world.player_inv.add_stack(stack):
                        if stack.count <= 0: inv.slots[idx] = None
            else:
                if 0 <= idx < 27: 
                    self.world.player_inv.add_stack(stack, range(27, 36))
                    if stack.count <= 0: inv.slots[idx] = None
                elif 27 <= idx < 36: 
                    self.world.player_inv.add_stack(stack, range(0, 27))
                    if stack.count <= 0: inv.slots[idx] = None
            return

        if button == 1:
            if not self.held_item:
                if stack:
                    self.held_item = stack
                    inv.slots[idx] = None
            else:
                if not stack:
                    inv.slots[idx] = self.held_item
                    self.held_item = None
                elif stack.item_type == self.held_item.item_type:
                    space = stack.max_stack - stack.count
                    move = min(space, self.held_item.count)
                    stack.count += move
                    self.held_item.count -= move
                    if self.held_item.count <= 0: self.held_item = None
                else:
                    inv.slots[idx] = self.held_item
                    self.held_item = stack
        elif button == 3:
            if not self.held_item and stack:
                half = stack.count // 2
                if half > 0:
                    self.held_item = ItemStack(stack.item_type, stack.count - half)
                    stack.count = half
            elif self.held_item:
                if not stack:
                    inv.slots[idx] = ItemStack(self.held_item.item_type, 1)
                    self.held_item.count -= 1
                elif stack.item_type == self.held_item.item_type and stack.count < stack.max_stack:
                    stack.count += 1
                    self.held_item.count -= 1
                if self.held_item and self.held_item.count <= 0: self.held_item = None

    def get_slot_under_mouse(self, mx, my):
        # 수정: TECH_TREE 상태에서도 인벤토리 슬롯 인식을 위해 조건 추가
        if self.state not in [GameState.CONTAINER, GameState.TECH_TREE]: return None
        
        pinv_x, pinv_y = SCREEN_WIDTH // 2 - (9 * 44) // 2, SCREEN_HEIGHT - 200
        for i in range(36):
            col, row = i % 9, i // 9
            sx, sy = pinv_x + col * 44, pinv_y + (row if row < 3 else 3.2) * 44
            if pygame.Rect(sx, sy, 40, 40).collidepoint(mx, my): return (self.world.player_inv, i)

        if self.opened_container:
            c_x, c_y = SCREEN_WIDTH // 2, 100
            b = self.opened_container
            if b.type == BuildingType.BOX:
                start_x = c_x - (9 * 44) // 2
                for i in range(27):
                    sx, sy = start_x + (i%9)*44, c_y + (i//9)*44
                    if pygame.Rect(sx, sy, 40, 40).collidepoint(mx, my): return (b.inv, i)
            elif b.type == BuildingType.SMELTER:
                slots = [(c_x - 44, c_y), (c_x - 44, c_y + 88), (c_x + 60, c_y + 44)]
                for i, (sx, sy) in enumerate(slots):
                    if pygame.Rect(sx, sy, 40, 40).collidepoint(mx, my): return (b.inv, i)
            elif b.type == BuildingType.ASSEMBLER:
                slots = [(c_x - 90, c_y), (c_x - 46, c_y), (c_x - 90, c_y + 44), (c_x - 46, c_y + 44), (c_x + 50, c_y + 22)]
                for i, (sx, sy) in enumerate(slots):
                    if pygame.Rect(sx, sy, 40, 40).collidepoint(mx, my): return (b.inv, i)
            elif b.type == BuildingType.LAB:
                # TECH_TREE 상태일 때도 랩의 인벤토리 슬롯(팩 투입구) 위치 인식
                if pygame.Rect(c_x - 20, c_y + 40, 40, 40).collidepoint(mx, my): return (b.inv, 0)
        return None

    def pickup_items(self, wx, wy):
        wx_grid, wy_grid = int(wx // TILE_SIZE), int(wy // TILE_SIZE)
        if not (self.world.min_x <= wx_grid < self.world.max_x and self.world.min_y <= wy_grid < self.world.max_y): return

        picked = [i for i in self.world.items if math.hypot(i.get_render_pos()[0]-wx, i.get_render_pos()[1]-wy) <= PICKUP_RADIUS]
        for item in picked:
            if self.world.player_inv.add_item(item.type, 1):
                if item in self.world.items: self.world.items.remove(item)

    def handle_shop_click(self, mx, my):
        buy_viewport = pygame.Rect(50, 140, 300, SCREEN_HEIGHT - 200)
        sell_viewport = pygame.Rect(400, 140, 300, SCREEN_HEIGHT - 260)

        if buy_viewport.collidepoint(mx, my):
            adjusted_y = my - 140 + self.shop_buy_scroll
            item_idx = int(adjusted_y // 60)
            if 0 <= item_idx < len(SHOP_ITEMS):
                if adjusted_y % 60 <= 50:
                    item_type = SHOP_ITEMS[item_idx]
                    
                    is_locked = False
                    if item_type == ItemType.FAST_CONVEYOR and "logistics" not in self.world.unlocked_techs: is_locked = True
                    elif item_type == ItemType.HEAVY_MINER and "mining" not in self.world.unlocked_techs: is_locked = True
                    
                    if not is_locked:
                        cost = ITEM_DATA[item_type]["cost"]
                        if self.world.money >= cost:
                            if self.world.player_inv.add_item(item_type, 1):
                                self.world.money -= cost

        sell_items = [t for t in ItemType if not ITEM_DATA[t].get("is_building")]
        if sell_viewport.collidepoint(mx, my):
            adjusted_y = my - 140 + self.shop_sell_scroll
            item_idx = int(adjusted_y // 60)
            if 0 <= item_idx < len(sell_items):
                if adjusted_y % 60 <= 50:
                    item_type = sell_items[item_idx]
                    if self.world.player_inv.remove_item(item_type, 1):
                        self.world.money += ITEM_DATA[item_type]["value"]

        sell_all_rect = pygame.Rect(400, SCREEN_HEIGHT - 100, 300, 50)
        if sell_all_rect.collidepoint(mx, my):
            for i, stack in enumerate(self.world.player_inv.slots):
                if stack and not ITEM_DATA[stack.item_type].get("is_building"):
                    self.world.money += ITEM_DATA[stack.item_type]["value"] * stack.count
                    self.world.player_inv.slots[i] = None

    def handle_mission_click(self, mx, my):
        mission_viewport = pygame.Rect(50, 140, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 200)
        if not mission_viewport.collidepoint(mx, my): return

        adjusted_y = my - 140 + self.mission_scroll
        mission_idx = int(adjusted_y // 100)
        
        if 0 <= mission_idx < len(self.world.available_missions):
            if adjusted_y % 100 <= 90:
                mission_id = self.world.available_missions[mission_idx]
                mission_status = self.world.missions.get(mission_id)

                if mission_status == "ready":
                    base_y = (mission_idx * 100) + 140 - self.mission_scroll
                    complete_btn_rect = pygame.Rect(SCREEN_WIDTH - 200, base_y + 10, 150, 40)
                    if complete_btn_rect.collidepoint(mx, my):
                        self.world.complete_mission(mission_id)
    
    def handle_tech_click(self, mx, my):
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        start_y = cy - 100
        for tech_id, data in TECH_DATA.items():
            rect = pygame.Rect(cx - 200, start_y, 400, 80)
            if rect.collidepoint(mx, my):
                req = data.get("req")
                if req and req not in self.world.unlocked_techs: return
                self.world.start_research(tech_id)
            start_y += 100

    def render(self):
        self.screen.fill(COLOR_BG)
        self.render_world()
        
        tooltip_stack = None 
        if self.state == GameState.PLAY:
            self.render_hud()
            self.render_hotbar()
        elif self.state == GameState.CONTAINER:
            tooltip_stack = self.render_container_ui()
            self.render_hotbar()
        elif self.state == GameState.SHOP:
            self.render_shop_ui()
        elif self.state == GameState.MISSIONS:
            tooltip_stack = self.render_mission_ui()
        elif self.state == GameState.TECH_TREE:
            self.render_tech_ui()
            # TECH_TREE 상태에서도 툴팁 표시를 위해 인벤토리 체크
            mx, my = pygame.mouse.get_pos()
            slot_info = self.get_slot_under_mouse(mx, my)
            if slot_info:
                inv, idx = slot_info
                if inv.slots[idx]: tooltip_stack = inv.slots[idx]

        mx, my = pygame.mouse.get_pos()
        if self.held_item:
            self.draw_item(mx - 20, my - 20, self.held_item.item_type, self.held_item.count)
        else:
            if self.state == GameState.CONTAINER:
                slot_info = self.get_slot_under_mouse(mx, my)
                if slot_info:
                    inv, idx = slot_info
                    if inv.slots[idx]: tooltip_stack = inv.slots[idx]
            elif self.state == GameState.PLAY:
                px, py = SCREEN_WIDTH // 2 - (9 * 44) // 2, SCREEN_HEIGHT - 60
                for i in range(9):
                    if pygame.Rect(px + i * 44, py, 40, 40).collidepoint(mx, my):
                        if self.world.player_inv.slots[27+i]: 
                            tooltip_stack = self.world.player_inv.slots[27+i]
                            break
        
        if tooltip_stack and not self.held_item:
            self.render_tooltip(tooltip_stack, mx, my)

    def render_world(self):
        sx, ex = max(0, self.camera_x // TILE_SIZE), min(self.world.max_width, (self.camera_x + SCREEN_WIDTH) // TILE_SIZE + 1)
        sy, ey = max(0, self.camera_y // TILE_SIZE), min(self.world.max_height, (self.camera_y + SCREEN_HEIGHT) // TILE_SIZE + 1)
        
        for y in range(sy, ey):
            for x in range(sx, ex):
                rx, ry = x*TILE_SIZE - self.camera_x, y*TILE_SIZE - self.camera_y
                r = pygame.Rect(rx, ry, TILE_SIZE, TILE_SIZE)
                
                if not (self.world.min_x <= x < self.world.max_x and self.world.min_y <= y < self.world.max_y):
                    pygame.draw.rect(self.screen, COLOR_BG, r) 
                    continue 
                
                if self.grass_tile: self.screen.blit(self.grass_tile, r)
                else: pygame.draw.rect(self.screen, COLOR_GRASS, r)
                
                res = self.world.tiles[y][x]
                if res:
                    tile_sprite = self.tile_images.get(res)
                    if tile_sprite: self.screen.blit(tile_sprite, r)
                    else:
                        color = COLOR_COAL_ORE if res == ItemType.COAL_ORE else ITEM_DATA[res]["color"]
                        pygame.draw.rect(self.screen, color, r)
                pygame.draw.rect(self.screen, COLOR_GRID, r, 1)

        for b in sorted(self.world.buildings.values(), key=lambda b: b.gy):
            r = b.get_rect()
            r.x -= self.camera_x
            r.y -= self.camera_y
            
            if r.colliderect(self.screen.get_rect()):
                sprite_orig = None
                sprite_dict = self.building_images.get(b.type)
                
                if sprite_dict:
                    if b.type == BuildingType.SMELTER and 'active' in sprite_dict and b.fuel_left > 0:
                        sprite_orig = sprite_dict['active']
                    elif b.type == BuildingType.ASSEMBLER and 'active' in sprite_dict and b.progress > 0:
                        sprite_orig = sprite_dict['active']
                    elif b.type == BuildingType.LAB and 'active' in sprite_dict and b.active:
                        sprite_orig = sprite_dict['active']
                    else:
                        sprite_orig = sprite_dict.get('default')

                if sprite_orig:
                    angle = 0
                    if b.direction == Direction.UP: angle = 180
                    elif b.direction == Direction.RIGHT: angle = 90
                    elif b.direction == Direction.LEFT: angle = -90
                    sprite_rot = pygame.transform.rotate(sprite_orig, angle)
                    new_rect = sprite_rot.get_rect(center=r.center)
                    self.screen.blit(sprite_rot, new_rect)
                else:
                    col = ITEM_DATA[BUILDING_TO_ITEM[b.type]]["color"]
                    pygame.draw.rect(self.screen, col, r)
                    pygame.draw.rect(self.screen, (0,0,0), r, 2)
                    if b.data.get("has_dir"): self.draw_arrow(r, b.direction)

        for item in self.world.items:
            ix_tile, iy_tile = int(item.x), int(item.y)
            if not (self.world.min_x <= ix_tile < self.world.max_x and self.world.min_y <= iy_tile < self.world.max_y): continue

            ix, iy = item.get_render_pos()
            if 0 <= ix - self.camera_x <= SCREEN_WIDTH and 0 <= iy - self.camera_y <= SCREEN_HEIGHT:
                sprite = self.item_images.get(item.type)
                if sprite:
                    scaled_sprite = pygame.transform.scale(sprite, (24, 24))
                    self.screen.blit(scaled_sprite, (ix - self.camera_x - 12, iy - self.camera_y - 12))
                else:
                    pygame.draw.circle(self.screen, ITEM_DATA[item.type]["color"], (ix - self.camera_x, iy - self.camera_y), 8)
        
        if self.state == GameState.PLAY:
            mx, my = pygame.mouse.get_pos()
            gx, gy = (mx + self.camera_x) // TILE_SIZE, (my + self.camera_y) // TILE_SIZE
            
            if self.delete_mode:
                r = pygame.Rect(gx*TILE_SIZE - self.camera_x, gy*TILE_SIZE - self.camera_y, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(self.screen, (255, 0, 0), r, 3)
            else:
                stack = self.world.player_inv.slots[27 + self.selected_hotbar_idx]
                if stack and ITEM_DATA[stack.item_type].get("is_building"):
                    b_type = ITEM_TO_BUILDING[stack.item_type]
                    b_data = BUILDING_DATA[b_type]
                    r = pygame.Rect(gx*TILE_SIZE - self.camera_x, gy*TILE_SIZE - self.camera_y, b_data["size"][0]*TILE_SIZE, b_data["size"][1]*TILE_SIZE)
                    
                    ghost_sprite = None
                    sprite_dict = self.building_images.get(b_type)
                    if sprite_dict: ghost_sprite = sprite_dict.get('default')

                    if ghost_sprite:
                        angle = 0
                        if self.build_rot == Direction.UP: angle = 180
                        elif self.build_rot == Direction.RIGHT: angle = 90
                        elif self.build_rot == Direction.LEFT: angle = -90
                        sprite_rot = pygame.transform.rotate(ghost_sprite, angle)
                        sprite_rot.set_alpha(150)
                        new_rect = sprite_rot.get_rect(center=r.center)
                        self.screen.blit(sprite_rot, new_rect)
                    else: pygame.draw.rect(self.screen, (255, 255, 255, 100), r, 2)
                    
                    can_place = self.world.can_place_building(gx, gy, b_data["size"][0], b_data["size"][1])
                    color = (255, 255, 255) if can_place else (255, 0, 0)
                    pygame.draw.rect(self.screen, color, r, 3)

    def render_hud(self):
        pygame.draw.rect(self.screen, COLOR_PANEL, (0,0,SCREEN_WIDTH,40))
        
        mode_txt = "[X]삭제모드: 켜짐" if self.delete_mode else "[X]삭제모드: 꺼짐"
        col = (255, 100, 100) if self.delete_mode else (255, 255, 255)
        self.screen.blit(self.font.render(mode_txt, True, col), (SCREEN_WIDTH - 150, 50))

        info = f"자금: {self.world.money} Cr | [E]인벤 [B]상점 [M]미션 | [우클릭]상호작용"
        self.screen.blit(self.font.render(info, True, COLOR_TEXT), (20, 10))

        if self.world.mission_alert:
            alert_text = self.font.render("미션 완료 가능! (M)", True, (255, 100, 100))
            self.screen.blit(alert_text, (SCREEN_WIDTH - 200, 10))

        if self.inspected_info:
            my_ui = SCREEN_HEIGHT - 100
            for i, txt in enumerate(self.inspected_info):
                self.screen.blit(self.font.render(txt, True, COLOR_TEXT), (20, my_ui - 30 - i*25))

    def render_hotbar(self):
        px, py = SCREEN_WIDTH // 2 - (9 * 44) // 2, SCREEN_HEIGHT - 60
        mx, my = pygame.mouse.get_pos()
        for i in range(9):
            sx, sy = px + i * 44, py
            hover = pygame.Rect(sx, sy, 40, 40).collidepoint(mx, my)
            self.draw_slot(sx, sy, self.world.player_inv.slots[27+i], hover, i == self.selected_hotbar_idx)

    def render_container_ui(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,150))
        self.screen.blit(overlay, (0,0))
        pinv_x, pinv_y = SCREEN_WIDTH // 2 - (9 * 44) // 2, SCREEN_HEIGHT - 200
        self.screen.blit(self.font.render("인벤토리", True, COLOR_TEXT), (pinv_x, pinv_y - 25))
        mx, my = pygame.mouse.get_pos()
        for i in range(36):
            col, row = i % 9, i // 9
            sx, sy = pinv_x + col * 44, pinv_y + (row if row < 3 else 3.2) * 44
            hover = pygame.Rect(sx, sy, 40, 40).collidepoint(mx, my)
            self.draw_slot(sx, sy, self.world.player_inv.slots[i], hover, i >= 27 and (i-27) == self.selected_hotbar_idx)

        hovered_recipe_ingredient = None

        if self.opened_container:
            c_x, c_y = SCREEN_WIDTH // 2, 100
            b = self.opened_container
            self.screen.blit(self.font.render(BUILDING_DATA[b.type]["name"], True, COLOR_TEXT), (c_x - 50, c_y - 30))
            
            if b.type == BuildingType.BOX:
                start_x = c_x - (9 * 44) // 2
                for i in range(27):
                    sx, sy = start_x + (i%9)*44, c_y + (i//9)*44
                    self.draw_slot(sx, sy, b.inv.slots[i], pygame.Rect(sx, sy, 40, 40).collidepoint(mx, my))
            elif b.type == BuildingType.SMELTER:
                slots = [(c_x - 44, c_y), (c_x - 44, c_y + 88), (c_x + 60, c_y + 44)]
                for i, (sx, sy) in enumerate(slots):
                    self.draw_slot(sx, sy, b.inv.slots[i], pygame.Rect(sx, sy, 40, 40).collidepoint(mx, my))
                if b.max_fuel_time > 0:
                    h = int(40 * (b.fuel_left / b.max_fuel_time))
                    pygame.draw.rect(self.screen, COLOR_PROGRESS_BG, (c_x+1, c_y+44, 10, 40))
                    pygame.draw.rect(self.screen, COLOR_PROGRESS_FIRE, (c_x+1, c_y+44 + (40-h), 10, h))
                if b.inv.slots[0] and b.inv.slots[0].item_type in SMELTER_RECIPES:
                    w = int(50 * (b.progress / SMELTER_RECIPES[b.inv.slots[0].item_type]["time"]))
                    pygame.draw.rect(self.screen, COLOR_PROGRESS_BG, (c_x+5, c_y+54, 50, 20))
                    pygame.draw.rect(self.screen, COLOR_PROGRESS_ARROW, (c_x+5, c_y+54, w, 20))
            elif b.type == BuildingType.ASSEMBLER:
                slots = [(c_x - 90, c_y), (c_x - 46, c_y), (c_x - 90, c_y + 44), (c_x - 46, c_y + 44), (c_x + 50, c_y + 22)]
                for i, (sx, sy) in enumerate(slots):
                    self.draw_slot(sx, sy, b.inv.slots[i], pygame.Rect(sx, sy, 40, 40).collidepoint(mx, my))
                
                if b.recipe:
                    w = int(40 * (b.progress / ASSEMBLER_RECIPES[b.recipe]["time"]))
                    pygame.draw.rect(self.screen, COLOR_PROGRESS_BG, (c_x + 4, c_y + 30, 40, 20))
                    pygame.draw.rect(self.screen, COLOR_PROGRESS_ARROW, (c_x + 4, c_y + 30, w, 20))
                
                rx, ry = c_x + 120, c_y
                self.screen.blit(self.font.render("레시피 선택:", True, COLOR_TEXT), (rx, ry - 25))
                for r_type, r_data in ASSEMBLER_RECIPES.items():
                    r_rect = pygame.Rect(rx, ry, 150, 35)
                    col = COLOR_BUTTON_HOVER if r_rect.collidepoint(mx, my) else COLOR_BUTTON
                    if b.recipe == r_type: col = (100, 200, 100)
                    pygame.draw.rect(self.screen, col, r_rect, border_radius=5)
                    self.draw_item(rx - 5, ry - 3, r_type) 
                    self.screen.blit(self.font_small.render(r_data["name"], True, COLOR_TEXT), (rx + 35, ry + 10))
                    ix = rx + 160
                    for ing_type, ing_count in r_data["inputs"].items():
                        self.draw_item(ix, ry + 5, ing_type, ing_count)
                        if pygame.Rect(ix, ry + 5, 30, 30).collidepoint(mx, my):
                            hovered_recipe_ingredient = ItemStack(ing_type, ing_count)
                        ix += 35
                    ry += 45
        
        return hovered_recipe_ingredient

    def render_shop_ui(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,200))
        self.screen.blit(overlay, (0,0))
        self.screen.blit(self.font_big.render("상점", True, COLOR_TEXT), (50, 30))
        self.screen.blit(self.font_big.render(f"보유: {self.world.money} Cr", True, COLOR_ARROW), (SCREEN_WIDTH - 300, 30))

        mx, my = pygame.mouse.get_pos()
        
        buy_viewport = pygame.Rect(50, 140, 300, SCREEN_HEIGHT - 200)
        self.screen.blit(self.font_big.render("[ 건물 구매 ]", True, COLOR_TEXT), (50, 80))
        
        max_buy_scroll = max(0, len(SHOP_ITEMS) * 60 - buy_viewport.height)
        self.shop_buy_scroll = max(0, min(self.shop_buy_scroll, max_buy_scroll))

        self.screen.set_clip(buy_viewport)
        y = 140 - self.shop_buy_scroll
        for item_type in SHOP_ITEMS:
            r = pygame.Rect(50, y, 300, 50)
            if r.bottom > buy_viewport.top and r.top < buy_viewport.bottom:
                is_locked = False
                lock_msg = ""
                if item_type == ItemType.FAST_CONVEYOR and "logistics" not in self.world.unlocked_techs:
                    is_locked = True; lock_msg = "(연구 필요)"
                elif item_type == ItemType.HEAVY_MINER and "mining" not in self.world.unlocked_techs:
                    is_locked = True; lock_msg = "(연구 필요)"

                col = COLOR_BUTTON_LOCKED if is_locked else COLOR_BUTTON
                if not is_locked and r.collidepoint(mx, my) and buy_viewport.collidepoint(mx, my): col = COLOR_BUTTON_HOVER
                
                pygame.draw.rect(self.screen, col, r, border_radius=8)
                d = ITEM_DATA[item_type]
                self.draw_item(55, y + 7, item_type)
                txt_col = (150, 150, 150) if is_locked else COLOR_TEXT
                self.screen.blit(self.font.render(f"{d['name']} - {d['cost']} Cr {lock_msg}", True, txt_col), (100, y + 15))
            y += 60
        self.screen.set_clip(None)

        sell_items = [t for t in ItemType if not ITEM_DATA[t].get("is_building")]
        sell_viewport = pygame.Rect(400, 140, 300, SCREEN_HEIGHT - 260)
        self.screen.blit(self.font_big.render("[ 자원 판매 ]", True, COLOR_TEXT), (400, 80))

        max_sell_scroll = max(0, len(sell_items) * 60 - sell_viewport.height)
        self.shop_sell_scroll = max(0, min(self.shop_sell_scroll, max_sell_scroll))

        self.screen.set_clip(sell_viewport)
        y = 140 - self.shop_sell_scroll
        for item_type in sell_items:
            r = pygame.Rect(400, y, 300, 50)
            if r.bottom > sell_viewport.top and r.top < sell_viewport.bottom:
                col = COLOR_BUTTON_HOVER if r.collidepoint(mx, my) and sell_viewport.collidepoint(mx, my) else COLOR_BUTTON
                pygame.draw.rect(self.screen, col, r, border_radius=8)
                d = ITEM_DATA[item_type]
                self.draw_item(405, y + 7, item_type)
                self.screen.blit(self.font.render(f"{d['name']} - {d['value']} Cr", True, COLOR_TEXT), (450, y + 15))
            y += 60
        self.screen.set_clip(None)

        sell_all_rect = pygame.Rect(400, SCREEN_HEIGHT - 100, 300, 50)
        col = (100, 150, 100) if sell_all_rect.collidepoint(mx, my) else (80, 120, 80)
        pygame.draw.rect(self.screen, col, sell_all_rect, border_radius=8)
        self.screen.blit(self.font.render("모두 판매", True, COLOR_TEXT), (410, SCREEN_HEIGHT - 100 + 15))

    def render_mission_ui(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,200))
        self.screen.blit(overlay, (0,0))
        self.screen.blit(self.font_big.render("미션 (나가기: M)", True, COLOR_TEXT), (50, 30))
        
        size_x = self.world.max_x - self.world.min_x
        size_y = self.world.max_y - self.world.min_y
        self.screen.blit(self.font_big.render(f"현재 영역: {size_x}x{size_y}", True, COLOR_ARROW), (SCREEN_WIDTH - 300, 30))

        mx, my = pygame.mouse.get_pos()
        mission_viewport = pygame.Rect(50, 140, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 200)
        max_mission_scroll = max(0, len(self.world.available_missions) * 100 - mission_viewport.height)
        self.mission_scroll = max(0, min(self.mission_scroll, max_mission_scroll))

        self.screen.set_clip(mission_viewport)
        y = 140 - self.mission_scroll
        hovered_item_stack = None

        for mission_id in self.world.available_missions:
            r = pygame.Rect(50, y, SCREEN_WIDTH - 100, 90)
            if r.bottom > mission_viewport.top and r.top < mission_viewport.bottom:
                pygame.draw.rect(self.screen, COLOR_PANEL, r, border_radius=8)
                data = MISSION_DATA[mission_id]
                status = self.world.missions.get(mission_id)
                self.screen.blit(self.font.render(data["name"], True, COLOR_TEXT), (65, y + 10))
                self.screen.blit(self.font_small.render(data["desc"], True, (180, 180, 180)), (65, y + 35))

                self.screen.blit(self.font_small.render("요구:", True, COLOR_TEXT), (65, y + 60))
                rx = 100
                for item_type, req_count in data["requirements"].items():
                    self.draw_item(rx, y + 50, item_type, 1) 
                    player_count = self.world.player_inv.count_items(item_type)
                    col = (100, 255, 100) if player_count >= req_count else COLOR_TEXT
                    count_text = self.font_small.render(f"{player_count}/{req_count}", True, col)
                    self.screen.blit(count_text, (rx + 40 - count_text.get_width(), y + 78))
                    if pygame.Rect(rx, y + 50, 40, 40).collidepoint(mx, my):
                        hovered_item_stack = ItemStack(item_type, req_count)
                    rx += 44

                self.screen.blit(self.font_small.render("보상:", True, COLOR_TEXT), (rx + 20, y + 60))
                rew_x = rx + 50
                if "money" in data["rewards"]:
                    self.screen.blit(self.font.render(f"{data['rewards']['money']} Cr", True, (255, 215, 0)), (rew_x, y + 55))
                    rew_x += 100
                if "expand" in data["rewards"]:
                    self.screen.blit(self.font.render(f"확장 +{data['rewards']['expand']}", True, (100, 100, 255)), (rew_x, y + 55))

                if status == "ready":
                    btn_rect = pygame.Rect(SCREEN_WIDTH - 200, y + 10, 150, 40)
                    col = COLOR_BUTTON_HOVER if btn_rect.collidepoint(mx, my) else (100, 200, 100)
                    pygame.draw.rect(self.screen, col, btn_rect, border_radius=5)
                    text_surf = self.font.render("완료", True, COLOR_TEXT)
                    text_rect = text_surf.get_rect(center=btn_rect.center)
                    self.screen.blit(text_surf, text_rect)
                elif status == "completed":
                    self.screen.blit(self.font.render("완료됨", True, (100, 100, 100)), (SCREEN_WIDTH - 180, y + 20))
            y += 100
        self.screen.set_clip(None)
        return hovered_item_stack

    def render_tech_ui(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill(COLOR_TECH_BG)
        self.screen.blit(overlay, (0,0))
        self.screen.blit(self.font_big.render("기술 연구 트리 (나가기: T 또는 ESC)", True, COLOR_TEXT), (50, 30))
        
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        
        # --- 수정: 인벤토리(팩 투입)와 플레이어 인벤토리 표시 ---
        pinv_x, pinv_y = SCREEN_WIDTH // 2 - (9 * 44) // 2, SCREEN_HEIGHT - 200
        self.screen.blit(self.font.render("인벤토리", True, COLOR_TEXT), (pinv_x, pinv_y - 25))
        mx, my = pygame.mouse.get_pos()
        for i in range(36):
            col, row = i % 9, i // 9
            sx, sy = pinv_x + col * 44, pinv_y + (row if row < 3 else 3.2) * 44
            hover = pygame.Rect(sx, sy, 40, 40).collidepoint(mx, my)
            self.draw_slot(sx, sy, self.world.player_inv.slots[i], hover, i >= 27 and (i-27) == self.selected_hotbar_idx)

        if self.opened_container and self.opened_container.type == BuildingType.LAB:
            b = self.opened_container
            c_x, c_y = SCREEN_WIDTH // 2, 100
            # 랩(연구소) 투입구 표시
            sx, sy = c_x - 20, c_y + 40
            self.draw_slot(sx, sy, b.inv.slots[0], pygame.Rect(sx, sy, 40, 40).collidepoint(mx, my))
            self.screen.blit(self.font_small.render("자동화 팩 투입", True, COLOR_TEXT), (sx - 20, sy - 15))
            
            if self.world.current_research:
                cur = TECH_DATA[self.world.current_research]
                pct = self.world.research_progress / cur['cost']
                w = int(200 * pct)
                pygame.draw.rect(self.screen, COLOR_PROGRESS_BG, (c_x - 100, c_y + 100, 200, 20))
                pygame.draw.rect(self.screen, COLOR_PROGRESS_RESEARCH, (c_x - 100, c_y + 100, w, 20))
                self.screen.blit(self.font.render(f"{cur['name']} ({int(pct*100)}%)", True, COLOR_TEXT), (c_x - 80, c_y + 105))
        # ---------------------------------------------------

        start_y = cy - 100
        for tech_id, data in TECH_DATA.items():
            rect = pygame.Rect(cx - 200, start_y, 400, 80)
            is_unlocked = tech_id in self.world.unlocked_techs
            is_researching = self.world.current_research == tech_id
            is_locked = False
            if data.get("req") and data["req"] not in self.world.unlocked_techs: is_locked = True

            col = COLOR_BUTTON
            if is_unlocked: col = COLOR_BUTTON_RESEARCHED
            elif is_researching: col = COLOR_PROGRESS_RESEARCH
            elif is_locked: col = COLOR_BUTTON_LOCKED
            elif rect.collidepoint(mx, my): col = COLOR_BUTTON_HOVER
            
            pygame.draw.rect(self.screen, col, rect, border_radius=10)
            pygame.draw.rect(self.screen, (200, 200, 200), rect, 2)

            name_txt = f"{data['name']} [완료]" if is_unlocked else data['name']
            self.screen.blit(self.font_big.render(name_txt, True, COLOR_TEXT), (rect.x + 20, rect.y + 15))
            self.screen.blit(self.font_small.render(data['desc'], True, (200, 200, 200)), (rect.x + 20, rect.y + 50))
            if not is_unlocked:
                 cost_txt = f"비용: 자동화 팩 {data['cost']}개"
                 self.screen.blit(self.font.render(cost_txt, True, (255, 100, 100)), (rect.right - 150, rect.centery - 10))
            start_y += 100

    def render_tooltip(self, stack, mx, my):
        data = ITEM_DATA[stack.item_type]
        lines = [data["name"], data.get("desc", "")]
        if data.get("fuel_value"): lines.append(f"연료 효율: {data['fuel_value']/LOGIC_TICK_RATE:.1f}초")
        mw = max(self.font.size(l)[0] for l in lines) + 10
        mh = len(lines) * 20 + 10
        tx, ty = mx + 10, my + 10
        if tx + mw > SCREEN_WIDTH: tx = mx - mw - 10
        if ty + mh > SCREEN_HEIGHT: ty = my - mh - 10
        
        s = pygame.Surface((mw, mh), pygame.SRCALPHA)
        s.fill(COLOR_TOOLTIP_BG)
        self.screen.blit(s, (tx, ty))
        for i, line in enumerate(lines):
            self.screen.blit(self.font.render(line, True, COLOR_TEXT), (tx+5, ty+5 + i*20))

    def draw_slot(self, x, y, stack, hover=False, selected=False):
        col = COLOR_SLOT_SELECTED if selected else (COLOR_SLOT_HOVER if hover else COLOR_SLOT)
        pygame.draw.rect(self.screen, col, (x, y, 40, 40), border_radius=3)
        if selected: pygame.draw.rect(self.screen, (255, 255, 0), (x, y, 40, 40), 2, border_radius=3)
        if stack: self.draw_item(x+2, y+2, stack.item_type, stack.count)

    def draw_item(self, x, y, item_type, count=1):
        sprite = self.item_images.get(item_type)
        if sprite: self.screen.blit(sprite, (x + 2, y + 2))
        else:
            col = ITEM_DATA[item_type]["color"]
            if ITEM_DATA[item_type].get("is_building"):
                pygame.draw.rect(self.screen, col, (x+6, y+6, 24, 24))
                pygame.draw.rect(self.screen, (0,0,0), (x+6, y+6, 24, 24), 1)
            else:
                pygame.draw.circle(self.screen, col, (x+18, y+18), 10)
                pygame.draw.circle(self.screen, (0,0,0), (x+18, y+18), 10, 1)
        if count > 1:
            txt = self.font_small.render(str(count), True, (255, 255, 255))
            shadow = self.font_small.render(str(count), True, (0, 0, 0))
            self.screen.blit(shadow, (x+36-shadow.get_width()+1, y+36-shadow.get_height()+1))
            self.screen.blit(txt, (x+36-txt.get_width(), y+36-txt.get_height()))

    def draw_arrow(self, rect, direction, color=COLOR_ARROW):
        cx, cy = rect.centerx, rect.centery
        size = min(rect.width, rect.height) // 2.5
        dx, dy = direction.to_vector()
        end = (cx + dx * size, cy + dy * size)
        start = (cx - dx * size * 0.5, cy - dy * size * 0.5)
        pygame.draw.line(self.screen, color, start, end, 3)
        angle = math.atan2(dy, dx)
        p1 = end
        p2 = (end[0] - size*0.6 * math.cos(angle - math.pi/6), end[1] - size*0.6 * math.sin(angle - math.pi/6))
        p3 = (end[0] - size*0.6 * math.cos(angle + math.pi/6), end[1] - size*0.6 * math.sin(angle + math.pi/6))
        pygame.draw.polygon(self.screen, color, [p1, p2, p3])

if __name__ == "__main__":
    Game().run()