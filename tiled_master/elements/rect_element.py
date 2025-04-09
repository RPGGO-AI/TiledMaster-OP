from typing import Optional, Tuple, ClassVar
from enum import Enum

from tiled_master.framework.element import MapElement, ObjectGroupDescriptor
from tiled_master.framework.map_cache import MAP_CACHE
from tiled_master.framework.object import Object
import tiled_master.framework.config as config
from tiled_master.framework.schema import TextureObject, ObjectGroup

class RectElement(MapElement):
    """A rectangular element that can place object groups in a specified region
    
    Required resources:
    - objects (ObjectGroupDescriptor): The object group to be placed in the rectangle
    """
    
    class Resources(Enum):
        OBJECTS = "objects"
    
    def __init__(self, 
                 name: str,
                 x: int,
                 y: int,
                 width: int,
                 height: int,
                 layer: int,
                 descriptors: Optional[dict] = None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.layer = layer
        super().__init__(name=name, descriptors=descriptors)
    
    def _setup_resources(self):
        """Setup the required object group resource"""
        self._add_object_group(self.Resources.OBJECTS.value)
    
    def _within_bounds(self, map_width: int, map_height: int) -> bool:
        """Check if the rectangle is completely within map bounds"""
        return (self.x >= 0 
                and self.x + self.width <= map_width 
                and self.y >= 0 
                and self.y + self.height <= map_height)
    
    def get_region(self) -> Tuple[int, int, int, int]:
        """Get the region as (x, y, width, height)"""
        return self.x, self.y, self.width, self.height
    
    async def build(self, map_cache: MAP_CACHE):
        """Build the rectangle by placing objects from the object group"""
        # Get map dimensions
        map_width = map_cache.width
        map_height = map_cache.height
        
        # Check if rectangle is within bounds
        if not self._within_bounds(map_width, map_height):
            raise ValueError(f"Rectangle {self.get_region()} is out of map bounds ({map_width}, {map_height})")
        
        # Get the object group
        object_group: ObjectGroup = self.loaded_resources[self.Resources.OBJECTS.value]

        # Generate all coordinate points within the rectangular area
        drop_area = []
        for y in range(self.y, self.y + self.height):
            for x in range(self.x, self.x + self.width):
                drop_area.append((x, y))
        
        # Use the new method to place the object group
        map_cache.drop_objects_from_objectgroup(
            objectgroup=object_group,
            drop_area=drop_area,
            target_layer=self.layer,
            add_to_items=True
        )

# Example usage:
"""
# Method 1: Directly create and customize object groups
descriptors = RectElement.get_default_descriptors()
objects_group = descriptors[RectElement.Resources.OBJECTS.value]

# Add a simple building
objects_group.add_object(
    resource_id="house",
    image="assets/buildings/house.png",
    width=2,
    height=2,
    collision=True
)

# Add a shop with special functions
objects_group.add_object(
    resource_id="shop",
    name="Magic Shop",
    image="assets/buildings/shop.png",
    width=3,
    height=2,
    collision=True,
    functions=["shop", "save_point"]
)

# Add a rotatable decoration
objects_group.add_object(
    resource_id="statue",
    name="Dragon Statue",
    image="assets/decorations/statue.png",
    width=1,
    height=1,
    collision=False,
    rotation=45,
    visible=True
)

# Create an element instance
rect = RectElement(
    name="building_area",
    x=10,
    y=10,
    width=3,
    height=2,
    descriptors=descriptors
)

# Use factory method to create preset elements
town_center = RectElement.create_town_buildings(x=5, y=5)

# Create elements from configuration
config_data = {
    "name": "castle",
    "x": 20,
    "y": 20,
    "width": 5,
    "height": 4,
    "objects": [
        {
            "id": "castle_main",
            "name": "Castle Main Building",
            "image": "assets/buildings/castle_main.png",
            "width": 5,
            "height": 4,
            "collision": True,
            "functions": ["save_point", "quest_hub"],
            "visible": True
        },
        {
            "id": "castle_tower",
            "name": "Castle Tower",
            "image": "assets/buildings/castle_tower.png",
            "width": 2,
            "height": 3,
            "collision": True,
            "visible": True
        }
    ]
}
castle = RectElement.create_from_config(config_data)

# Use in async context:
async def build_elements(preloader, map_cache):
    # Preload resources
    await rect.preload(preloader)
    await town_center.preload(preloader)
    await castle.preload(preloader)
    
    # Build to map
    await rect.build(map_cache)
    await town_center.build(map_cache)
    await castle.build(map_cache)
""" 