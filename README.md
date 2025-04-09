# TiledMaster

A python tiled-map framework for procedural map generation.

## Introduction

TiledMaster is a flexible framework for generating tile-based maps. It provides a component-based architecture that allows developers to create various map types by combining different elements. The framework handles resource management, map construction, and export to standard Tiled format.

## Design Philosophy and Background

TiledMaster emerged from our exploration of procedural map generation and the integration possibilities with Large Language Model (LLM) Agents. We found that while the Tiled editor has become an industry-standard tool for game map creation, procedural map generation still requires starting from scratch, making it difficult to quickly implement and test automation processes and algorithms.

Our core philosophy is simple: **let developers focus exclusively on resource configuration and placement algorithms**. We believe that entry-level developers should not need to interact with the intricate any details of the Tiled format or resource management systems.

TiledMaster aims to provide students and developers who want to conduct algorithm research and development using Tiled and Python with a tool to quickly implement and validate their algorithmic ideas. We believe that by simplifying technical barriers, more innovative map generation methods will become possible.

The long-term goal of TiledMaster is to build a Model Context Protocol (MCP) project for Tiled maps. While there is still significant work ahead, we have already taken important first steps toward this vision.

## Core Design

TiledMaster uses an element-driven approach to map generation. Each element is responsible for a specific aspect of the map (terrain, buildings, vegetation, etc.) and can be combined to create complex maps. The framework provides:

- Automatic resource management and loading
- Efficient map data structures
- Algorithm utilities for procedural generation
- Standard map format export
- LLM Agent-friendly interfaces for AI-assisted generation

## Getting Started

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/TiledMaster.git

# Install requirements
pip install -r requirements.txt
```

### Example Implementations

TiledMaster comes with several example implementations to help you get started. These examples are located in the `implement` directory:

- `town_impl` - A complete town map generator implementation
- `room_impl` - A dungeon room generator implementation

Each implementation demonstrates different aspects of the framework and can be used as a reference for your own projects.

### Basic Usage

```python
import asyncio
from tiled_master import MapBuilder
from your_elements import YourElement

async def generate_map():
    # Create a map builder
    builder = MapBuilder(
        map_id="your_map_id",
        width=80,
        height=40
    )
    
    # Add elements
    builder.add_element(YourElement("element_name"))
    
    # Build the map
    await builder.build()
    
    # Export and preview
    json_path = builder.export_map()
    preview_path = builder.preview_map(display=True)
    
    print(f"Map exported to: {json_path}")
    print(f"Preview saved to: {preview_path}")

if __name__ == "__main__":
    asyncio.run(generate_map())
```

## Creating Custom Elements

TiledMaster's key strength is its extensibility through custom elements. Elements are the building blocks of map generation, and developers can create specialized elements for different map features.

### Element Implementation Approaches

There are two main approaches to implementing map elements:

#### 1. Elements with Externally Configured Resources

In this approach, resource descriptors are provided externally when instantiating the element:

```python
# Create descriptors
descriptors = MyElement.get_default_descriptors()
tile_group = descriptors[MyElement.Resources.TILES.value]
tile_group.add_tile("tile1", "path/to/tile.png")

# Create element with descriptors
element = MyElement("my_element", descriptors=descriptors)
```

#### 2. Elements with Internally Configured Resources (Recommended)

This approach encapsulates resource configuration within the element itself, making usage simpler:

```python
class ForestGroundElement(MapElement):
    """Forest ground element with internally configured resources"""
    
    class Resources(Enum):
        GRASS_TILES = "grass_tiles"
        DIRT_TILES = "dirt_tiles"
    
    def __init__(self, name: str, moisture: int = 3, descriptors: Optional[dict] = None):
        self.moisture = moisture
        super().__init__(name=name, descriptors=descriptors)
    
    def _setup_resources(self):
        """Setup and configure resources internally"""
        # Add and configure grass tiles
        grass_group = self._add_tile_group(self.Resources.GRASS_TILES.value)
        grass_group.add_tile(
            resource_id="grass_light",
            image="assets/forest/grass_light.png"
        ).add_tile(  # Method chaining for cleaner configuration
            resource_id="grass_medium",
            image="assets/forest/grass_medium.png",
            rate=2  # Increased occurrence rate
        )
        
        # Add and configure dirt tiles
        dirt_group = self._add_tile_group(self.Resources.DIRT_TILES.value)
        dirt_group.add_tile(
            resource_id="dirt_dry",
            image="assets/forest/dirt_dry.png"
        ).add_tile(
            resource_id="dirt_stones",
            image="assets/forest/dirt_stones.png"
        )
    
    async def build(self, map_cache: MapCache):
        """Build the forest ground on the map"""
        logger.info(f"Generating forest ground, moisture level: {self.moisture}")
        
        # Access pre-loaded resources
        grass_tiles = self.loaded_resources[self.Resources.GRASS_TILES.value]
        dirt_tiles = self.loaded_resources[self.Resources.DIRT_TILES.value]
        
        # Generate terrain using noise
        width, height = map_cache.width, map_cache.height
        noise_map = NoiseMap(width, height, map_cache.random_seed)
        noise_map._generate_double_perlin_noise(30, 10)
        
        # Adjust thresholds based on moisture
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
        map_cache.drop_tiles_from_tilegroup(grass_tiles, grass_area, 0)
        map_cache.drop_tiles_from_tilegroup(dirt_tiles, dirt_area, 0)
        
        logger.info(f"Forest ground generation complete")
```

Using the element is now extremely simple:

```python
# Simply create the element with desired parameters
forest_ground = ForestGroundElement("forest_ground", moisture=4)
builder.add_element(forest_ground)
```

### Benefits of Internal Resource Configuration

1. **Self-contained components**: Elements encapsulate both behavior and resources
2. **Simplified usage**: No need for external resource configuration
3. **Default logic**: Elements provide sensible defaults based on their purpose
4. **Method chaining**: Cleaner, more readable resource configuration
5. **Strong encapsulation**: Resource configuration logic is tied to element functionality

This approach is particularly well-suited for:
- Examples and tutorials
- Specialized elements designed for specific map types
- Rapid prototyping of different element combinations

The framework still preserves flexibility by allowing external descriptors to override default configurations when needed for highly customized scenarios.

## Complete Example: Forest Map Generator

Below is a complete example demonstrating how to implement a forest map generator using internally configured elements:

```python
import asyncio
from tiled_master import MapBuilder, CollisionElement
from forest_ground import ForestGroundElement
from forest_trees import ForestTreesElement

class ForestMapSetting:
    """Configuration settings for forest maps"""
    def __init__(self, 
                 size: str = "medium",
                 moisture: int = 3,
                 density: int = 3,
                 variation: int = 3):
        self.size = size
        self.moisture = moisture
        self.density = density
        self.variation = variation

class ForestMapGenerator:
    """Forest map generator implementation"""
    
    def __init__(self, map_id: str, setting: ForestMapSetting = None):
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
        """Build the forest map"""
        # Create a map builder
        builder = MapBuilder(
            map_id=self.map_id,
            width=self.width,
            height=self.height
        )
        
        # Add ground element - no external configuration needed
        ground = ForestGroundElement(
            name="forest_ground",
            moisture=self.setting.moisture
        )
        builder.add_element(ground)
        
        # Add trees element - no external configuration needed
        trees = ForestTreesElement(
            name="forest_trees",
            density=self.setting.density,
            variation=self.setting.variation
        )
        builder.add_element(trees)
        
        # Add collision element
        builder.add_element(CollisionElement(name="collision"))
        
        # Build the map
        await builder.build()
        
        # Export and preview
        json_path = builder.export_map()
        image_path = builder.preview_map(display=preview)
        
        return json_path, image_path

# Usage
async def generate_different_forests():
    """Generate different types of forests"""
    # Dense pine forest
    dense_pine = await ForestMapGenerator(
        map_id="dense_pine_forest",
        setting=ForestMapSetting(moisture=4, density=5, variation=2)
    ).build_map(preview=True)
    
    # Mixed woodland
    mixed_woodland = await ForestMapGenerator(
        map_id="mixed_woodland",
        setting=ForestMapSetting(size="large", moisture=3, density=3, variation=5)
    ).build_map(preview=True)
    
    # Sparse birch grove
    sparse_birch = await ForestMapGenerator(
        map_id="sparse_birch",
        setting=ForestMapSetting(size="small", moisture=2, density=2, variation=3)
    ).build_map(preview=True)

if __name__ == "__main__":
    asyncio.run(generate_different_forests())
```

## Advanced Features

TiledMaster provides several advanced features for more complex map generation:

### Procedural Generation Algorithms

The framework includes various algorithms to assist with map generation:

```python
# Noise-based natural terrain
from app.methods import NoiseMap
noise_map = NoiseMap(width, height, seed)
terrain = noise_map.generate_terrain(3)  # Level 3 terrain

# Binary Space Partitioning for room layouts
from app.methods import BSP
regions, corners = BSP(min_size=8, random_seed=seed)(region, width, height)

# Pathfinding for roads and corridors
from app.methods import Pathfinder
paths = Pathfinder(map_cache, width, height).find_corridor_path(start, end, obstacles)
```

### Element Interaction

Elements can interact with each other through the map cache:

```python
# Check if a position contains water
if map_cache.check_exists(x, y, water_layer):
    # This is water, don't place a building here
    pass

# Create a temporary map copy to try placement
temp_map = map_cache.create_copy()
if temp_map.drop_object(x, y, layer, object_texture):
    # Placement successful, apply changes
    map_cache.assign(temp_map)
```

## Documentation

For more detailed information about TiledMaster, please refer to the documentation in the `docs` directory:

- [Core Concepts Guide](docs/core_concepts.md) - Detailed explanation of framework's core components and design philosophy
- [Quick Implementation Guide](docs/quick_implementation_guide.md) - Step-by-step guide to implementing your own map generator
- [API Reference](docs/api_reference.md) - Complete API reference for all framework components

The documentation provides in-depth explanations of how TiledMaster works and how to leverage its full capabilities for your map generation needs.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

