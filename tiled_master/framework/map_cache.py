import random
from typing import Tuple, List, Set
from copy import deepcopy
import numpy as np
import tiled_master.framework.config as static_config
from tiled_master.framework.schema import *
from tiled_master.framework.object import ItemLayer, Object
from tiled_master.utils.logger import logger
from collections import deque
from tiled_master.utils.utils import stable_hash


class MapCache:
    """
    MapCache class manages the map data for a tile-based game.
    It handles tile storage, manipulation, collision detection, and other map-related operations.
    """
    def __init__(self, map_id: str, width: int, height: int, layer_nums: int):
        """
        Initialize a new map cache with specified dimensions.
        
        Args:
            map_id: Unique identifier for the map
            width: Width of the map in tiles
            height: Height of the map in tiles
        """
        self.map_id = map_id
        self.random_seed = stable_hash(map_id)
        logger.info(f"init map with seed {self.random_seed}")
        self.rand = random.Random(self.random_seed)
        self.width = width
        self.height = height
        self.layer_nums = layer_nums
        # tile_data: 4D array [layer, y, x, 4], 4 stores (tileset_idx, local_id, collide, cover)
        self.tile_data = np.zeros((self.layer_nums, self.height, self.width, 4))
        self.itemlayer = ItemLayer(layer_id=static_config.item_layer, name="Items")
        self.collision_idx = (0, 0)
        self.cover_idx = (0, 0)

    def assign(self, other: 'MapCache'):
        """
        Copy all properties from another MapCache instance to this one.
        
        Args:
            other: The source MapCache instance to copy from
        
        Raises:
            TypeError: If other is not an instance of MapCache
        """
        if not isinstance(other, MapCache):
            raise TypeError("The object to assign must be an instance of MapCache.")

        self.width = other.width
        self.height = other.height
        self.layer_nums = other.layer_nums
        self.random_seed = other.random_seed
        self.rand = random.Random()
        self.rand.setstate(other.rand.getstate())
        self.tile_data = np.copy(other.tile_data)
        self.itemlayer = deepcopy(other.itemlayer)
        self.collision_idx = other.collision_idx
        self.cover_idx = other.cover_idx

    def create_copy(self, attempts: int = 0) -> 'MapCache':
        """
        Create a new copy of the MapCache with a modified random seed.
        
        Args:
            attempts: Number to modify the random seed, useful for creating variations
            
        Returns:
            A new MapCache instance with the same properties but different seed
        """
        # Create a new MapCache with a modified random seed based on attempts
        new_cache = MapCache.__new__(MapCache)
        new_cache.map_id = self.map_id
        new_cache.random_seed = stable_hash(str((self.random_seed, attempts)))
        new_cache.rand = random.Random(new_cache.random_seed)
        new_cache.width = self.width
        new_cache.height = self.height
        new_cache.layer_nums = self.layer_nums
        new_cache.tile_data = np.copy(self.tile_data)
        new_cache.itemlayer = deepcopy(self.itemlayer)
        new_cache.collision_idx = self.collision_idx
        new_cache.cover_idx = self.cover_idx
        return new_cache

    def set_cover_idx(self, tileset_id, local_id):
        """
        Set the default cover tile index.
        
        Args:
            tileset_id: ID of the tileset
            local_id: Local ID within the tileset
        """
        self.cover_idx = (tileset_id, local_id)

    def set_collision_idx(self, tileset_id, local_id):
        """
        Set the default collision tile index.
        
        Args:
            tileset_id: ID of the tileset
            local_id: Local ID within the tileset
        """
        self.collision_idx = (tileset_id, local_id)

    def set_tile(self, x: int, y: int, layer: int, tile: Tuple[int, int, int, int]):
        """
        Set tile data in the map_cache, similar to the previous set_tile function.
        
        Args:
            x: X coordinate of the tile
            y: Y coordinate of the tile
            layer: Layer index
            tile: Tuple of (tileset_id, local_id, collision, cover)
        """
        if (0 <= layer < self.layer_nums) and (0 <= y < self.height) and (0 <= x < self.width):
            self.tile_data[layer, y, x, 0] = tile[0]
            self.tile_data[layer, y, x, 1] = tile[1]
            self.tile_data[layer, y, x, 2] = tile[2]
            self.tile_data[layer, y, x, 3] = tile[3]
        else:
            pass

    def drop_tile(self, x: int, y: int, layer: int, tile_config: TextureTile):
        """
        Place a tile at the specified position using a TextureTile configuration.
        
        Args:
            x: X coordinate
            y: Y coordinate
            layer: Layer index
            tile_config: TextureTile object containing tile properties
            
        Returns:
            True if successful, False if coordinates are out of bounds
        """
        tileset_id = tile_config.tileset_id
        local_id = tile_config.local_id
        collision = 1 if tile_config.collision else 0
        cover = 1 if tile_config.cover else 0
        if 0 <= x < self.width and 0 <= y < self.height:
            self.set_tile(x, y, layer, (tileset_id, local_id, collision, cover))
            return True
        else:
            return False


    def get_tile(self, x: int, y: int, layer: int):
        """
        Get tile data at the specified position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            layer: Layer index
            
        Returns:
            Tuple of (tileset_id, local_id, collision, cover)
        """
        if not (0 <= layer < self.layer_nums and 0 <= y < self.height and 0 <= x < self.width):
            return 0, 0, 0, 0
        ts_idx = self.tile_data[layer, y, x, 0]
        local_id = self.tile_data[layer, y, x, 1]
        collision = self.tile_data[layer, y, x, 2]
        cover = self.tile_data[layer, y, x, 3]
        return ts_idx, local_id, collision, cover

    def clear_tile(self, x: int, y: int, layer: int):
        """
        Clear a tile at the specified position by setting it to zero.
        
        Args:
            x: X coordinate
            y: Y coordinate
            layer: Layer index
        """
        if not (0 <= layer < self.layer_nums and 0 <= y < self.height and 0 <= x < self.width):
            return
        self.tile_data[layer, y, x] = 0

    def clear_layer(self, layer: int) -> None:
        """
        Clear all tiles from the specified layer.
        
        Args:
            layer: Layer index to clear
        """
        if 0 <= layer < self.layer_nums:
            self.tile_data[layer] = 0  # Clear the layer
            logger.info(f"Cleared all tiles from layer {layer}")
        else:
            pass

    def get_layer(self, layer: int) -> List[Tuple[int, int]]:
        """
        Get coordinates of all non-empty tiles in the specified layer.
        
        Args:
            layer: Layer index
            
        Returns:
            List of (x, y) coordinates for non-empty tiles
            
        Raises:
            IndexError: If layer is out of bounds
        """
        if not (0 <= layer < self.layer_nums):
            raise IndexError("Layer out of bounds")

        non_empty_tiles = np.argwhere(self.tile_data[layer, :, :, 1] > 0)
        return [(x, y) for y, x in non_empty_tiles]

    def get_neighbors(self, x: int, y: int, layer: int, radius: int = 1) -> List[Tuple[int, int]]:
        """
        Get coordinates of neighboring tiles within the specified radius.
        
        Args:
            x: X coordinate of the center tile
            y: Y coordinate of the center tile
            layer: Layer index
            radius: Search radius (default: 1)
            
        Returns:
            List of (x, y) coordinates for neighboring tiles
            
        Raises:
            IndexError: If coordinates or layer are out of bounds
        """
        if not (0 <= layer < self.layer_nums):
            raise IndexError("Layer out of bounds")
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise IndexError("Coordinates out of bounds")

        neighbors = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if self.check_exists(nx, ny, layer):
                        neighbors.append((nx, ny))
        return neighbors

    def check_collision(self, x: int, y: int, layer: int) -> bool:
        """
        Check if a tile has collision enabled.
        
        Args:
            x: X coordinate
            y: Y coordinate
            layer: Layer index
            
        Returns:
            True if the tile has collision, False otherwise
        """
        tileset_id, local_id, collision, cover = self.get_tile(x, y, layer)
        return bool(collision)

    def check_cover(self, x: int, y: int, layer: int) -> bool:
        """
        Check if a tile has cover enabled.
        
        Args:
            x: X coordinate
            y: Y coordinate
            layer: Layer index
            
        Returns:
            True if the tile has cover, False otherwise
        """
        tileset_id, local_id, collision, cover = self.get_tile(x, y, layer)
        return bool(cover)

    def check_exists(self, x: int, y: int, layer: int) -> bool:
        """
        Check if a non-empty tile exists at the specified position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            layer: Layer index
            
        Returns:
            True if a tile exists, False otherwise
            
        Raises:
            Exception: If tileset_id is 0 but local_id is not 0 (invalid state)
        """
        ts_idx, local_id, _, _ = self.get_tile(x, y, layer)
        if local_id == 0:
            return False
        else:
            if ts_idx == 0:
                raise Exception("ts_idx should not be 0 while local id is not 0, check the code")
            return True

    def drop_tiles_from_tilegroup(self, tilegroup: TileGroup, drop_area: List[Tuple[int, int]], target_layer: int) -> None:
        """
        Place tiles from a tile group onto the map in the specified area.
        
        Args:
            tilegroup: TileGroup containing tile textures
            drop_area: List of (x, y) coordinates to place tiles
            target_layer: Layer index to place tiles on
        """
        tile_textures = []
        autotile_texture = None

        textures = tilegroup.textures
        for texture in textures:
            if texture.type == "tile":
                tile_textures.extend([texture] * texture.rate)
            if texture.type == "autotile":
                autotile_texture = texture

        if tile_textures:
            for (x, y) in drop_area:
                tile_texture = self.rand.choice(tile_textures)
                self.drop_tile(x, y, target_layer, tile_texture)

        if autotile_texture is not None:
            from tiled_master.framework.autotile import AutoTile  # Avoid circular import
            autotile = AutoTile(autotile_texture.method)
            if not tile_textures:
                for (x, y) in drop_area:
                    base_texture_local_id = autotile.get_base_tile_local_id()
                    tile_texture = TextureTile(
                        name=f"{autotile_texture.name}_{base_texture_local_id}",
                        collision=autotile_texture.collision,
                        cover=autotile_texture.cover,
                        tileset_id=autotile_texture.tileset_id,
                        local_id=base_texture_local_id
                    )
                    self.drop_tile(x, y, target_layer, tile_texture)
            # Note: Edge variants must be processed after the block has been assigned values to detect edge states
            for (x, y) in drop_area:
                local_id = autotile.get_autotile_local_id(self, x, y, target_layer)
                if local_id:
                    tile_texture = TextureTile(
                        name=f"{autotile_texture.name}_{local_id}",
                        collision=autotile_texture.collision,
                        cover=autotile_texture.cover,
                        tileset_id=autotile_texture.tileset_id,
                        local_id=local_id
                    )
                    self.drop_tile(x, y, target_layer, tile_texture)

    def drop_objects_from_objectgroup(self, objectgroup: ObjectGroup, drop_area: List[Tuple[int, int]], target_layer: int, add_to_items: bool = True) -> None:
        """
        Place objects from an object group onto the map in the specified area.
        
        Args:
            objectgroup: ObjectGroup containing object textures
            drop_area: List of (x, y) coordinates to place objects
            target_layer: Layer index to place objects on
            add_to_items: Whether to add objects to item layer (default: True)
        """
        object_textures = []
        
        textures = objectgroup.textures
        for texture in textures:
            object_textures.extend([texture] * texture.rate)
            
        if object_textures:
            for (x, y) in drop_area:
                object_texture = self.rand.choice(object_textures)
                self.drop_object(x, y, target_layer, object_texture, add_to_items)

    def drop_object(self, x: int, y: int, layer: int, object_texture: TextureObject, add_to_items: bool = False) -> bool:
        """
        Place an object onto the map at the specified position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            layer: Layer index
            object_texture: TextureObject to place
            
        Returns:
            True if successful, False otherwise
        """
        temp_map_cache = self.create_copy()
        for blueprint in object_texture.blueprints:
            # Currently only supports relative_o = "left_top", absolute position = (x + relative_x, y + relative_y)
            abs_x = x + blueprint.relative_x
            abs_y = y + blueprint.relative_y
            if not temp_map_cache.drop_tile(abs_x, abs_y, layer, blueprint.texture):
                return False
        self.assign(temp_map_cache)

        if add_to_items:
            logger.debug(f"add object to items: {object_texture.name}")
            obj = Object(
                obj_id=0,
                name=object_texture.name,
                type_=object_texture.type,
                x=x*static_config.tile_width,
                y=y*static_config.tile_height,
                original_width=object_texture.original_width,
                original_height=object_texture.original_height,
                width=object_texture.width*static_config.tile_width,
                height=object_texture.height*static_config.tile_height,
                functions=object_texture.functions,
                rotation=object_texture.rotation,
                visible=object_texture.visible,
                image=object_texture.image_url,
                image_path=object_texture.image_path
            )
            self.add_object_to_items(obj)
        return True
    
    def flood_fill_to_edge(self, start_x: int, start_y: int, layer: int) -> bool:
            """
            Perform flood fill from the starting point to check if it can reach the map edge.
            
            Args:
                start_x: X coordinate of the starting point
                start_y: Y coordinate of the starting point
                layer: Layer index
                
            Returns:
                True if the fill can reach the map edge, False otherwise
                
            Raises:
                IndexError: If coordinates or layer are out of bounds
            """
            # Check if the starting point is valid
            if not (0 <= layer < self.layer_nums):
                raise IndexError("Layer out of bounds")
            if not (0 <= start_x < self.width and 0 <= start_y < self.height):
                raise IndexError("Coordinates out of bounds")

            # Check if the starting point is not empty
            if self.get_tile(start_x, start_y, layer)[0] != 0:
                print("case1")
                return True

            # Create queue and visited set
            queue = deque([(start_x, start_y)])
            visited = set()
            visited.add((start_x, start_y))

            # Define eight directions (up, down, left, right, and four diagonals)
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

            while queue:
                x, y = queue.popleft()

                # If reached the edge, return True
                if x == 0 or x == self.width - 1 or y == 0 or y == self.height - 1:
                    print("case0")
                    return True

                # Check adjacent cells
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height and (nx, ny) not in visited:
                        # If the current cell is empty, continue filling
                        if self.get_tile(nx, ny, layer)[0] == 0:
                            queue.append((nx, ny))
                            visited.add((nx, ny))

            # If all reachable points have been traversed without reaching the edge, return False
            print("case2")
            return False

    def add_object_to_items(self, obj: Object):
        """
        Add an object to the item layer.
        
        Args:
            obj: Object to add to the item layer
        """
        self.itemlayer.add_object(obj)

    def merge_layer_from(self, source_map_cache: 'MapCache', source_layer: int, target_layer: int, 
                        only_non_zero: bool = True, region: Tuple[int, int, int, int] = None) -> bool:
        """
        Merge a layer from source map_cache to the target layer in this map_cache.
        
        Args:
            source_map_cache: Source MapCache object
            source_layer: Layer index in the source map
            target_layer: Layer index in this map
            only_non_zero: If True, only merge non-zero tiles (default: True)
            region: Optional merge region as (start_x, start_y, width, height)
            
        Returns:
            True if successful, False otherwise
        """
        if not (0 <= source_layer < source_map_cache.layer_nums):
            logger.error(f"Source layer {source_layer} out of bounds")
            return False
            
        if not (0 <= target_layer < self.layer_nums):
            logger.error(f"Target layer {target_layer} out of bounds")
            return False
            
        # Determine merge region
        if region:
            start_x, start_y, width, height = region
            end_x = min(start_x + width, min(source_map_cache.width, self.width))
            end_y = min(start_y + height, min(source_map_cache.height, self.height))
        else:
            start_x, start_y = 0, 0
            end_x = min(source_map_cache.width, self.width)
            end_y = min(source_map_cache.height, self.height)
            
        # Execute merge
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                source_tile = source_map_cache.get_tile(x, y, source_layer)
                
                # Skip if only merging non-zero tiles and source tile is zero
                if only_non_zero and source_tile == (0, 0, 0, 0):
                    continue
                    
                self.set_tile(x, y, target_layer, source_tile)
                
        return True
        
    def create_temp_layer(self) -> 'MapCache':
        """
        Create a new single-layer MapCache as a temporary layer.
        
        Returns:
            A new MapCache instance with a single layer
        """
        temp_id = f"{self.map_id}_temp_{self.rand.randint(0, 10000)}"
        temp_map = MapCache(temp_id, self.width, self.height)
        temp_map.layer_nums = 1  # Use only a single layer
        temp_map.tile_data = np.zeros((1, self.height, self.width, 4))
        return temp_map