from typing import Optional
from enum import Enum
from tiled_master.framework.element import MapElement
from tiled_master.framework.map_cache import MapCache
import tiled_master.framework.config as config
from tiled_master.utils.logger import logger
from tiled_master.framework.config import place_holder_tile_path

class CollisionElement(MapElement):
    """
    Collision element responsible for generating collision layer on the map.
    Scans all layers on the map and generates a new collision layer based on tile collision properties.
    """

    class Resources(Enum):
        """Base class for resource ID definitions."""
        COLLISION_TILES = "collision_tiles"
        COLLISION_TILE = "collision_tile"
    
    def __init__(self, name: str = "Collision Element", **data):
        super().__init__(name=name, **data)
    
    def _setup_resources(self):
        """Set up resources required for the collision element"""
        # Add a simple tile group containing a tile for collision representation
        tile_group = self._add_tile_group(CollisionElement.Resources.COLLISION_TILES.value, scale=1)
        # Add collision tile using collision image path
        tile_group.add_tile(CollisionElement.Resources.COLLISION_TILE.value, place_holder_tile_path, collision=True)
    
    async def build(self, map_cache: MapCache):
        """
        Build collision layer by generating unified collision information based on all map layers
        
        Args:
            map_cache: Map cache instance
        """
        logger.info("Generating collision layer")
        
        # Check if the specified collision layer is within valid range
        if not (0 <= config.obstacle_layer < map_cache.layer_nums):
            raise IndexError("Specified collision layer is out of map bounds")
        
        # Clear the obstacle layer used for collision data
        map_cache.clear_layer(config.obstacle_layer)
        
        # Get preloaded collision tile resource
        collision_tileset = self.loaded_resources[CollisionElement.Resources.COLLISION_TILES.value]
        collision_texture = collision_tileset.textures[0]
        
        # Set collision tile index
        map_cache.set_collision_idx(collision_texture.tileset_id, collision_texture.local_id)
        
        # Iterate through each position on the map
        for y in range(map_cache.height):
            for x in range(map_cache.width):
                # Check from the top layer down
                for layer in reversed(range(map_cache.layer_nums)):
                    # Check if this layer's tile is non-empty
                    if map_cache.tile_data[layer, y, x, 1] != 0:
                        # Found the topmost non-empty tile, check if it has collision property
                        if map_cache.check_collision(x, y, layer):
                            self._place_tile(map_cache, x, y, config.obstacle_layer, collision_texture)
                        # No need to check lower layers after finding the first non-empty tile
                        break
                    # If we've reached the bottom layer and it's empty, add collision
                    elif layer == 0 and map_cache.tile_data[layer, y, x, 1] == 0:
                        self._place_tile(map_cache, x, y, config.obstacle_layer, collision_texture)
        
        logger.info("Collision layer generation completed")
    
    def _place_tile(self, map_cache: MapCache, x: int, y: int, layer: int, texture):
        """Place collision tile at the specified position"""
        map_cache.tile_data[layer, y, x, 0] = texture.tileset_id
        map_cache.tile_data[layer, y, x, 1] = texture.local_id 