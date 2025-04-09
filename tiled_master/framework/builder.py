import os
import json
from typing import List, Dict, Any, Optional
import asyncio

from tiled_master.framework.element import MapElement
from tiled_master.framework.preloader import Preloader
from tiled_master.framework.map_cache import MapCache
from tiled_master.framework.schema import Tileset
import tiled_master.framework.config as static_config
from tiled_master.framework.visualize import visualize_tilemap
from tiled_master.utils.logger import logger, logger_runtime_async


class MapBuilder:
    """
    Builder class for constructing maps with multiple elements.
    
    This class manages the entire map building process, including:
    - Element collection and management
    - Resource preloading
    - Map construction
    """
    
    def __init__(self, map_id: str, width: int = 80, height: int = 40, total_layer: int = 10):
        """
        Initialize the map builder.
        
        Args:
            map_id: Unique identifier for the map
            width: Width of the map in tiles (default: 80)
            height: Height of the map in tiles (default: 40)
        """
        self.map_id = map_id
        self.width = width
        self.height = height
        self.layer_nums = total_layer
        self.elements: List[MapElement] = []
        self.preloader: Optional[Preloader] = None
        self.map_cache: Optional[MapCache] = None
        self.tilesets: Dict[int, Tileset] = {}  # Store tileset information
        
    
    def add_element(self, element: MapElement) -> 'MapBuilder':
        """
        Add a map element to the builder.
        
        Args:
            element: The MapElement instance to add
            
        Returns:
            The builder instance for method chaining
        """
        self.elements.append(element)
        return self
    
    async def preload_resources(self) -> None:
        """
        Preload all resources for all elements.
        Creates a preloader and runs each element's preload method.
        """
        self.preloader = Preloader(self.map_id)
        
        for element in self.elements:
            logger.info(f"Preloading element: {element.name}")
            await element.preload(self.preloader)
        
        # Get tileset information and store it
        tilesets_list = self._get_tilesets_from_preloader()
        self.tilesets = {tileset.tileset_id: tileset for tileset in tilesets_list}
    
    def _get_tilesets_from_preloader(self) -> List[Tileset]:
        """
        Extract tileset information from the preloader.
        Combines dynamic tileset and autotiles.
        """
        if not self.preloader:
            raise RuntimeError("Preloader not initialized. Call preload_resources first.")
        
        # Directly use preloader's process_tilesets method to get all tilesets
        return self.preloader.process_tilesets()
    
    @logger_runtime_async()
    async def build(self) -> MapCache:
        """
        Execute the complete build process:
        1. Preload all elements' resources
        2. Create MapCache directly with parameters
        3. Build all elements into the map
        4. Return the built map cache
        
        Returns:
            The built MapCache
        """
        logger.info(f"Building map '{self.map_id}' ({self.width}x{self.height}) with {len(self.elements)} elements")
        
        # Step 1: Preload all resources
        await self.preload_resources()
        
        # Step 2: Create MAP_CACHE with direct parameters
        self.map_cache = MapCache(
            map_id=self.map_id,
            width=self.width,
            height=self.height,
            layer_nums=self.layer_nums
        )
        
        # Step 3: Build all elements
        for element in self.elements:
            logger.info(f"Building element: {element.name}")
            await element.build(self.map_cache)
        
        logger.info(f"Map '{self.map_id}' built successfully")

    
    def export_map(self) -> str:
        """Export map as JSON file"""
        if not self.map_cache:
            raise RuntimeError("Map not built yet. Call build() first.")
        
        exporter = MapExporter(self.map_id)
        json_path = exporter.export_json(self.map_cache, self.tilesets)
    
        return json_path

    def preview_map(self, display: bool = True) -> str:
        """Generate map preview"""
        if not self.map_cache:
            raise RuntimeError("Map not built yet. Call build() first.")
        
        exporter = MapExporter(self.map_id)
        tilemap_dict = MapExporter._generate_map_data(self.map_cache, self.tilesets)
        return exporter.preview_map(tilemap_dict, display=display)

class MapExporter:
    """
    Utility class for exporting maps in various formats.
    Works with MapCache instances to create export files.
    """
    def __init__(self, map_id: str) -> None:
        self.map_id = map_id
        self.map_json_path = static_config.temp_map_json_template.format(map_id=self.map_id)
        self.preview_image_path = static_config.temp_preview_image_template.format(map_id=self.map_id)

    def export_json(self, map_cache: MapCache, tilesets: Dict[int, Tileset]) -> str:
        """
        Export the map to a JSON file.
        
        Args:
            map_cache: The MapCache instance to export
            tilesets: Dictionary of tilesets {tileset_id: Tileset}
            output_path: The file path to save the exported map
        
        Returns:
            The path to the exported file
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(self.map_json_path)), exist_ok=True)
        
        # Generate map data
        tilemap_dict = MapExporter._generate_map_data(map_cache, tilesets)
        
        # Write to file
        with open(self.map_json_path, 'w', encoding='utf-8') as f:
            json.dump(tilemap_dict, f, indent=2)
        
        logger.info(f"Map exported to JSON: {self.map_json_path}")
        return self.map_json_path

    def preview_map(self, tilemap_dict: dict, display: bool = True) -> str:
        """
        Generate a preview image of the map.
        
        Args:
            tilemap_dict: Tilemap dictionary to generate a preview for
            display: Whether to display the preview
        
        Returns:
            The path to the generated preview image
        """
        if tilemap_dict is None:
            raise ValueError("Tilemap dictionary must be provided for preview")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(self.preview_image_path)), exist_ok=True)
        
        logger.info(f"Preview image would be generated at: {self.preview_image_path}")
        visualize_tilemap(tilemap_dict, self.preview_image_path, display)
        
        # Return the path where the preview would be saved
        return self.preview_image_path

    @staticmethod
    def _generate_map_data(map_cache: MapCache, tilesets: Dict[int, Tileset]) -> dict:
        """Generate map data dictionary"""
        
        tilemap_dict = {
            "width": map_cache.width,
            "height": map_cache.height,
            "tilewidth": static_config.tile_width,
            "tileheight": static_config.tile_height,
            "version": "1.10",
            "type": "map",
            "tiledversion": "1.10.0",
            "orientation": "orthogonal",
            "renderorder": "right-down",
            "nextlayerid": map_cache.layer_nums + 1,
            "nextobjectid": 1,
            "compressionlevel": -1,
            "layers": [],
            "tilesets": []
        }

        # Process layer data, first add itemlayer to layers
        layers = [map_cache.itemlayer.to_dict()]
        
        # Exclude all-zero layers, but always include cover and collision layers
        for layer_index in range(map_cache.layer_nums):
            layer_data = []
            for y in range(map_cache.height):
                for x in range(map_cache.width):
                    ts_idx = map_cache.tile_data[layer_index, y, x, 0]
                    local_id = map_cache.tile_data[layer_index, y, x, 1]
                    if ts_idx <= 0:
                        gid = 0
                    else:
                        tileset = tilesets[ts_idx]
                        gid = tileset.firstgid + local_id - 1

                    layer_data.append(gid)
                    
            # 排除全0层，但一定包含遮盖和碰撞层
            if (any(data for data in layer_data)
                    or layer_index == static_config.cover_layer
                    or layer_index == static_config.obstacle_layer):
                common_layer_name = f"Layer_{layer_index + 1}"
                if layer_index == static_config.cover_layer:
                    common_layer_name = "CoverLayer"
                elif layer_index == static_config.obstacle_layer:
                    common_layer_name = "Obstacles"
                layer_dict = {
                    "id": layer_index,
                    "name": common_layer_name,
                    "type": "tilelayer",
                    "width": map_cache.width,
                    "height": map_cache.height,
                    "visible": True,
                    "opacity": 1,
                    "data": layer_data,
                    "x": 0,
                    "y": 0
                }
                layers.append(layer_dict)
                
        # Process tileset data
        tilesets_data = []
        for tileset_id, tileset in tilesets.items():
            tileset_dict = tileset.dict()
            tilesets_data.append(tileset_dict)

            if tileset_id == map_cache.collision_idx[0]:
                if "tiles" not in tileset_dict:
                    tileset_dict["tiles"] = []
                tileset_dict["tiles"].append(
                    {
                        "id": tileset.firstgid + map_cache.collision_idx[1] - 1,
                        "properties": [
                            {
                                "name": "collision",
                                "type": "bool",
                                "value": True
                            }
                        ]
                    }
                )
            if tileset_id == map_cache.cover_idx[0]:
                if "tiles" not in tileset_dict:
                    tileset_dict["tiles"] = []
                tileset_dict["tiles"].append(
                    {
                        "id": tileset.firstgid + map_cache.cover_idx[1] - 1,
                        "properties": [
                            {
                                "name": "cover",
                                "type": "bool",
                                "value": True
                            }
                        ]
                    }
                )
                
        tilemap_dict["layers"] = layers
        tilemap_dict["tilesets"] = tilesets_data

        return tilemap_dict