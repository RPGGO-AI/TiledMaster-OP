from enum import Enum
from typing import List, Tuple, Optional

import implement.town_impl.config as config
from tiled_master import MapElement, MapCache
from tiled_master.schema import *
from tiled_master.methods import NoiseMap
from tiled_master.utils.logger import logger, logger_runtime


class River(MapElement):
    """River element for the map"""
    class Resources(Enum):
        RIVER_TILES = "river_tiles"
    
    def __init__(self, name: str, descriptors: Optional[dict] = None):
        super().__init__(name=name, descriptors=descriptors)
    
    def _setup_resources(self):
        """Setup the required resources"""
        self._add_tile_group(self.Resources.RIVER_TILES.value)
    
    async def build(self, map_cache: MapCache):
        """Build the river on the map"""
        logger.info("generating river")
        map_width = map_cache.width
        map_height = map_cache.height
        
        # Get the river tile group resource
        river_tile_group = self.loaded_resources.get(self.Resources.RIVER_TILES.value)
        
        # Generate river using noise map
        noise_map = NoiseMap(map_width, map_height, map_cache.random_seed)
        river_tiles = noise_map.generate_natural_river(scale=river_tile_group.scale)
        
        # Place river tiles on the map
        map_cache.drop_tiles_from_tilegroup(river_tile_group, river_tiles, config.water_layer)
        
        logger.info("generate river done")


class Bush(MapElement):
    """Bush element for the map"""
    class Resources(Enum):
        BUSH_TILES = "bush_tiles"
    
    def __init__(self, name: str, descriptors: Optional[dict] = None):
        super().__init__(name=name, descriptors=descriptors)
    
    def _setup_resources(self):
        """Setup the required resources"""
        self._add_tile_group(self.Resources.BUSH_TILES.value)
    
    async def build(self, map_cache: MapCache):
        """Build bushes on the map"""
        logger.info("generating bush")
        map_width = map_cache.width
        map_height = map_cache.height
        
        # Get the bush tile group resource
        bush_tile_group = self.loaded_resources.get(self.Resources.BUSH_TILES.value)
        
        # Generate bush locations using noise map
        noise_map = NoiseMap(map_width, map_height, map_cache.random_seed)
        bush_tiles = noise_map.generate_bushes()
        
        # Filter out positions that overlap with water or roads
        drop_area = []
        for (x, y) in bush_tiles:
            if not map_cache.check_exists(x, y, config.water_layer) and not map_cache.check_exists(x, y, config.road_layer):
                drop_area.append((x, y))
        
        # Place bush tiles on the map
        map_cache.drop_tiles_from_tilegroup(bush_tile_group, drop_area, config.plants_layer)
        
        logger.info("generate bush done")


class Ground(MapElement):
    """Ground element for the map"""
    class Resources(Enum):
        GROUND_TILES = "ground_tiles"
    
    def __init__(self, name: str, descriptors: Optional[dict] = None):
        super().__init__(name=name, descriptors=descriptors)
    
    def _setup_resources(self):
        """Setup the required resources"""
        self._add_tile_group(self.Resources.GROUND_TILES.value)
    
    async def build(self, map_cache: MapCache):
        """Build the ground layer on the map"""
        logger.info("generating ground")
        
        # Get the ground tile group resource
        ground_tile_group = self.loaded_resources.get(self.Resources.GROUND_TILES.value)
        
        # Generate ground for the entire map
        map_width = map_cache.width
        map_height = map_cache.height
        drop_area = [(tx, ty) for tx in range(map_width) for ty in range(map_height)]
        
        # Place ground tiles on the map
        map_cache.drop_tiles_from_tilegroup(ground_tile_group, drop_area, config.ground_layer)
        
        logger.info("generate ground done")


class Woods(MapElement):
    """Woods element for the map"""
    class Resources(Enum):
        TREE_OBJECTS = "tree_objects"
    
    def __init__(self, name: str, descriptors: Optional[dict] = None):
        self.trees = []  # 存储树木位置信息
        super().__init__(name=name, descriptors=descriptors)
    
    def _setup_resources(self):
        """Setup the required resources"""
        self._add_object_group(self.Resources.TREE_OBJECTS.value)
    
    async def build(self, map_cache: MapCache):
        """Build the woods on the map"""
        logger.info("generate woods")
        
        # Get the tree object group resource
        object_group = self.loaded_resources.get(self.Resources.TREE_OBJECTS.value)
        
        # Generate woods
        map_width = map_cache.width
        map_height = map_cache.height
        self._generate_woods(map_cache, map_width, map_height, object_group)
        
        logger.info(f"generate woods with {len(self.trees)} trees")
    
    @logger_runtime()
    def _generate_woods(self, map_cache: MapCache, map_width, map_height, object_group: ObjectGroup):
        """Generate woods with trees"""
        max_attempts = max(map_height * map_width // 20 * object_group.scale, 40)
        noise_map = NoiseMap(map_width, map_height, map_cache.random_seed)
        woods_area = set(noise_map.generate_tree_area(object_group.scale))

        waters = set(map_cache.get_layer(config.water_layer))
        roads = set(map_cache.get_layer(config.road_layer))
        houses = set(map_cache.get_layer(config.house_layer))
        woods_area = woods_area - waters - roads - houses

        self.trees = []
        attempt = 0
        while attempt < max_attempts and woods_area:
            temp_map_cache = map_cache.create_copy(attempt)
            cx, cy = temp_map_cache.rand.choice(list(woods_area))
            candidate_obj_textures = object_group.textures

            obj_texture: TextureObject = temp_map_cache.rand.choices(
                candidate_obj_textures, 
                weights=[obj.rate for obj in candidate_obj_textures], 
                k=1
            )[0]

            tree_height = obj_texture.height
            tree_width = obj_texture.width
            
            # 计算左上角坐标
            x = cx - tree_width // 2
            y = cy - tree_height // 2
            
            # 检查是否可以放置树木
            can_place = True
            for tx in range(x, x + tree_width):
                for ty in range(y, y + tree_height):
                    if (tx < 0 or ty < 0 or tx >= map_width or ty >= map_height or
                        temp_map_cache.check_exists(tx, ty, config.water_layer) or
                        temp_map_cache.check_exists(tx, ty, config.road_layer) or
                        temp_map_cache.check_exists(tx, ty, config.house_layer) or
                        temp_map_cache.check_exists(tx, ty, config.tree_layer)):
                        can_place = False
                        break
                if not can_place:
                    break
            
            if can_place:
                # 放置树木
                if temp_map_cache.drop_object(x, y, config.tree_layer, obj_texture):
                    self.trees.append({"x": x, "y": y, "width": tree_width, "height": tree_height})
                    map_cache.assign(temp_map_cache)
                    
                    # 从可用区域中移除已用空间
                    for tx in range(cx - tree_width, cx + tree_width):
                        for ty in range(cy - tree_width, cy + tree_height):
                            woods_area.discard((tx, ty))
            
            attempt += 1 