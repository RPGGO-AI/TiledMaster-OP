import os
import json
import asyncio
import uuid
from typing import Dict, Any, Optional

from implement.town_impl.config import (
    SUMMER_CONFIG_PATH, WINTER_CONFIG_PATH, DESERT_CONFIG_PATH, 
    MODERN_CONFIG_PATH, MUD_CONFIG_PATH, IMPLEMENT_FOLDER
)
from implement.town_impl.schema import MapGenSetting, MapGenRequest
from implement.town_impl.element_town import Town
from implement.town_impl.element_village import Village
from implement.town_impl.element_natural import River, Woods, Ground, Bush
from implement.town_impl.element_logic import TownLogic
from tiled_master import CollisionElement, CoverElement, MapBuilder
from tiled_master.schema import ResourceDescriptor
from tiled_master.utils.logger import logger
from tiled_master.utils.globalvaris import (
    WaterLevel, TreeLevel, SceneLevel, LAYOUT
)


class TownImplementation:
    """
    Town Implementation Class
    
    Handles MapGenSetting configuration and creates Town maps, replacing the old implementation in config_loader.py
    """
    
    def __init__(self, map_id: str, setting: Optional[MapGenSetting] = None, config_url: str = ""):
        """
        Initialize implementation
        
        Args:
            map_id: Map ID
            setting: MapGenSetting configuration, if None, config_url will be used to load configuration
            config_url: Configuration file path, used when setting is None
        """
        if not map_id:
            logger.warning("map_id is expected, but not provided")
            map_id = str(uuid.uuid4())
        self.map_id = map_id
        self.setting = setting
        self.config_url = config_url
        self.config = self._load_config()
        self.width = self.config.get("width", 128)
        self.height = self.config.get("height", 64)
        self.layout_name = self.config.get("type", "Town")  # Default to Town layout
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration file based on setting or config_url"""
        try:
            if self.setting:
                return self._get_config_from_setting(self.setting)
            elif self.config_url:
                with open(self.config_url, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Default configuration
                with open(SUMMER_CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config_dict = json.load(f)
                    logger.info("Using default map configuration")
                    return config_dict
        except Exception as e:
            logger.error(f"Failed to load configuration file: {e}")
            raise
    
    def _get_config_from_setting(self, setting: MapGenSetting) -> Dict[str, Any]:
        """
        Build configuration based on MapGenSetting
        
        References the old _get_config_from_setting method in config_loader.py
        """
        def get_element_by_name(elements, el_name) -> dict | None:
            for el in elements:
                if el["name"] == el_name:
                    return el
            return None

        try:
            scene_name = setting.Scene.get("name")
            # Select base configuration file based on scene name
            if scene_name == "Summer":
                config_dict = self._read_json_file(SUMMER_CONFIG_PATH)
            else:
                logger.warning(f"Unknown scene name: {scene_name}, using Summer scene")
                config_dict = self._read_json_file(SUMMER_CONFIG_PATH)
            
            # Set layout type
            layout_name = setting.Layout.get("name", "Town")
            config_dict["type"] = layout_name
            logger.info(f"Setting layout type: {layout_name}")

            elements = config_dict.get("elements", [])

            # Handle building configuration
            town_dict = get_element_by_name(elements, "town")
            if town_dict:
                town_dict["data"]["scale"] = setting.Building

                # Handle road configuration
                road_dict = town_dict["data"].get("road", {})
                if setting.Building == 0:
                    # If there are no buildings, roads are not needed
                    road_dict = {}
                elif setting.Building <= 5:
                    road_dict["scale"] = 1
                else:
                    road_dict["scale"] = 2
                town_dict["data"]["road"] = road_dict

            # Handle river configuration
            river_dict = get_element_by_name(elements, "river")
            if river_dict and setting.Water:
                river_mapping = {
                    WaterLevel.Scattered.value: 1,
                    WaterLevel.Standard.value: 2,
                    WaterLevel.Wide.value: 3,
                    WaterLevel.Straight.value: 4,
                    WaterLevel.Island.value: 5,
                    WaterLevel.Coastal.value: 6
                }
                river_dict["data"]["scale"] = river_mapping.get(setting.Water, 2)
            elif river_dict:
                river_dict["enable"] = False

            # Handle tree configuration
            woods_dict = get_element_by_name(elements, "woods")
            if woods_dict and setting.Tree:
                tree_mapping = {
                    TreeLevel.Sparse.value: 1,
                    TreeLevel.Encircle.value: 2,
                    TreeLevel.Patchy.value: 3,
                    TreeLevel.Dense_Encircle.value: 4
                }
                woods_dict["data"]["scale"] = tree_mapping.get(setting.Tree, 1)
            elif woods_dict:
                woods_dict["enable"] = False

            return config_dict

        except Exception as e:
            logger.error(f"Failed to build configuration from MapGenSetting: {e}")
            # Return default configuration
            return self._read_json_file(SUMMER_CONFIG_PATH)
    
    def _read_json_file(self, file_path: str) -> Dict[str, Any]:
        """Read JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read JSON file: {file_path}, {e}")
            raise
    
    def _configure_village_descriptors(self, element_config: Dict[str, Any], descriptors: Dict[str, ResourceDescriptor]) -> Dict[str, ResourceDescriptor]:
        """Configure resource descriptors for Village element"""
        # Configure special buildings
        if "spec_buildings" in element_config and Village.Resources.SPEC_BUILDINGS.value in descriptors:
            spec_buildings_descriptor = descriptors[Village.Resources.SPEC_BUILDINGS.value]
            spec_buildings_descriptor.scale = element_config.get("scale", spec_buildings_descriptor.scale)
            
            # Clear default textures and add configured building textures
            spec_buildings_descriptor.objects = []
            for building in element_config.get("spec_buildings", []):
                if "data" in building and "textures" in building["data"]:
                    for texture in building["data"]["textures"]:
                        spec_buildings_descriptor.add_object(
                            resource_id=texture.get("name", "spec_building"),
                            image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                            shape="rectangle",
                            width=texture.get("width", 2),
                            height=texture.get("height", 2),
                            collision=texture.get("collision", True),
                            cover=texture.get("cover", False),
                            rate=texture.get("rate", 1)
                        )
        
        # Configure default buildings
        if "default_buildings" in element_config and Village.Resources.DEFAULT_BUILDINGS.value in descriptors:
            default_buildings_descriptor = descriptors[Village.Resources.DEFAULT_BUILDINGS.value]
            default_buildings_descriptor.scale = element_config.get("scale", default_buildings_descriptor.scale)
            
            # Clear default textures and add configured building textures
            default_buildings_descriptor.objects = []
            for building in element_config.get("default_buildings", []):
                if "data" in building and "textures" in building["data"]:
                    for texture in building["data"]["textures"]:
                        default_buildings_descriptor.add_object(
                            resource_id=texture.get("name", "default_building"),
                            image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                            shape="rectangle",
                            width=texture.get("width", 2),
                            height=texture.get("height", 2),
                            collision=texture.get("collision", True),
                            cover=texture.get("cover", False),
                            rate=texture.get("rate", 1)
                        )
        
        # Configure road
        if "road" in element_config and Village.Resources.ROAD.value in descriptors:
            road_descriptor = descriptors[Village.Resources.ROAD.value]
            road_config = element_config.get("road", {})
            road_descriptor.scale = road_config.get("scale", road_descriptor.scale)
            
            # Clear default textures and add configured road textures
            road_descriptor.tiles = []
            road_descriptor.auto_tiles = []
            if "textures" in road_config:
                for texture in road_config["textures"]:
                    if texture.get("type") == "auto_tile":
                        road_descriptor.add_auto_tile(
                            resource_id=texture.get("name", "road"),
                            image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                            method=texture.get("method", "tile48"),
                            collision=texture.get("collision", False),
                            cover=texture.get("cover", False),
                            rate=texture.get("rate", 1)
                        )
                    else:
                        road_descriptor.add_tile(
                            resource_id=texture.get("name", "road"),
                            image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                            collision=texture.get("collision", False),
                            cover=texture.get("cover", False),
                            rate=texture.get("rate", 1)
                        )
        
        # Configure bridge
        if "bridge" in element_config and Village.Resources.BRIDGE.value in descriptors:
            bridge_descriptor = descriptors[Village.Resources.BRIDGE.value]
            bridge_config = element_config.get("bridge", {})
            bridge_descriptor.scale = bridge_config.get("scale", bridge_descriptor.scale)
            
            # Clear default textures and add configured bridge textures
            bridge_descriptor.tiles = []
            if "textures" in bridge_config:
                for texture in bridge_config["textures"]:
                    if texture.get("type") == "auto_tile":
                        bridge_descriptor.add_auto_tile(
                            resource_id=texture.get("name", "bridge"),
                            image=os.path.join(IMPLEMENT_FOLDER, texture.get("image")),
                            method=texture.get("method"),
                            collision=texture.get("collision", False),
                            cover=texture.get("cover", False),
                            rate=texture.get("rate", 1)
                        )
                    else:
                        bridge_descriptor.add_tile(
                            resource_id=texture.get("name", "bridge"),
                            image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                            collision=texture.get("collision", False),
                            cover=texture.get("cover", False),
                            rate=texture.get("rate", 1)
                        )
        
        return descriptors

    def _configure_town_descriptors(self, element_config: Dict[str, Any], descriptors: Dict[str, ResourceDescriptor]) -> Dict[str, ResourceDescriptor]:
        """Configure resource descriptors for Town element"""
        # Configure special buildings
        if "spec_buildings" in element_config and Town.Resources.SPEC_BUILDINGS.value in descriptors:
            spec_buildings_descriptor = descriptors[Town.Resources.SPEC_BUILDINGS.value]
            spec_buildings_descriptor.scale = element_config.get("scale", spec_buildings_descriptor.scale)
            
            # Clear default textures and add configured building textures
            spec_buildings_descriptor.objects = []
            for building in element_config.get("spec_buildings", []):
                if "data" in building and "textures" in building["data"]:
                    for texture in building["data"]["textures"]:
                        spec_buildings_descriptor.add_object(
                            resource_id=texture.get("name", "spec_building"),
                            image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                            shape="rectangle",
                            width=texture.get("width", 2),
                            height=texture.get("height", 2),
                            collision=texture.get("collision", True),
                            cover=texture.get("cover", False),
                            rate=texture.get("rate", 1)
                        )
        
        # Configure default buildings
        if "default_buildings" in element_config and Town.Resources.DEFAULT_BUILDINGS.value in descriptors:
            default_buildings_descriptor = descriptors[Town.Resources.DEFAULT_BUILDINGS.value]
            default_buildings_descriptor.scale = element_config.get("scale", default_buildings_descriptor.scale)
            
            # Clear default textures and add configured building textures
            default_buildings_descriptor.objects = []
            for building in element_config.get("default_buildings", []):
                if "data" in building and "textures" in building["data"]:
                    for texture in building["data"]["textures"]:
                        default_buildings_descriptor.add_object(
                            resource_id=texture.get("name", "default_building"),
                            image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                            shape="rectangle",
                            width=texture.get("width", 2),
                            height=texture.get("height", 2),
                            collision=texture.get("collision", True),
                            cover=texture.get("cover", False),
                            rate=texture.get("rate", 1)
                        )
        
        # Configure road
        if "road" in element_config and Town.Resources.ROAD.value in descriptors:
            road_descriptor = descriptors[Town.Resources.ROAD.value]
            road_config = element_config.get("road", {})
            road_descriptor.scale = road_config.get("scale", road_descriptor.scale)
            
            # Clear default textures and add configured road textures
            road_descriptor.tiles = []
            road_descriptor.auto_tiles = []
            if "textures" in road_config:
                for texture in road_config["textures"]:
                    if texture.get("type") == "auto_tile":
                        road_descriptor.add_auto_tile(
                            resource_id=texture.get("name", "road"),
                            image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                            method=texture.get("method", "tile48"),
                            collision=texture.get("collision", False),
                            cover=texture.get("cover", False),
                            rate=texture.get("rate", 1)
                        )
                    else:
                        road_descriptor.add_tile(
                            resource_id=texture.get("name", "road"),
                            image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                            collision=texture.get("collision", False),
                            cover=texture.get("cover", False),
                            rate=texture.get("rate", 1)
                        )
        
        # Configure bridge
        if "bridge" in element_config and Town.Resources.BRIDGE.value in descriptors:
            bridge_descriptor = descriptors[Town.Resources.BRIDGE.value]
            bridge_config = element_config.get("bridge", {})
            bridge_descriptor.scale = bridge_config.get("scale", bridge_descriptor.scale)
            
            # Clear default textures and add configured bridge textures
            bridge_descriptor.tiles = []
            if "textures" in bridge_config:
                for texture in bridge_config["textures"]:
                    if texture.get("type") == "auto_tile":
                        bridge_descriptor.add_auto_tile(
                            resource_id=texture.get("name", "bridge"),
                            image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                            method=texture.get("method", "tile48"),
                            collision=texture.get("collision", False),
                            cover=texture.get("cover", False),
                            rate=texture.get("rate", 1)
                        )
                    else:
                        bridge_descriptor.add_tile(
                            resource_id=texture.get("name", "bridge"),
                            image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                            collision=texture.get("collision", False),
                            cover=texture.get("cover", False),
                            rate=texture.get("rate", 1)
                        )
        
        return descriptors
    
    def _configure_river_descriptors(self, element_config: Dict[str, Any], descriptors: Dict[str, ResourceDescriptor]) -> Dict[str, ResourceDescriptor]:
        """Configure resource descriptors for River element"""
        river_descriptor = descriptors[River.Resources.RIVER_TILES.value]
        river_descriptor.scale = element_config.get("scale", river_descriptor.scale)
        
        # Clear default textures and add configured river textures
        river_descriptor.tiles = []
        river_descriptor.auto_tiles = []
        if "textures" in element_config:
            for texture in element_config["textures"]:
                if texture.get("type") == "auto_tile":
                    river_descriptor.add_auto_tile(
                        resource_id=texture.get("name", "river"),
                        image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                        method=texture.get("method", "tile48"),
                        collision=texture.get("collision", False),
                        cover=texture.get("cover", False),
                        rate=texture.get("rate", 1)
                    )
                else:
                    river_descriptor.add_tile(
                        resource_id=texture.get("name", "river"),
                        image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                        collision=texture.get("collision", False),
                        cover=texture.get("cover", False),
                        rate=texture.get("rate", 1)
                    )
        
        return descriptors
    
    def _configure_woods_descriptors(self, element_config: Dict[str, Any], descriptors: Dict[str, ResourceDescriptor]) -> Dict[str, ResourceDescriptor]:
        """Configure resource descriptors for Woods element"""
        woods_descriptor = descriptors[Woods.Resources.TREE_OBJECTS.value]
        woods_descriptor.scale = element_config.get("scale", woods_descriptor.scale)
        
        # Clear default textures and add configured tree textures
        woods_descriptor.objects = []
        if "textures" in element_config:
            for texture in element_config["textures"]:
                woods_descriptor.add_object(
                    resource_id=texture.get("name", "tree"),
                    image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                    shape="rectangle",
                    width=texture.get("width", 1),
                    height=texture.get("height", 1),
                    collision=texture.get("collision", True),
                    cover=texture.get("cover", True),
                    rate=texture.get("rate", 1)
                )
        
        return descriptors
    
    def _configure_ground_descriptors(self, element_config: Dict[str, Any], descriptors: Dict[str, ResourceDescriptor]) -> Dict[str, ResourceDescriptor]:
        """Configure resource descriptors for Ground element"""
        ground_descriptor = descriptors[Ground.Resources.GROUND_TILES.value]
        ground_descriptor.scale = element_config.get("scale", ground_descriptor.scale)
        
        # Clear default textures and add configured ground textures
        ground_descriptor.tiles = []
        if "textures" in element_config:
            for texture in element_config["textures"]:            
                if texture.get("type") == "auto_tile":
                    ground_descriptor.add_auto_tile(
                        resource_id=texture.get("name", "ground_autotile"),
                        image=os.path.join(IMPLEMENT_FOLDER, texture.get("image")),
                        method=texture.get("method"),
                        collision=texture.get("collision", False),
                        cover=texture.get("cover", False),
                        rate=texture.get("rate", 1)
                    )
                else:
                    ground_descriptor.add_tile(
                        resource_id=texture.get("name", "ground"),
                        image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                        collision=texture.get("collision", False),
                        cover=texture.get("cover", False),
                        rate=texture.get("rate", 1)
                    )
        
        return descriptors
    
    def _configure_bush_descriptors(self, element_config: Dict[str, Any], descriptors: Dict[str, ResourceDescriptor]) -> Dict[str, ResourceDescriptor]:
        """Configure resource descriptors for Bush element"""
        bush_descriptor = descriptors[Bush.Resources.BUSH_TILES.value]
        bush_descriptor.scale = element_config.get("scale", bush_descriptor.scale)
        
        # Clear default textures and add configured shrub textures
        bush_descriptor.tiles = []
        if "textures" in element_config:
            for texture in element_config["textures"]:
                bush_descriptor.add_tile(
                    resource_id=texture.get("name", "bush"),
                    image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                    collision=texture.get("collision", False),
                    cover=texture.get("cover", True),
                    rate=texture.get("rate", 1)
                )
        
        return descriptors
    
    def _configure_collision_descriptors(self, element_config: Dict[str, Any], descriptors: Dict[str, ResourceDescriptor]) -> Dict[str, ResourceDescriptor]:
        """Configure resource descriptors for Collision element"""
        collision_descriptor = descriptors[CollisionElement.Resources.COLLISION_TILES.value]
        collision_descriptor.scale = element_config.get("scale", collision_descriptor.scale)
        
        # Clear default textures and add configured collision textures
        collision_descriptor.tiles = []
        if "textures" in element_config:
            for texture in element_config["textures"]:
                collision_descriptor.add_tile(
                    resource_id=texture.get("name", "collision"),
                    image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                    collision=texture.get("collision", True),
                    cover=texture.get("cover", False),
                    rate=texture.get("rate", 1)
                )
        
        return descriptors
    
    def _configure_cover_descriptors(self, element_config: Dict[str, Any], descriptors: Dict[str, ResourceDescriptor]) -> Dict[str, ResourceDescriptor]:
        """Configure resource descriptors for Cover element"""
        cover_descriptor = descriptors[CoverElement.Resources.COVER_TILES.value]
        cover_descriptor.scale = element_config.get("scale", cover_descriptor.scale)
        
        # Clear default textures and add configured cover textures
        cover_descriptor.tiles = []
        if "textures" in element_config:
            for texture in element_config["textures"]:
                cover_descriptor.add_tile(
                    resource_id=texture.get("name", "cover"),
                    image=os.path.join(IMPLEMENT_FOLDER, texture.get("image", "")),
                    collision=texture.get("collision", False),
                    cover=texture.get("cover", True),
                    rate=texture.get("rate", 1)
                )
        
        return descriptors
            
    
    async def build_map(self, preview = False):
        """
        Build the map and export it
        
        Args:
            preview: Whether to generate a preview only
            
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
                
                if element_name == "town":
                    # Select Town or Village based on layout type
                    if self.layout_name == "Village":
                        logger.info(f"Using Village layout to generate map")
                        # Use Village element
                        village_descriptors = Village.get_default_descriptors()
                        # Update resource descriptors based on configuration
                        configured_descriptors = self._configure_village_descriptors(element_data, village_descriptors)
                        
                        # Create Village element
                        village = Village(
                            name="village",
                            width=self.width,
                            height=self.height,
                            num_nodes=element_data.get("num_nodes", 15),
                            descriptors=configured_descriptors
                        )
                        builder.add_element(village)
                    else:
                        logger.info(f"Using Town layout to generate map")
                        # Use Town element
                        town_descriptors = Town.get_default_descriptors()
                        # Update resource descriptors based on configuration
                        configured_descriptors = self._configure_town_descriptors(element_data, town_descriptors)
                        
                        # Create Town element
                        town = Town(
                            name="town",
                            num_nodes=element_data.get("num_nodes", 20),
                            descriptors=configured_descriptors
                        )
                        builder.add_element(town)
                
                elif element_name == "river":
                    # Get default resource descriptors for River element
                    river_descriptors = River.get_default_descriptors()
                    # Update resource descriptors based on configuration
                    configured_descriptors = self._configure_river_descriptors(element_data, river_descriptors)
                    # Create River element
                    river = River(
                        name="river",
                        descriptors=configured_descriptors
                    )
                    builder.add_element(river)
                
                elif element_name == "woods":
                    # Get default resource descriptors for Woods element
                    woods_descriptors = Woods.get_default_descriptors()
                    # Update resource descriptors based on configuration
                    configured_descriptors = self._configure_woods_descriptors(element_data, woods_descriptors)
                    
                    # Create Woods element
                    woods = Woods(
                        name="woods",
                        descriptors=configured_descriptors
                    )
                    builder.add_element(woods)
                
                elif element_name == "ground":
                    # Get default resource descriptors for Ground element
                    ground_descriptors = Ground.get_default_descriptors()
                    # Update resource descriptors based on configuration
                    configured_descriptors = self._configure_ground_descriptors(element_data, ground_descriptors)
                    
                    # Create Ground element
                    ground = Ground(
                        name="ground",
                        descriptors=configured_descriptors
                    )
                    builder.add_element(ground)
                
                elif element_name == "bush":
                    # Get default resource descriptors for Bush element
                    bush_descriptors = Bush.get_default_descriptors()
                    # Update resource descriptors based on configuration
                    configured_descriptors = self._configure_bush_descriptors(element_data, bush_descriptors)
                    
                    # Create Bush element
                    bush = Bush(
                        name="bush",
                        descriptors=configured_descriptors
                    )
                    builder.add_element(bush)

                elif element_name == "collision":
                    # Get CollisionElement default resource descriptors
                    collision_descriptors = CollisionElement.get_default_descriptors()
                    # Update resource descriptors based on configuration
                    configured_descriptors = self._configure_collision_descriptors(element_data, collision_descriptors)
                    
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
                    configured_descriptors = self._configure_cover_descriptors(element_data, cover_descriptors)
                    
                    # Create cover element
                    cover_element = CoverElement(
                        name="cover",
                        descriptors=configured_descriptors
                    )
                    builder.add_element(cover_element)
            
            # Add business logic element
            town_logic = TownLogic()
            builder.add_element(town_logic)

            # Build map (builder will handle preload and build process)
            map_cache = await builder.build()
            export_path = builder.export_map()
            image_path = builder.preview_map(display=preview)
            return export_path, image_path
            
        except Exception as e:
            logger.error(f"Failed to build map: {e}")
            raise


async def load_config_from_request(req: MapGenRequest) -> TownImplementation:
    """
    Load configuration from MapGenRequest and create TownImplementation instance
    
    Args:
        req: MapGenRequest request object
        
    Returns:
        TownImplementation instance
    """
    try:
        implementation = TownImplementation(
            map_id=req.map_id,
            setting=req.setting,
            config_url=req.config_url
        )
        return implementation
    except Exception as e:
        logger.error(f"Failed to load configuration from request: {e}")
        raise


async def generate_town_map(req: MapGenRequest):
    import uuid

    if not req.map_id:
        req.map_id = str(uuid.uuid4())

    implementation = await load_config_from_request(req)
    export_path, image_path = await implementation.build_map()
    logger.info(f"Map export successful: {export_path}, preview_image_path: {image_path}")
        
    
async def test_visualize():
    setting = MapGenSetting(
        Layout={"name": "Village"},
        Scene={"name": "Summer"},
        Building=20,
        Tree=TreeLevel.Patchy.value,
        Water=WaterLevel.Standard.value
    )
    request = MapGenRequest(
        game_id="collection",
        setting=setting
    )
    implementation = await load_config_from_request(request)
    export_path, image_path = await implementation.build_map(preview=True)

if __name__ == "__main__":
    # asyncio.run(main())
    asyncio.run(test_visualize())
