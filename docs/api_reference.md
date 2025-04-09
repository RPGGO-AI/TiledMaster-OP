# TiledMaster API Reference

This document provides reference for the main APIs and methods of the TiledMaster framework, helping developers quickly find and use the framework's functionality.

---

## MapBuilder

The map builder, responsible for organizing elements and building complete maps.

### Constructor

```python
MapBuilder(map_id: str, width: int = 80, height: int = 40, total_layer: int = 10)
```

**Parameters**:
- `map_id` - The unique identifier for the map
- `width` - Map width (in tiles), default 80
- `height` - Map height (in tiles), default 40
- `total_layer` - Total number of layers, default 10

### Methods

---

#### add_element

```python
add_element(element: MapElement) -> MapBuilder
```

Add a map element to the builder. Returns the builder instance to support method chaining.

**Parameters**:
- `element` - The MapElement instance to add

**Return Value**:
- MapBuilder instance (self)

**Example**:
```python
builder = (MapBuilder("my_map")
          .add_element(ground)
          .add_element(river)
          .add_element(trees))
```

---

#### build

```python
async build() -> MapCache
```

Execute the complete build process, including resource preloading, creating map cache, and building all elements.

**Return Value**:
- The completed MapCache instance

**Example**:
```python
map_cache = await builder.build()
```

---

#### export_map

```python
export_map() -> str
```

Export the built map in Tiled JSON format.

**Return Value**:
- Path to the exported JSON file

**Example**:
```python
json_path = builder.export_map()
```

---

#### preview_map

```python
preview_map(display: bool = True) -> str
```

Generate a map preview image.

**Parameters**:
- `display` - Whether to display the preview image, default True

**Return Value**:
- Path to the preview image file

**Example**:
```python
image_path = builder.preview_map(display=True)
```

---

## MapElement

The abstract base class for map elements. All custom elements should inherit from this class.

### Constructor

```python
MapElement(name: str, descriptors: Optional[Dict[str, ResourceDescriptor]] = None, **data)
```

**Parameters**:
- `name` - Element name
- `descriptors` - Optional dictionary of resource descriptors, keys are resource IDs, values are ResourceDescriptor instances
- `**data` - Other initialization data

### Abstract Methods

---

#### _setup_resources

```python
def _setup_resources(self)
```

Abstract method that must be implemented by subclasses. Used to set up the resources needed by the element.

**Example**:
```python
def _setup_resources(self):
    tile_group = self._add_tile_group("my_tiles")
    tile_group.add_tile("tile1", "path/to/tile1.png")
```

---

#### build

```python
async def build(self, map_cache: MapCache)
```

Abstract method that must be implemented by subclasses. Implements the element's building logic.

**Parameters**:
- `map_cache` - MapCache instance, used to access and modify map data

**Example**:
```python
async def build(self, map_cache):
    # Implement building logic
    tiles = self.loaded_resources["my_tiles"]
    positions = [(x, y) for x in range(10) for y in range(10)]
    map_cache.drop_tiles_from_tilegroup(tiles, positions, 0)
```

### Resource Methods

---

#### _add_tile_group

```python
_add_tile_group(resource_id: str, scale: int = -1) -> TileGroupDescriptor
```

Add a tile group resource descriptor.

**Parameters**:
- `resource_id` - Resource unique identifier
- `scale` - Scale factor, default -1

**Return Value**:
- Created TileGroupDescriptor, supports method chaining

**Example**:
```python
grass_group = self._add_tile_group("grass_tiles")
grass_group.add_tile("grass1", "assets/grass1.png")
```

---

#### _add_object_group

```python
_add_object_group(resource_id: str, scale: int = -1) -> ObjectGroupDescriptor
```

Add an object group resource descriptor.

**Parameters**:
- `resource_id` - Resource unique identifier
- `scale` - Scale factor, default -1

**Return Value**:
- Created ObjectGroupDescriptor, supports method chaining

**Example**:
```python
building_group = self._add_object_group("buildings")
building_group.add_object("house", "assets/house.png", width=3, height=2)
```

---

#### _add_tile

```python
_add_tile(resource_id: str, image: str, **kwargs) -> TileDescriptor
```

Add a single tile resource descriptor.

**Parameters**:
- `resource_id` - Resource unique identifier
- `image` - Image path
- `**kwargs` - Other tile properties

**Return Value**:
- Created TileDescriptor

**Example**:
```python
self._add_tile("special_tile", "assets/special.png", rate=2)
```

---

#### _add_auto_tile

```python
_add_auto_tile(resource_id: str, image: str, **kwargs) -> AutoTileDescriptor
```

Add an auto tile resource descriptor, used for continuous tiles (like rivers).

**Parameters**:
- `resource_id` - Resource unique identifier
- `image` - Image path
- `**kwargs` - Other auto tile properties

**Return Value**:
- Created AutoTileDescriptor

**Example**:
```python
self._add_auto_tile("river", "assets/river.png", auto_type="river")
```

---

#### _add_object

```python
_add_object(resource_id: str, name: Optional[str] = None, image: Optional[str] = None, **kwargs) -> ObjectDescriptor
```

Add a single object resource descriptor.

**Parameters**:
- `resource_id` - Resource unique identifier
- `name` - Object display name, defaults to resource_id
- `image` - Image path
- `**kwargs` - Other object properties

**Return Value**:
- Created ObjectDescriptor

**Example**:
```python
self._add_object("tree", image="assets/tree.png", width=2, height=3, collision=True)
```

---

#### get_default_descriptors

```python
@classmethod
get_default_descriptors(cls) -> Dict[str, ResourceDescriptor]
```

Class method to get the default resource descriptors for the element.

**Return Value**:
- Dictionary of default resource descriptors

**Example**:
```python
descriptors = MyElement.get_default_descriptors()
# Modify descriptors
descriptors["my_tiles"].add_tile("custom", "assets/custom.png")
# Create element with modified descriptors
element = MyElement("custom_element", descriptors=descriptors)
```

---

## MapCache

Map cache, stores and manages map data.

### Constructor

```python
MapCache(map_id: str, width: int, height: int, layer_nums: int = 10, random_seed: Optional[int] = None)
```

**Parameters**:
- `map_id` - Map unique identifier
- `width` - Map width (in tiles)
- `height` - Map height (in tiles)
- `layer_nums` - Number of layers, default 10
- `random_seed` - Random seed, default None (system generated)

### Main Methods

#### drop_tiles_from_tilegroup

```python
drop_tiles_from_tilegroup(tile_group: TileGroup, positions: List[Tuple[int, int]], layer: int) -> None
```

Place multiple tiles from a tile group on the specified layer.

**Parameters**:
- `tile_group` - TileGroup instance
- `positions` - List of positions, each position is an (x, y) tuple
- `layer` - Target layer index

**Example**:
```python
positions = [(x, y) for x in range(10) for y in range(10)]
map_cache.drop_tiles_from_tilegroup(grass_tiles, positions, 0)
```

#### drop_object

```python
drop_object(x: int, y: int, layer: int, obj_texture: TextureObject) -> bool
```

Place an object at the specified position.

**Parameters**:
- `x` - X coordinate
- `y` - Y coordinate
- `layer` - Target layer index
- `obj_texture` - TextureObject instance

**Return Value**:
- Whether the placement was successful

**Example**:
```python
if map_cache.drop_object(10, 15, 2, house_texture):
    print("House placed successfully")
```

#### check_exists

```python
check_exists(x: int, y: int, layer: int) -> bool
```

Check if the specified position already has content.

**Parameters**:
- `x` - X coordinate
- `y` - Y coordinate
- `layer` - Layer index

**Return Value**:
- Whether the position already has content

**Example**:
```python
if not map_cache.check_exists(x, y, 1):
    # Position is available, can place content
    map_cache.drop_tile(x, y, 1, tile)
```

#### get_layer

```python
get_layer(layer: int) -> List[Tuple[int, int]]
```

Get all non-empty positions in a specific layer.

**Parameters**:
- `layer` - Layer index

**Return Value**:
- List of positions, each position is an (x, y) tuple

**Example**:
```python
water_positions = map_cache.get_layer(water_layer)
```

#### create_copy

```python
create_copy(seed_offset: int = 0) -> 'MapCache'
```

Create a copy of the map cache, for trial operations.

**Parameters**:
- `seed_offset` - Random seed offset, default 0

**Return Value**:
- New MapCache instance

**Example**:
```python
temp_map = map_cache.create_copy()
if temp_map.drop_object(x, y, layer, obj):
    map_cache.assign(temp_map)
```

#### assign

```python
assign(other: 'MapCache') -> None
```

Assign the content of another map cache to the current map cache.

**Parameters**:
- `other` - Another MapCache instance

**Example**:
```python
temp_map = map_cache.create_copy()
# Modify temp_map
map_cache.assign(temp_map)  # Apply changes
```

---

## Resource Descriptors

### TileGroupDescriptor

Tile group descriptor, containing multiple tiles.

```python
TileGroupDescriptor(resource_id: str, scale: int = -1)
```

**Methods**:

#### add_tile

```python
add_tile(resource_id: str, image: str, rate: float = 1.0, **kwargs) -> 'TileGroupDescriptor'
```

Add a tile to the group.

**Parameters**:
- `resource_id` - Tile unique identifier
- `image` - Image path
- `rate` - Occurrence frequency weight, default 1.0
- `**kwargs` - Other tile properties

**Return Value**:
- TileGroupDescriptor instance (self), supports method chaining

**Example**:
```python
tile_group = TileGroupDescriptor("ground_tiles")
tile_group.add_tile("grass", "assets/grass.png", rate=2)
         .add_tile("dirt", "assets/dirt.png")
```

### ObjectGroupDescriptor

Object group descriptor, containing multiple objects.

```python
ObjectGroupDescriptor(resource_id: str, scale: int = -1)
```

**Methods**:

#### add_object

```python
add_object(resource_id: str, image: str, width: int = 1, height: int = 1, collision: bool = False, cover: bool = False, rate: float = 1.0, **kwargs) -> 'ObjectGroupDescriptor'
```

Add an object to the group.

**Parameters**:
- `resource_id` - Object unique identifier
- `image` - Image path
- `width` - Object width (in tiles), default 1
- `height` - Object height (in tiles), default 1
- `collision` - Whether the object has collision properties, default False
- `cover` - Whether the object has cover properties, default False
- `rate` - Occurrence frequency weight, default 1.0
- `**kwargs` - Other object properties

**Return Value**:
- ObjectGroupDescriptor instance (self), supports method chaining

**Example**:
```python
object_group = ObjectGroupDescriptor("buildings")
object_group.add_object("house", "assets/house.png", width=3, height=2, collision=True)
            .add_object("shed", "assets/shed.png", width=2, height=2, collision=True, rate=0.5)
```

---

## Algorithm Tools

### NoiseMap

Noise map generator, used to generate natural terrain and distributions.

```python
NoiseMap(width: int, height: int, seed: Optional[int] = None)
```

**Parameters**:
- `width` - Map width
- `height` - Map height
- `seed` - Random seed, default None (system generated)

**Methods**:

---

#### generate_perlin_noise

```python
generate_perlin_noise(scale: float = 10.0, octaves: int = 1) -> None
```

Generate Perlin noise.

**Parameters**:
- `scale` - Noise scaling, default 10.0
- `octaves` - Number of noise layers, default 1

**Example**:
```python
noise_map = NoiseMap(80, 40, seed=42)
noise_map.generate_perlin_noise(scale=20, octaves=3)
```

---

#### generate_double_perlin_noise

```python
generate_double_perlin_noise(scale1: float = 30.0, scale2: float = 10.0) -> None
```

Generate double Perlin noise, providing more complex terrain.

**Parameters**:
- `scale1` - First layer noise scaling, default 30.0
- `scale2` - Second layer noise scaling, default 10.0

**Example**:
```python
noise_map = NoiseMap(80, 40, seed=42)
noise_map.generate_double_perlin_noise(scale1=30, scale2=10)
```

---

#### generate_natural_river

```python
generate_natural_river(scale: int = 1) -> List[Tuple[int, int]]
```

Generate natural river distribution.

**Parameters**:
- `scale` - River scale factor, default 1

**Return Value**:
- List of river tile positions, each position is an (x, y) tuple

**Example**:
```python
noise_map = NoiseMap(80, 40, seed=42)
river_positions = noise_map.generate_natural_river(scale=2)
```

---

#### generate_tree_area

```python
generate_tree_area(density: int = 3) -> List[Tuple[int, int]]
```

Generate tree distribution area.

**Parameters**:
- `density` - Density level, default 3

**Return Value**:
- List of possible tree positions, each position is an (x, y) tuple

**Example**:
```python
noise_map = NoiseMap(80, 40, seed=42)
tree_positions = noise_map.generate_tree_area(density=4)
```

---

### Pathfinder

Pathfinding algorithm, used to generate roads and corridors.

```python
Pathfinder(map_cache: MapCache, width: int, height: int)
```

**Parameters**:
- `map_cache` - MapCache instance
- `width` - Map width
- `height` - Map height

**Methods**:

---

#### find_path

```python
find_path(start: Tuple[int, int], end: Tuple[int, int], obstacles: List[Tuple[int, int]] = None) -> List[Tuple[int, int]]
```

Use A* algorithm to find a path from start to end.

**Parameters**:
- `start` - Start coordinates, (x, y) tuple
- `end` - End coordinates, (x, y) tuple
- `obstacles` - List of obstacle positions, default None

**Return Value**:
- List of path positions, each position is an (x, y) tuple

**Example**:
```python
pathfinder = Pathfinder(map_cache, 80, 40)
path = pathfinder.find_path((0, 0), (20, 30), obstacles=water_tiles)
```

---

## Built-in Elements

---

### CollisionElement

Collision element, automatically handles collision areas on the map.

```python
CollisionElement(name: str, descriptors: Optional[Dict[str, ResourceDescriptor]] = None)
```

**Parameters**:
- `name` - Element name
- `descriptors` - Optional resource descriptor dictionary

**Features**:
- Automatically collects objects marked as collision=True on the map
- Adds collision information to the collision layer

**Example**:
```python
builder.add_element(CollisionElement("collision"))
```

---

### CoverElement

Cover element, handles cover effects (such as roofs, tree canopies, etc.).

```python
CoverElement(name: str, descriptors: Optional[Dict[str, ResourceDescriptor]] = None)
```

**Parameters**:
- `name` - Element name
- `descriptors` - Optional resource descriptor dictionary

**Features**:
- Automatically collects objects marked as cover=True on the map
- Adds cover information to the cover layer

**Example**:
```python
builder.add_element(CoverElement("cover"))
```

---

## Utility Functions

---

### Logging Tools

```python
from tiled_master.utils.logger import logger, logger_runtime

# Basic logging
logger.debug("Debug information")
logger.info("General information")
logger.warning("Warning information")
logger.error("Error information")

# Performance timing decorator
@logger_runtime()
def expensive_function():
    # Perform time-consuming operation
    pass

# Async performance timing decorator
@logger_runtime_async()
async def async_expensive_function():
    # Perform async time-consuming operation
    pass
```

---

### File Tools

```python
from tiled_master.utils.utils import read_json, write_json

# Read JSON file
config = read_json("path/to/config.json")

# Write JSON file
write_json("path/to/output.json", data_dict)
```

---

## Constants and Configurations

### Framework Configuration

```python
import tiled_master.framework.config as config

# Tile dimensions
TILE_WIDTH = config.tile_width  # Default 32
TILE_HEIGHT = config.tile_height  # Default 32

# Special layer indices
COLLISION_LAYER = config.obstacle_layer  # Default 8
COVER_LAYER = config.cover_layer  # Default 9
```

---

## Export Format

Maps exported by TiledMaster use the standard Tiled JSON format, which can be opened directly in the Tiled map editor. The basic structure includes:

```json
{
  "width": 80,
  "height": 40,
  "tilewidth": 32,
  "tileheight": 32,
  "type": "map",
  "orientation": "orthogonal",
  "renderorder": "right-down",
  "layers": [
    {
      "id": 0,
      "name": "Layer_1",
      "type": "tilelayer",
      "width": 80,
      "height": 40,
      "data": [...]
    },
    // More layers...
    {
      "id": 8,
      "name": "Obstacles",
      "type": "tilelayer",
      "width": 80,
      "height": 40,
      "data": [...]
    }
  ],
  "tilesets": [
    {
      "firstgid": 1,
      "name": "tileset_1",
      "tilecount": 10,
      "tilewidth": 32,
      "tileheight": 32,
      "image": "path/to/tileset.png"
    }
    // More tilesets...
  ]
}
``` 