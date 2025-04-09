from typing import Optional
from enum import Enum
from tiled_master.framework.element import MapElement
from tiled_master.framework.map_cache import MapCache
import tiled_master.framework.config as config
from tiled_master.utils.logger import logger
from tiled_master.framework.config import place_holder_tile_path

class CoverElement(MapElement):
    """
    Cover element responsible for generating cover layer on the map.
    Scans all layers on the map and generates a new cover layer based on tile cover properties.
    """
    
    class Resources(Enum):
        """Base class for resource ID definitions."""
        COVER_TILES = "cover_tiles"
        COVER_TILE = "cover_tile"
    
    def __init__(self, name: str = "Cover Element", **data):
        super().__init__(name=name, **data)
    
    def _setup_resources(self):
        """Set up resources required for the cover element"""
        # Add a simple tile group containing a tile for cover representation
        tile_group = self._add_tile_group(CoverElement.Resources.COVER_TILES.value, scale=1)
        # Add cover tile using cover image path
        tile_group.add_tile(CoverElement.Resources.COVER_TILE.value, place_holder_tile_path, cover=True)
    
    async def build(self, map_cache: MapCache):
        """
        Build cover layer by generating unified cover information based on all map layers
        
        Args:
            map_cache: Map cache instance
        """
        logger.info("Generating cover layer")
        
        # Check if the specified cover layer is within valid range
        if not (0 <= config.cover_layer < map_cache.layer_nums):
            raise IndexError("Specified cover layer is out of map bounds")
        
        # Clear the cover layer used for cover data
        map_cache.clear_layer(config.cover_layer)
        
        # Get preloaded cover tile resource
        cover_tileset = self.loaded_resources[CoverElement.Resources.COVER_TILES.value]
        cover_texture = cover_tileset.textures[0]
        
        # Set cover tile index
        map_cache.set_cover_idx(cover_texture.tileset_id, cover_texture.local_id)
        
        # Iterate through each position on the map
        for y in range(map_cache.height):
            for x in range(map_cache.width):
                # Check from the top layer down
                for layer in reversed(range(map_cache.layer_nums)):
                    # Check if this layer's tile is non-empty
                    if map_cache.tile_data[layer, y, x, 1] != 0:
                        # Found the topmost non-empty tile, check if it has cover property
                        if map_cache.check_cover(x, y, layer):
                            self._place_tile(map_cache, x, y, config.cover_layer, cover_texture)
                        # No need to check lower layers after finding the first non-empty tile
                        break
        
        logger.info("Cover layer generation completed")
    
    def _place_tile(self, map_cache: MapCache, x: int, y: int, layer: int, texture):
        """Place cover tile at the specified position"""
        map_cache.tile_data[layer, y, x, 0] = texture.tileset_id
        map_cache.tile_data[layer, y, x, 1] = texture.local_id 