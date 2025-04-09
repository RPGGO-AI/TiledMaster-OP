from copy import deepcopy
from enum import Enum
from typing import Optional

from tiled_master.methods import KMST
import implement.town_impl.config as config
from tiled_master import MapElement, MapCache
from tiled_master.schema import *
from tiled_master.config import place_holder_texture
from tiled_master.methods import Pathfinder
from tiled_master.utils.logger import logger


class Village(MapElement):
    """
    Town element that places buildings in a village layout with connecting roads.
    """
    class Resources(Enum):
        SPEC_BUILDINGS = "spec_buildings"
        DEFAULT_BUILDINGS = "default_buildings"
        ROAD = "road"
        BRIDGE = "bridge"
    
    def __init__(self, 
                 name: str, 
                 width: int, 
                 height: int, 
                 num_nodes: int,
                 descriptors: Optional[dict] = None):
        """Initialize the town element"""
        self.width = width
        self.height = height
        self.num_nodes = num_nodes
        self.extra_count = 4
        self.edges = []
        self.nodes = []  # Store location and size information of all buildings
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
        
        # Generate houses with maximum attempts
        max_attempts = 50
        attempt = 0
        
        # Get the building resources
        spec_buildings = self.loaded_resources.get(self.Resources.SPEC_BUILDINGS.value)
        default_buildings = self.loaded_resources.get(self.Resources.DEFAULT_BUILDINGS.value)
        
        while attempt <= max_attempts:
            temp_map_cache = map_cache.create_copy(attempt)
            self._generate_houses(temp_map_cache, spec_buildings, default_buildings)
            self._build_kmst_from_nodes(temp_map_cache)
            if len(self.nodes) == 1 or self.edges is not None:
                map_cache.assign(temp_map_cache)
                break
            else:
                attempt += 1
                logger.warning(f"failed to generate connections for nodes, refreshing the nodes position to retry, trytimes={attempt}")

        # Generate roads connecting the buildings
        road = self.loaded_resources.get(self.Resources.ROAD.value)
        bridge = self.loaded_resources.get(self.Resources.BRIDGE.value)
        
        if road is not None and self.edges is not None:
            self._generate_roads(map_cache, self.edges,road, bridge)
        
        logger.info("generate town done")

    def _build_kmst_from_nodes(self, map_cache: MapCache):
        """Build a K-Minimum Spanning Tree from building nodes"""
        self.edges = []
        connection_points = [node.get("connection_hook") for node in self.nodes]
        self.edges = KMST(connection_points, extra_count=2, random_seed=map_cache.random_seed).generate_connections()

    def _generate_house(self, map_cache: MapCache, obj_texture: TextureObject):
        """Generate a single house from a TextureObject"""
        # Check if the object is valid
        if not obj_texture or not hasattr(obj_texture, 'width') or not hasattr(obj_texture, 'height'):
            logger.error("Invalid object texture for house generation")
            return None
        
        # Calculate random position
        house_width = obj_texture.width
        house_height = obj_texture.height
        width_shift = self.width // 10
        height_shift = self.height // 20
        x = int(map_cache.rand.uniform(width_shift, self.width - width_shift - house_width))
        y = int(map_cache.rand.uniform(height_shift, self.height - height_shift - house_height))
        
        # Check if the position is available
        if not self._can_place_house(map_cache, x, y, house_width, house_height):
            return None
        
        # Place object
        if map_cache.drop_object(x, y, config.house_layer, obj_texture, add_to_items=True):
            # Generate building base for road collision detection
            for tx in range(x, x + house_width):
                for ty in range(y + 2, y + house_height):
                    map_cache.drop_tile(tx, ty, config.structure_layer, place_holder_texture)
            
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
        """Check if a house can be placed at the specified location"""
        # Check if it exceeds map boundaries
        if (x < 0 or y < 0 or 
            x + width > map_cache.width or 
            y + height > map_cache.height):
            return False
        
        # Check for overlap with water, trees, or other buildings
        for tx in range(x, x + width):
            for ty in range(y, y + height):
                if (map_cache.check_exists(tx, ty, config.water_layer) or
                    map_cache.check_exists(tx, ty, config.tree_layer) or
                    map_cache.check_exists(tx, ty, config.house_layer)):
                    return False
        
        return True

    def _generate_house_with_spec(self, map_cache, spec_buildings, default_buildings):
        """Generate a house with either specified or default building style"""
        # First, try to generate specified nodes
        if spec_buildings and spec_buildings.textures:
            spec_node = spec_buildings.textures[0]
            new_node = self._generate_house(
                map_cache,
                spec_node
            )
            return new_node
        else:
            if default_buildings and default_buildings.textures:
                default_node = map_cache.rand.choice(default_buildings.textures)
                return self._generate_house(map_cache, default_node)
        return None

    def _generate_houses(self, map_cache, spec_buildings, default_buildings):
        """Generate multiple houses within the town area"""
        max_attempts = max(map_cache.width * map_cache.height // 40, 20)
        self.nodes = []
        spec_buildings_copy = deepcopy(spec_buildings.textures) if spec_buildings else []
        attempts = 0

        while (len(self.nodes) < self.num_nodes
               and attempts < max_attempts):
            temp_map_cache = map_cache.create_copy(attempts)
            attempts += 1
            
            # Create a temporary spec_buildings object for _generate_house_with_spec
            temp_spec = ObjectGroup(name="temp_spec", type="object_group", textures=spec_buildings_copy) if spec_buildings_copy else None
            
            new_node = self._generate_house_with_spec(temp_map_cache, temp_spec, default_buildings)
            if new_node:
                self.nodes.append(new_node)
                map_cache.assign(temp_map_cache)
                if spec_buildings_copy:
                    logger.debug(f"popped {spec_buildings_copy[0].name}, left {len(spec_buildings_copy) - 1} nodes")
                    spec_buildings_copy.pop(0)
                logger.debug(f"generate house {new_node['width']}x{new_node['height']} at ({new_node['x']},{new_node['y']})")

        if len(self.nodes) < self.num_nodes:
            logger.warning(f"Warning: Only placed {len(self.nodes)} nodes out of {self.num_nodes} due to overlap constraints.")
    
    def _generate_roads(self, map_cache, edges, road_model, bridge_model):
        """Generate roads connecting the corners"""
        logger.info("generating roads")

        corridor_positions = []
        self.road_tiles = []
        
        for edge in edges:
            start = edge[0]
            goal = edge[1]
            paths = Pathfinder(map_cache, self.width, self.height).find_corridor_path(start, goal, [config.structure_layer])
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
