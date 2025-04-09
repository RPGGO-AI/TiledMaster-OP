from __future__ import annotations
from pydantic import BaseModel, model_validator
from typing import Any
from tiled_master.utils.globalvaris import TreeLevel, WaterLevel, SceneLevel, LAYOUT
from tiled_master.utils.exception import BadRequestException


class MapGenSetting(BaseModel):
    Layout: dict[str, str]
    Scene: dict[str, str]
    Building: int = 0
    Tree: str | None = None
    Water: str | None = None

    @model_validator(mode='after')
    def validator(cls, values):
        # 使用属性访问来获取字段值，而不是字典的get方法
        if values.Building < 0:
            raise BadRequestException("Building must be non-negative")

        tree = values.Tree
        if tree is not None:
            if tree not in TreeLevel.list:
                raise BadRequestException(f"Tree must be one of {TreeLevel.list}")

        water = values.Water
        if water is not None:
            if water not in WaterLevel.list:
                raise BadRequestException(f"Water must be one of {WaterLevel.list}")

        layout = values.Layout
        if layout is not None:
            layout_name = layout.get("name")  # layout 是字典，此处可以使用get方法
            if layout_name is None or not isinstance(layout_name, str):
                raise BadRequestException("Layout must have string name")
            if layout_name not in LAYOUT.list:
                raise BadRequestException(f"Layout name must be one of {LAYOUT.list}")

        scene = values.Scene
        if scene is not None:
            scene_name = scene.get("name")
            if scene_name is None or not isinstance(scene_name, str):
                raise BadRequestException("Scene must have string name")
            if scene_name not in SceneLevel.list:
                raise BadRequestException(f"Scene name must be one of {SceneLevel.list}")
        return values


class MapGenRequest(BaseModel):
    map_id: str = ""
    config_url: str = ""
    setting: MapGenSetting | None = None
    game_id: str = "collection"


class MapGenResponse(BaseModel):
    json_url: str = ""
    preview_img_url: str = ""
    debug_info: Any | None = None