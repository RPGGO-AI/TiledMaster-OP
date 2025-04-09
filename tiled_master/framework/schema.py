from __future__ import annotations
from pydantic import BaseModel, Field, model_validator
from typing import List, Union, Dict, Any, Tuple, Optional
from tiled_master.utils.globalvaris import TreeLevel, WaterLevel, SceneLevel, LAYOUT
from tiled_master.utils.exception import BadRequestException


# Resource Descriptors
class ResourceDescriptor(BaseModel):
    """Base class for resource descriptors"""
    resource_id: str
    resource_type: str


class TileDescriptor(ResourceDescriptor):
    """Descriptor for a single tile"""
    resource_type: str = "tile"
    image: str
    name: Optional[str] = None
    collision: bool = False
    cover: bool = False
    rate: int = 1
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.name is None:
            self.name = self.resource_id


class AutoTileDescriptor(ResourceDescriptor):
    """Descriptor for an auto tile"""
    resource_type: str = "auto_tile"
    image: str
    name: Optional[str] = None
    method: str = "tile48"
    collision: bool = False
    cover: bool = False
    rate: int = 1
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.name is None:
            self.name = self.resource_id


class TileGroupDescriptor(ResourceDescriptor):
    """Descriptor for a tile group"""
    resource_type: str = "tile_group"
    scale: int = -1
    tiles: List[TileDescriptor] = Field(default_factory=list)
    auto_tiles: List[AutoTileDescriptor] = Field(default_factory=list)
    
    def add_tile(self, resource_id: str, image: Optional[str] = None, **kwargs) -> 'TileGroupDescriptor':
        """Add a tile to this group"""
        tile = TileDescriptor(
            resource_id=resource_id,
            image=image,
            name=kwargs.get("name", None),
            collision=kwargs.get("collision", False),
            cover=kwargs.get("cover", False),
            rate=kwargs.get("rate", 1)
        )
        self.tiles.append(tile)
        return self
        
    def add_auto_tile(self, resource_id: str, image: Optional[str] = None, **kwargs) -> 'TileGroupDescriptor':
        """Add an auto tile to this group"""
        auto_tile = AutoTileDescriptor(
            resource_id=resource_id,
            image=image,
            name=kwargs.get("name", None),
            method=kwargs.get("method", "tile48"),
            collision=kwargs.get("collision", False),
            cover=kwargs.get("cover", False),
            rate=kwargs.get("rate", 1)
        )
        self.auto_tiles.append(auto_tile)
        return self


class ObjectDescriptor(ResourceDescriptor):
    """Descriptor for a single object"""
    resource_type: str = "object"
    name: Optional[str] = None
    image: Optional[str] = None
    width: int = 1
    height: int = 1
    collision: bool = False
    cover: bool = False
    rate: int = 1
    functions: List[str] = Field(default_factory=list)
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.name is None:
            self.name = self.resource_id


class ObjectGroupDescriptor(ResourceDescriptor):
    """Descriptor for an object group"""
    resource_type: str = "object_group"
    scale: int = -1
    objects: List[ObjectDescriptor] = Field(default_factory=list)
    
    def add_object(self, resource_id: str, image: Optional[str] = None, **kwargs) -> 'ObjectGroupDescriptor':
        """Add an object to this group"""
        obj = ObjectDescriptor(
            resource_id=resource_id,
            name=kwargs.get("name", None),
            image=image,
            width=kwargs.get("width", 1),
            height=kwargs.get("height", 1),
            collision=kwargs.get("collision", False),
            cover=kwargs.get("cover", False),
            functions=kwargs.get("functions", [])
        )
        self.objects.append(obj)
        return self


# Tile
class TextureAutoTile(BaseModel):  # This is a spec tileset with 6*8 unique tiles
    name: str
    type: str = "autotile"
    method: str = "tile48"
    image_path: str = ""
    collision: bool = False
    cover: bool = False
    rate: int = 1
    tileset_id: int = 1


class TextureTile(BaseModel):
    name: str
    type: str = "tile"
    image_path: str = ""
    collision: bool = False
    cover: bool = False
    rate: int = 1
    tileset_id: int
    local_id: int


class TileGroup(BaseModel):
    type: str = "tilegroup"
    textures: List[Union[TextureAutoTile, TextureTile]]
    scale: int = 2


# Object
class Blueprint(BaseModel):
    texture: TextureTile
    relative_x: int
    relative_y: int

    @property
    def relative_coordinates(self) -> Tuple[int, int]:
        return self.relative_x, self.relative_y


class TextureObject(BaseModel):
    name: str
    type: str = "object"
    shape: str = "rectangle"
    width: int
    height: int
    original_width: int
    original_height: int
    functions: list = Field(default_factory=list)
    image_path: str = ""
    image_url: str = ""
    collision: bool = False
    cover: bool = False
    visible: bool = True
    rotation: int = 0
    rate: int = 1
    blueprints: List[Blueprint]

    def get_blueprints_area(self, x, y, relative="left_top"):
        if relative != "left_top":
            raise ValueError("relative must be 'left_top'")
        area = []
        for bluepr in self.blueprints:
            area.append((x+bluepr.relative_coordinates[0],y+bluepr.relative_coordinates[1]))
        return area


class ObjectGroup(BaseModel):
    type: str = "objectgroup"
    textures: List[TextureObject]
    scale: int = 2


# Tileset
class Tileset(BaseModel):
    tileset_id: int
    name: str
    columns: int
    firstgid: int
    image: str
    imagewidth: int
    imageheight: int
    spacing: int
    margin: int
    tilecount: int
    tilewidth: int
    tileheight: int



