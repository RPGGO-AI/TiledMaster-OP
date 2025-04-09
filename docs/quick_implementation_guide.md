# TiledMaster Quick Implementation Guide

## Introduction

TiledMaster is a flexible tile-based map generation framework designed for procedural map generation. This guide will help you quickly understand the core concepts of the framework and implement your own custom map generator.

## Core Concepts

TiledMaster is based on the following key concepts:

1. **MapElement**: Responsible for generating specific aspects of the map (terrain, buildings, vegetation, etc.)
2. **MapBuilder**: Combines multiple elements to build a complete map
3. **MapCache**: The core structure for storing and manipulating map data
4. **Resource Descriptors**: Define the graphical resources used by elements

## Quick Start

### 1. Creating a Custom MapElement

Map elements are the building blocks of TiledMaster. Each element is responsible for generating a specific aspect of the map. Here's a simple example of a forest ground element:

```python
from enum import Enum
from typing import Optional

from tiled_master import MapElement, MapCache
from tiled_master.methods import NoiseMap
from tiled_master.utils.logger import logger

class ForestGroundElement(MapElement):
    """Forest ground element, responsible for generating the ground part of the forest"""
    
    class Resources(Enum):
        """Define resource groups needed by the element"""
        GRASS_TILES = "grass_tiles"
        DIRT_TILES = "dirt_tiles"
    
    def __init__(self, name: str, moisture: int = 3, descriptors: Optional[dict] = None):
        """
        Initialize the forest ground element
        
        Args:
            name: Element name
            moisture: Moisture level (1-5), affects the ratio of grass to dirt
            descriptors: Optional external resource descriptors
        """
        self.moisture = moisture
        super().__init__(name=name, descriptors=descriptors)
    
    def _setup_resources(self):
        """Configure the resources needed by the element"""
        # Add and configure grass tile group
        grass_group = self._add_tile_group(self.Resources.GRASS_TILES.value)
        grass_group.add_tile(
            resource_id="grass_light",
            image="assets/forest/grass_light.png"
        ).add_tile(  # Method chaining for cleaner configuration
            resource_id="grass_medium",
            image="assets/forest/grass_medium.png",
            rate=2  # Increase occurrence rate
        ).add_tile(
            resource_id="grass_dark",
            image="assets/forest/grass_dark.png"
        )
        
        # Add and configure dirt tile group
        dirt_group = self._add_tile_group(self.Resources.DIRT_TILES.value)
        dirt_group.add_tile(
            resource_id="dirt_dry",
            image="assets/forest/dirt_dry.png"
        ).add_tile(
            resource_id="dirt_wet",
            image="assets/forest/dirt_wet.png"
        ).add_tile(
            resource_id="dirt_stones",
            image="assets/forest/dirt_stones.png",
            rate=0.5  # Decrease occurrence rate
        )
    
    async def build(self, map_cache: MapCache):
        """Build the forest ground"""
        logger.info(f"Generating forest ground, moisture level: {self.moisture}")
        
        # Access preloaded resources
        grass_tiles = self.loaded_resources[self.Resources.GRASS_TILES.value]
        dirt_tiles = self.loaded_resources[self.Resources.DIRT_TILES.value]
        
        # Use noise to generate terrain
        width, height = map_cache.width, map_cache.height
        noise_map = NoiseMap(width, height, map_cache.random_seed)
        noise_map.generate_perlin_noise(scale=30)
        
        # Adjust threshold based on moisture
        dirt_threshold = 0.4 - (self.moisture * 0.05)
        
        # Prepare placement areas
        grass_area = []
        dirt_area = []
        
        # Distribute terrain based on noise
        for y in range(height):
            for x in range(width):
                noise_value = noise_map.noise_map[y][x]
                if noise_value > dirt_threshold:
                    grass_area.append((x, y))
                else:
                    dirt_area.append((x, y))
        
        # Place tiles on the map
        map_cache.drop_tiles_from_tilegroup(grass_tiles, grass_area, 0)  # Place grass on layer 0
        map_cache.drop_tiles_from_tilegroup(dirt_tiles, dirt_area, 0)    # Place dirt on layer 0
        
        logger.info("Forest ground generation complete")
```

### 2. Creating a Trees Element

Next, create an element to generate trees:

```python
class ForestTreesElement(MapElement):
    """Forest trees element, responsible for generating trees in the forest"""
    
    class Resources(Enum):
        """Define resource groups needed by the element"""
        TREE_OBJECTS = "tree_objects"
    
    def __init__(self, name: str, density: int = 3, variation: int = 3, descriptors: Optional[dict] = None):
        """
        Initialize the forest trees element
        
        Args:
            name: Element name
            density: Tree density (1-5)
            variation: Tree variation (1-5)
            descriptors: Optional external resource descriptors
        """
        self.density = density
        self.variation = variation
        self.trees = []  # Store tree position information
        super().__init__(name=name, descriptors=descriptors)
    
    def _setup_resources(self):
        """Configure the resources needed by the element"""
        # Add tree object group
        tree_group = self._add_object_group(self.Resources.TREE_OBJECTS.value)
        
        # Add different types of trees, controlled by the variation parameter
        base_rate = 1.0
        if self.variation >= 1:
            tree_group.add_object(
                resource_id="pine_tree",
                image="assets/forest/pine_tree.png",
                width=2,
                height=3,
                collision=True,
                rate=base_rate
            )
        
        if self.variation >= 2:
            tree_group.add_object(
                resource_id="oak_tree",
                image="assets/forest/oak_tree.png",
                width=3,
                height=4,
                collision=True,
                rate=base_rate * 0.8
            )
        
        if self.variation >= 3:
            tree_group.add_object(
                resource_id="birch_tree",
                image="assets/forest/birch_tree.png",
                width=2,
                height=4,
                collision=True,
                rate=base_rate * 0.7
            )
        
        if self.variation >= 4:
            tree_group.add_object(
                resource_id="dead_tree",
                image="assets/forest/dead_tree.png",
                width=2,
                height=3,
                collision=True,
                rate=base_rate * 0.4
            )
        
        if self.variation >= 5:
            tree_group.add_object(
                resource_id="ancient_tree",
                image="assets/forest/ancient_tree.png",
                width=4,
                height=5,
                collision=True,
                rate=base_rate * 0.2
            )
    
    async def build(self, map_cache: MapCache):
        """Build the forest trees"""
        logger.info(f"Generating forest trees, density level: {self.density}, variation level: {self.variation}")
        
        # Get tree object group resource
        tree_objects = self.loaded_resources[self.Resources.TREE_OBJECTS.value]
        
        # Use noise to generate tree distribution area
        width, height = map_cache.width, map_cache.height
        noise_map = NoiseMap(width, height, map_cache.random_seed)
        noise_map.generate_perlin_noise(scale=50, octaves=4)
        
        # Adjust attempt count and threshold based on density
        max_attempts = int(width * height * (self.density * 0.01))
        threshold = 0.65 - (self.density * 0.05)
        
        # Collect potential tree positions
        potential_positions = []
        for y in range(height):
            for x in range(width):
                if noise_map.noise_map[y][x] > threshold:
                    potential_positions.append((x, y))
        
        # Randomly shuffle positions
        map_cache.rand.shuffle(potential_positions)
        
        # Limit the number of positions to try
        target_positions = potential_positions[:max_attempts]
        
        # Place trees
        for x, y in target_positions:
            # Create a temporary map copy for trying
            temp_map = map_cache.create_copy()
            
            # Randomly select a tree object
            obj_texture = temp_map.rand.weighted_choice(tree_objects.textures)
            
            # Calculate placement position (centered)
            tree_x = x - obj_texture.width // 2
            tree_y = y - obj_texture.height // 2
            
            # Check if placement is possible (avoid water and roads)
            can_place = not any(
                temp_map.check_exists(tx, ty, 1) or temp_map.check_exists(tx, ty, 2)
                for tx in range(tree_x, tree_x + obj_texture.width)
                for ty in range(tree_y, tree_y + obj_texture.height)
            )
            
            # If placement is possible, place the tree
            if can_place and tree_x >= 0 and tree_y >= 0 and tree_x + obj_texture.width < width and tree_y + obj_texture.height < height:
                if temp_map.drop_object(tree_x, tree_y, 3, obj_texture):  # Place tree on layer 3
                    map_cache.assign(temp_map)
                    self.trees.append({"x": tree_x, "y": tree_y, "width": obj_texture.width, "height": obj_texture.height})
        
        logger.info(f"Forest trees generation complete, generated {len(self.trees)} trees")
```

### 3. Integrating the Map Generator

Now, create a map generator that integrates these elements:

```python
import asyncio
from tiled_master import MapBuilder, CollisionElement
from forest_ground import ForestGroundElement
from forest_trees import ForestTreesElement

class ForestMapSetting:
    """Forest map configuration"""
    def __init__(self, 
                 size: str = "medium",    # Map size: small, medium, large
                 moisture: int = 3,       # Moisture level: 1-5
                 density: int = 3,        # Tree density: 1-5
                 variation: int = 3):     # Tree variation: 1-5
        self.size = size
        self.moisture = moisture
        self.density = density
        self.variation = variation

class ForestMapGenerator:
    """Forest map generator"""
    
    def __init__(self, map_id: str, setting: ForestMapSetting = None):
        """
        Initialize the forest map generator
        
        Args:
            map_id: Map ID
            setting: Forest map configuration, uses default if not provided
        """
        self.map_id = map_id
        self.setting = setting or ForestMapSetting()
        
        # Determine map dimensions based on size setting
        if self.setting.size == "small":
            self.width, self.height = 40, 40
        elif self.setting.size == "medium":
            self.width, self.height = 80, 80
        else:  # large
            self.width, self.height = 120, 120
    
    async def build_map(self, preview=False):
        """
        Build the forest map
        
        Args:
            preview: Whether to preview the map
            
        Returns:
            json_path: Path to the exported JSON file
            image_path: Path to the preview image
        """
        # Create map builder
        builder = MapBuilder(
            map_id=self.map_id,
            width=self.width,
            height=self.height
        )
        
        # Add ground element
        ground = ForestGroundElement(
            name="forest_ground",
            moisture=self.setting.moisture
        )
        builder.add_element(ground)
        
        # Add trees element
        trees = ForestTreesElement(
            name="forest_trees",
            density=self.setting.density,
            variation=self.setting.variation
        )
        builder.add_element(trees)
        
        # Add collision element (handles collision detection)
        builder.add_element(CollisionElement(name="collision"))
        
        # Build the map
        await builder.build()
        
        # Export and preview
        json_path = builder.export_map()
        image_path = builder.preview_map(display=preview)
        
        return json_path, image_path

# Usage example
async def generate_forest_maps():
    """Generate different types of forest maps"""
    # Dense pine forest
    dense_pine = await ForestMapGenerator(
        map_id="dense_pine_forest",
        setting=ForestMapSetting(moisture=4, density=5, variation=2)
    ).build_map(preview=True)
    print(f"Dense pine forest exported to: {dense_pine[0]}")
    
    # Mixed woodland
    mixed_woodland = await ForestMapGenerator(
        map_id="mixed_woodland",
        setting=ForestMapSetting(size="large", moisture=3, density=3, variation=5)
    ).build_map(preview=True)
    print(f"Mixed woodland exported to: {mixed_woodland[0]}")
    
    # Sparse birch grove
    sparse_birch = await ForestMapGenerator(
        map_id="sparse_birch",
        setting=ForestMapSetting(size="small", moisture=2, density=2, variation=3)
    ).build_map(preview=True)
    print(f"Sparse birch grove exported to: {sparse_birch[0]}")

if __name__ == "__main__":
    asyncio.run(generate_forest_maps())
```

## Advanced Features

### 1. Noise Map Generation

TiledMaster provides built-in noise map generation tools to create natural-looking terrain:

```python
from tiled_master.methods import NoiseMap

# Create a noise map
noise_map = NoiseMap(width, height, seed)

# Generate Perlin noise
noise_map.generate_perlin_noise(scale=30, octaves=3)

# Generate double Perlin noise (more complex terrain)
noise_map.generate_double_perlin_noise(scale1=30, scale2=10)

# Generate natural river using thresholds
river_tiles = noise_map.generate_natural_river(scale=2)

# Generate tree area
tree_area = noise_map.generate_tree_area(density=3)
```

### 2. Resource Descriptors

TiledMaster uses resource descriptors to define and load graphical resources:

```python
# Get the default resource descriptors for an element
descriptors = MyElement.get_default_descriptors()

# Modify the descriptors
tile_group = descriptors[MyElement.Resources.TILES.value]
tile_group.add_tile("custom_tile", "path/to/custom_tile.png", rate=2)

# Create an element with the modified descriptors
element = MyElement("my_element", descriptors=descriptors)
```

### 3. Map Cache Operations

The MapCache provides many methods to manipulate map data:

```python
# Check if a position already has content
if map_cache.check_exists(x, y, layer):
    # This position already has content
    pass

# Create a temporary map copy for trying
temp_map = map_cache.create_copy()
if temp_map.drop_object(x, y, layer, object_texture):
    # Placement successful, apply changes
    map_cache.assign(temp_map)

# Get all content in a specific layer
layer_contents = map_cache.get_layer(layer)

# Place tiles from a tile group
map_cache.drop_tiles_from_tilegroup(tile_group, positions, layer)

# Place an object
map_cache.drop_object(x, y, layer, object_texture)
```

## Data Flow

The TiledMaster workflow is as follows:

1. **Initialize MapBuilder**: Define map size and basic properties
2. **Create and Add MapElements**: Each element is responsible for a specific part of the map
3. **Call builder.build()**:
   - Preload all resources
   - Create MapCache
   - Call each element's build method
4. **Export Map**: Export the map in Tiled format
5. **Generate Preview**: Optionally generate a map preview image

## Best Practices

1. **Use Internal Resource Configuration**: Encapsulate resource configuration within elements for simpler usage
2. **Separate Concerns**: Each element should focus on a specific function (terrain, buildings, vegetation, etc.)
3. **Use Method Chaining**: Make resource configuration more concise with method chaining
4. **Noise Map Strategy**: Use appropriate noise maps to generate natural terrain
5. **Temporary Map Trials**: Use temporary map copies for trial placements, applying only successful ones
6. **Collision and Cover Detection**: Always add collision and cover elements to your map

## Sample Project Structure

```
my_map_generator/
├── assets/
│   └── forest/
│       ├── grass_light.png
│       ├── grass_medium.png
│       └── ...
├── elements/
│   ├── forest_ground.py
│   ├── forest_trees.py
│   └── ...
├── generators/
│   └── forest_generator.py
└── main.py
```

That's it! Now you understand how to use the TiledMaster framework to quickly implement custom map generators. You can extend these examples according to your needs to create more complex maps. 