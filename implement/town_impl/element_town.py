from copy import deepcopy
from enum import Enum
from typing import List, Tuple, Optional, Dict, Any

from tiled_master.methods import KMST, BSP, Pathfinder

from tiled_master import MapElement, MapCache  
from tiled_master.schema import *

from tiled_master.utils.logger import logger, logger_runtime

import implement.town_impl.config as config

class Town(MapElement):
    """
    Town element that places buildings along roads in a city layout.
    """
    class Resources(Enum):
        SPEC_BUILDINGS = "spec_buildings"
        DEFAULT_BUILDINGS = "default_buildings"
        ROAD = "road"
        BRIDGE = "bridge"
    
    def __init__(self, 
                 name: str,
                 num_nodes: int,
                 descriptors: Optional[dict] = None):
        """Initialize the town element"""
        self.num_nodes = num_nodes
        self.extra_count = 2
        self.nodes = []  # Store position and size information of all buildings
        self.road_tiles = []  # Store road tile positions
        self.map_width = 0
        self.map_height = 0
        self.width_shift = 0
        self.height_shift = 0
        self.width = 0
        self.height = 0
        super().__init__(name=name, descriptors=descriptors)
    
    def _setup_resources(self):
        """Setup the required resources for town generation"""
        self._add_object_group(self.Resources.SPEC_BUILDINGS.value)
        self._add_object_group(self.Resources.DEFAULT_BUILDINGS.value)
        self._add_tile_group(self.Resources.ROAD.value)
        self._add_tile_group(self.Resources.BRIDGE.value)
    
    async def build(self, map_cache: MapCache):
        """Build the town on the map"""
        logger.info("generating town")
        
        # Initialize map dimensions
        self.map_width = map_cache.width
        self.map_height = map_cache.height
        self.width_shift = self.map_width // 10 + map_cache.rand.randint(-5, 5)
        self.height_shift = self.map_height // 10 + map_cache.rand.randint(-3, 3)
        self.width = self.map_width*9//10 + map_cache.rand.randint(-5, 5) - self.width_shift
        self.height = self.map_height*9//10 + map_cache.rand.randint(-3, 3) - self.height_shift
        
        logger.info(f"init city with scale: {self.width_shift, self.height_shift, self.width, self.height}")
        
        # Get resources
        road_model = self.loaded_resources.get(self.Resources.ROAD.value)
        bridge_model = self.loaded_resources.get(self.Resources.BRIDGE.value)
        spec_buildings = self.loaded_resources.get(self.Resources.SPEC_BUILDINGS.value)
        default_buildings = self.loaded_resources.get(self.Resources.DEFAULT_BUILDINGS.value)
        
        if road_model is not None:
            # Generate road map
            road_tiles = self._generate_road_map(map_cache, road_model, bridge_model)
            if road_tiles:
                # Generate houses along road
                self._generate_houses_along_edge(map_cache, spec_buildings, default_buildings, road_tiles)
                logger.info("generate town done")
            else:
                logger.warning("generate town failed: couldn't generate roadmap")
        else:
            logger.warning("no road no town")
        
    
    def _generate_road_map(self, map_cache, road_model, bridge_model, max_attempts=50):
        """Generate road map using BSP and KMST"""
        attempt = 0
        while attempt <= max_attempts:
            temp_map_cache = map_cache.create_copy(attempt)
            """region: (x, y, width, height)"""
            road_scale = road_model.scale
            logger.info(f"generate roadmap at scale {road_scale}")
            road_scale = 2 if road_scale == -1 else road_scale
            bsp_size = 12 - road_scale*2
            regions, corners = BSP(min_size=bsp_size, random_seed=temp_map_cache.random_seed)(
                (self.width_shift, self.height_shift, self.width, self.height), 
                temp_map_cache.width, 
                temp_map_cache.height
            )
            corners = self._remove_corner_on_water(temp_map_cache, corners)
            edges = self._build_kmst_from_corners(corners, map_cache)
            
            if edges is not None:
                map_cache.assign(temp_map_cache)
                self._generate_roads(map_cache, edges, road_model, bridge_model)
                return self.road_tiles
            else:
                attempt += 1
                logger.info(f"failed to generate connections for nodes, refreshing the nodes position to retry, trytimes={attempt}, random_seed={temp_map_cache.random_seed}")
        return None
    
    def _build_kmst_from_corners(self, corners, map_cache: MapCache):
        """Build a K-Minimum Spanning Tree from corners"""
        return KMST(corners, extra_count=self.extra_count, random_seed=map_cache.random_seed).generate_connections()
    
    def _remove_corner_on_water(self, map_cache, corners: List[Tuple[int, int]]):
        """Check if out-of-bounds nodes are on water"""
        new_corners = []
        for corner in corners:
            cx, cy = corner
            cx_code = -1 if cx < 0 else (1 if cx >= map_cache.width else 0)
            cy_code = -1 if cy < 0 else (1 if cy >= map_cache.height else 0)
            position_mapping = {
                (-1, -1): (0, 0),
                (-1, 0): (0, cy),
                (-1, 1): (0, map_cache.height - 1),
                (0, -1): (cx, 0),
                (0, 0): (cx, cy),
                (0, 1): (cx, map_cache.height - 1),
                (1, -1): (map_cache.width - 1, 0),
                (1, 0): (map_cache.width - 1, cy),
                (1, 1): (map_cache.width - 1, map_cache.height - 1),
            }
            x, y = position_mapping[(cx_code, cy_code)]
            if not map_cache.check_exists(x, y, config.water_layer):
                new_corners.append(corner)
        return new_corners
    
    def _generate_roads(self, map_cache, edges, road_model, bridge_model):
        """Generate roads connecting the corners"""
        logger.info("generating roads")

        corridor_positions = []
        self.road_tiles = []
        
        for edge in edges:
            start = edge[0]
            goal = edge[1]
            paths = Pathfinder(map_cache, self.map_width, self.map_height).find_corridor_path(start, goal, [config.structure_layer])
            corridor_positions.extend(paths)
            # Record path information for generating buildings along the road
            self.road_tiles.extend([(x, y, 1) for x, y in paths])

        if len(road_model.textures) > 0 and len(bridge_model.textures) > 0:
            bridge_area = []
            for x, y in corridor_positions:
                if map_cache.check_exists(x, y, config.water_layer):
                    bridge_area.append((x, y))

            corridor_positions_set = set(corridor_positions)
            bridge_area_set = set(bridge_area)
            road_area = list(corridor_positions_set - bridge_area_set)
            # Create a temporary copy for merging results
            final_map_cache = map_cache.create_copy()
            # Process roads
            road_temp_cache = map_cache.create_copy()
            self._drop_to_temp_layer_from_tilegroup(road_temp_cache, road_model, config.road_layer, road_area)
            final_map_cache.merge_layer_from(road_temp_cache, config.road_layer, config.road_layer)
            # Process bridges
            bridge_temp_cache = map_cache.create_copy()
            self._drop_to_temp_layer_from_tilegroup(bridge_temp_cache, bridge_model, config.road_layer, bridge_area)
            final_map_cache.merge_layer_from(bridge_temp_cache, config.road_layer, config.road_layer)
        
            # Assign the merged result back to map_cache
            map_cache.assign(final_map_cache)
        elif len(road_model.textures) > 0:
            map_cache.drop_tiles_from_tilegroup(road_model, corridor_positions, config.road_layer)
        else:
            raise Exception("no road model")
    
    def _drop_to_temp_layer_from_tilegroup(self, temp_cache, tile_group, target_layer, positions):
        """Helper method to drop tiles to a temporary map_cache from a tile group"""
        temp_cache.drop_tiles_from_tilegroup(tile_group, positions, target_layer)
    
    def _generate_house_along_edge(self, map_cache, obj_texture: TextureObject, edge_x, edge_y):
        """Generate a single house along an edge from a texture object"""
        # Check if the object is valid
        if not obj_texture or not hasattr(obj_texture, 'width') or not hasattr(obj_texture, 'height'):
            logger.error("Invalid object texture for house generation")
            return None
        
        house_width = obj_texture.width
        house_height = obj_texture.height
        
        # Define 4 anchor point offsets to try (relative to edge_x, edge_y)
        dis_offset = 1
        offsets = [
            # right
            (1, 1, 0, 0 + dis_offset, -house_height // 2),
            # bottom
            (2, 0, 1, -house_width // 2, 0 + dis_offset),
            # top
            (3, 0, -1, -house_width // 2, -house_height + 1 - dis_offset),
            # left
            (4, -1, 0, -house_width + 1 - dis_offset, -house_height // 2)
        ]
        
        # Try 4 different placement methods
        for attempt, shift_x, shift_y, offset_x, offset_y in offsets:
            temp_map_cache = map_cache.create_copy(attempt)
            x = edge_x + offset_x
            y = edge_y + offset_y
            checkpoint_x = edge_x + shift_x
            checkpoint_y = edge_y + shift_y
            
            # Check if key points are already occupied
            if (map_cache.check_exists(checkpoint_x, checkpoint_y, config.house_layer) or
                map_cache.check_exists(checkpoint_x, checkpoint_y, config.road_layer)):
                continue
            
            # Check if the position is available
            if not self._can_place_house(map_cache, x, y, house_width, house_height):
                continue
            
            # Place object
            if temp_map_cache.drop_object(x, y, config.house_layer, obj_texture, add_to_items=True):
                map_cache.assign(temp_map_cache)
                
                # Save building information
                house_info = {
                    "x": x, 
                    "y": y, 
                    "width": house_width, 
                    "height": house_height,
                    "connection_hook": (x + house_width // 2, y + house_height + 1)
                }
                return house_info
            
        return None
    
    def _can_place_house(self, map_cache, x, y, width, height):
        """Check if a building can be placed at the specified location"""
        # Check if it's outside the map boundaries
        if (x < 0 or y < 0 or 
            x + width > map_cache.width or 
            y + height > map_cache.height):
            return False
        
        # Check for overlap with water, road, or other buildings
        for tx in range(x, x + width):
            for ty in range(y, y + height):
                if (map_cache.check_exists(tx, ty, config.water_layer) or
                    map_cache.check_exists(tx, ty, config.road_layer) or 
                    map_cache.check_exists(tx, ty, config.house_layer)):
                    return False
        
        return True
    
    def _generate_house_with_spec(self, map_cache, spec_buildings, default_buildings, edge_x, edge_y):
        """Generate a house with either specified or default building style"""
        # First, try to generate specified nodes
        if spec_buildings and spec_buildings.textures:
            spec_node = spec_buildings.textures[0]
            new_node = self._generate_house_along_edge(map_cache, spec_node, edge_x, edge_y)
            return new_node
        else:
            if default_buildings and default_buildings.textures:
                default_node = map_cache.rand.choice(default_buildings.textures)
                return self._generate_house_along_edge(map_cache, default_node, edge_x, edge_y)
        return None
    
    @logger_runtime()
    def _generate_houses_along_edge(self, map_cache, spec_buildings, default_buildings, edge_tiles):
        """Generate houses along the edges of roads"""
        spec_buildings_copy = deepcopy(spec_buildings.textures) if spec_buildings else []
        edge_list = []
        
        # Filter valid edge positions
        for (x, y, l) in edge_tiles:
            if 0 <= x < map_cache.width and 0 < y <= map_cache.height:
                edge_list.append((x, y))
        
        attempts = 0
        self.nodes = []
        
        # Generate buildings
        while len(self.nodes) < self.num_nodes and edge_list:
            attempts += 1
            temp_map_cache = map_cache.create_copy(attempts)
            edge_x, edge_y = edge_list.pop(0)
            
            # Create temporary object group for _generate_house_with_spec
            temp_spec = ObjectGroup(name="temp_spec", type="object_group", textures=spec_buildings_copy) if spec_buildings_copy else None
            
            new_node = self._generate_house_with_spec(temp_map_cache, temp_spec, default_buildings, edge_x, edge_y)
            if new_node:
                self.nodes.append(new_node)
                map_cache.assign(temp_map_cache)
                if spec_buildings_copy:
                    logger.info(f"popped {spec_buildings_copy[0].name}, left {len(spec_buildings_copy) - 1} nodes")
                    spec_buildings_copy.pop(0)
                logger.debug(f"generate house {new_node['width']}x{new_node['height']} at ({new_node['x']},{new_node['y']})")
        
        if len(self.nodes) < self.num_nodes:
            logger.warning(f"Warning: Only placed {len(self.nodes)} nodes out of {self.num_nodes} due to overlap constraints.") 