import os
import json
import asyncio
from typing import Dict, Any

from implement.room_impl.config import ROOM_CONFIG_PATH, IMPLEMENT_FOLDER
from implement.room_impl.element_room import Room
from tiled_master import CollisionElement, CoverElement, MapBuilder
from tiled_master.schema import ResourceDescriptor
from tiled_master.utils.logger import logger


class RoomImplementation:
    """
    Room Implementation Class
    
    Reads configuration files, creates Room, CollisionElement and CoverElement instances,
    and uses MapBuilder to build and export the map
    """
    
    def __init__(self, map_id: str, config_path: str = ROOM_CONFIG_PATH):
        """
        Initialize implementation
        
        Args:
            config_path: Configuration file path, defaults to ROOM_CONFIG_PATH
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.map_id = map_id
        self.width = self.config.get("width", 60)
        self.height = self.config.get("height", 40)
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration file: {e}")
            raise
            
    def _configure_descriptors(self, element_config: Dict[str, Any], descriptors: Dict[str, ResourceDescriptor]) -> Dict[str, ResourceDescriptor]:
        """
        Update resource descriptors from configuration
        
        Args:
            element_config: Element configuration
            descriptors: Default resource descriptor dictionary
            
        Returns:
            Updated resource descriptor dictionary
        """
        # Handle interior element configuration
        if element_config.get("type") == "interior":
            # Update floor resource configuration
            if "floor" in element_config and Room.Resources.FLOOR_TILES.value in descriptors:
                floor_config = element_config["floor"]
                floor_descriptor = descriptors[Room.Resources.FLOOR_TILES.value]
                floor_descriptor.scale = element_config.get("scale", floor_descriptor.scale)
                
                # Clear default textures and add configured floor textures
                floor_descriptor.tiles = []
                if "textures" in floor_config:
                    for texture in floor_config["textures"]:
                        floor_descriptor.add_tile(
                            resource_id=texture.get("name", Room.Resources.FLOOR_TILES.value),
                            image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                            collision=texture.get("collision", False),
                            cover=texture.get("cover", False),
                            rate=texture.get("rate", 1)
                        )
                
            # Update wall level 1 resource configuration
            if "wall_lv1" in element_config and Room.Resources.WALL_LV1_TILES.value in descriptors:
                wall_lv1_config = element_config["wall_lv1"]
                wall_lv1_descriptor = descriptors[Room.Resources.WALL_LV1_TILES.value]
                wall_lv1_descriptor.scale = element_config.get("scale", wall_lv1_descriptor.scale)
                
                # Clear default textures and add configured wall textures
                wall_lv1_descriptor.tiles = []
                if "textures" in wall_lv1_config:
                    for texture in wall_lv1_config["textures"]:
                        wall_lv1_descriptor.add_tile(
                            resource_id=texture.get("name", Room.Resources.WALL_LV1_TILES.value),
                            image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                            collision=texture.get("collision", True),
                            cover=texture.get("cover", False),
                            rate=texture.get("rate", 1)
                        )
                
            # Update wall level 2 resource configuration
            if "wall_lv2" in element_config and Room.Resources.WALL_LV2_TILES.value in descriptors:
                wall_lv2_config = element_config["wall_lv2"]
                wall_lv2_descriptor = descriptors[Room.Resources.WALL_LV2_TILES.value]
                wall_lv2_descriptor.scale = element_config.get("scale", wall_lv2_descriptor.scale)
                
                # Clear default textures and add configured wall textures
                wall_lv2_descriptor.tiles = []
                if "textures" in wall_lv2_config:
                    for texture in wall_lv2_config["textures"]:
                        wall_lv2_descriptor.add_tile(
                            resource_id=texture.get("name", Room.Resources.WALL_LV2_TILES.value),
                            image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                            collision=texture.get("collision", True),
                            cover=texture.get("cover", False),
                            rate=texture.get("rate", 1)
                        )
                
            # Update roof resource configuration
            if "roof" in element_config and Room.Resources.ROOF_TILES.value in descriptors:
                roof_config = element_config["roof"]
                roof_descriptor = descriptors[Room.Resources.ROOF_TILES.value]
                roof_descriptor.scale = element_config.get("scale", roof_descriptor.scale)
                
                # Clear default textures and add configured roof textures
                roof_descriptor.tiles = []
                roof_descriptor.auto_tiles = []
                if "textures" in roof_config:
                    for texture in roof_config["textures"]:
                        if texture.get("type") == "auto_tile":
                            roof_descriptor.add_auto_tile(
                                resource_id=texture.get("name", Room.Resources.ROOF_TILES.value),
                                image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                                method=texture.get("method", "blob47"),
                                collision=texture.get("collision", True),
                                cover=texture.get("cover", False),
                                rate=texture.get("rate", 1)
                            )
                        else:
                            roof_descriptor.add_tile(
                                resource_id=texture.get("name", Room.Resources.ROOF_TILES.value),
                                image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                                collision=texture.get("collision", True),
                                cover=texture.get("cover", False),
                                rate=texture.get("rate", 1)
                            )
        # Handle collision element configuration
        elif element_config.get("type") == "tilegroup" and CollisionElement.Resources.COLLISION_TILES.value in descriptors:
            collision_descriptor = descriptors[CollisionElement.Resources.COLLISION_TILES.value]
            collision_descriptor.scale = element_config.get("scale", collision_descriptor.scale)
            
            # Clear default textures and add configured collision textures
            collision_descriptor.tiles = []
            if "textures" in element_config:
                for texture in element_config["textures"]:
                    collision_descriptor.add_tile(
                        resource_id=texture.get("name", CollisionElement.Resources.COLLISION_TILE.value),
                        image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                        collision=texture.get("collision", True),
                        cover=texture.get("cover", False),
                        rate=texture.get("rate", 1)
                    )
        
        # Handle cover element configuration
        elif element_config.get("type") == "tilegroup" and CoverElement.Resources.COVER_TILES.value in descriptors:
            cover_descriptor = descriptors[CoverElement.Resources.COVER_TILES.value]
            cover_descriptor.scale = element_config.get("scale", cover_descriptor.scale)
            
            # Clear default textures and add configured cover textures
            cover_descriptor.tiles = []
            if "textures" in element_config:
                for texture in element_config["textures"]:
                    cover_descriptor.add_tile(
                        resource_id=texture.get("name", CoverElement.Resources.COVER_TILE.value),
                        image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                        collision=texture.get("collision", False),
                        cover=texture.get("cover", True),
                        rate=texture.get("rate", 1)
                    )
                
        return descriptors
        
    async def build_map(self, output_path: str = None):
        """
        Build map and export
        
        Args:
            output_path: Output path, if None uses default path
            
        Returns:
            Export path
        """
        try:
            # Create map builder
            builder = MapBuilder(
                map_id=self.map_id,
                width=self.width,
                height=self.height
            )
            
            # Parse element configuration and add elements
            for element_config in self.config.get("elements", []):
                if not element_config.get("enable", True):
                    continue
                    
                element_name = element_config.get("name", "")
                element_data = element_config.get("data", {})
                
                if element_name == "interior":
                    # Get Room element default resource descriptors
                    room_descriptors = Room.get_default_descriptors()
                    # Update resource descriptors based on configuration
                    configured_descriptors = self._configure_descriptors(element_data, room_descriptors)
                    
                    # Create room element
                    room = Room(
                        name="interior_room",
                        grid_width=element_data.get("grid_width", 12),
                        grid_height=element_data.get("grid_height", 8),
                        cell_width=element_data.get("cell_width", 4),
                        cell_height=element_data.get("cell_height", 5),
                        line_width=element_data.get("line_width", 1),
                        descriptors=configured_descriptors
                    )
                    builder.add_element(room)
                    
                elif element_name == "collision":
                    # Get CollisionElement default resource descriptors
                    collision_descriptors = CollisionElement.get_default_descriptors()
                    # Update resource descriptors based on configuration
                    configured_descriptors = self._configure_descriptors(element_data, collision_descriptors)
                    
                    # Create collision element
                    collision_element = CollisionElement(
                        name="collision", 
                        descriptors=configured_descriptors
                    )
                    builder.add_element(collision_element)
                    
                elif element_name == "cover":
                    # Get CoverElement default resource descriptors
                    cover_descriptors = CoverElement.get_default_descriptors()
                    # Update resource descriptors based on configuration
                    configured_descriptors = self._configure_descriptors(element_data, cover_descriptors)
                    
                    # Create cover element
                    cover_element = CoverElement(
                        name="cover",
                        descriptors=configured_descriptors
                    )
                    builder.add_element(cover_element)
            
            # Build map (builder will handle preload and build process)
            map_cache = await builder.build()
                
            exported_path = builder.export_map()
            builder.preview_map()
            logger.info(f"Map exported to: {exported_path}")
            
            return exported_path
            
        except Exception as e:
            logger.error(f"Failed to build map: {e}")
            raise


async def main():
    """Main function"""
    try:
        implementation = RoomImplementation("23")
        await implementation.build_map()
    except Exception as e:
        logger.error(f"Map generation failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
