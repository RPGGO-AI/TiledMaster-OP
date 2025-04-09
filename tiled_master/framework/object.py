from typing import Dict
import json
from tiled_master.utils.logger import logger


class Object:
    def __init__(
        self,
        obj_id: int = 0,
        name: str = "",
        type_: str = "",
        x: int = 0,
        y: int = 0,
        original_width: int = 0,
        original_height: int = 0,
        width: int = 0,
        height: int = 0,
        functions: list = None,
        rotation: float = 0.0,
        visible: bool = True,
        image: str = "",
        image_path: str = "",
    ):
        """
        Initialize an object instance.
        """
        self.id = obj_id
        self.name = name
        self.type = type_
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.original_width = original_width
        self.original_height = original_height
        self.rotation = rotation
        self.visible = visible
        self.properties = []
        self._apply_image_to_properties(image)
        self._apply_image_path_to_properties(image_path)
        self._apply_functions_to_properties(functions)

    def _apply_image_to_properties(self, image):
        self.properties.append(
            {
                "name": "texture",
                "type": "string",
                "value": image
            }
        )

    def _apply_image_path_to_properties(self, image_path):
        self.properties.append(
            {
                "name": "image_path",
                "type": "string",
                "value": image_path
            }
        )

    def _apply_functions_to_properties(self, functions):
        if functions is None:
            functions = []
        self.properties.append(
            {
                "name": "functions",
                "type": "string",
                "value": json.dumps(functions)
            }
        )

    def to_dict(self) -> dict:
        """
        Export the object as a dictionary structure.
        """
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "x": self.x,
            "y": self.y,
            "original_width": self.original_width,
            "original_height": self.original_height,
            "width": self.width,
            "height": self.height,
            "rotation": self.rotation,
            "visible": self.visible,
            "properties": self.properties
        }


class ItemLayer:
    def __init__(
            self,
            layer_id: int,
            name: str,
            visible: bool = True,
            opacity: float = 1.0,
            x: int = 0,
            y: int = 0
    ):
        """
        Initialize an item layer object.

        :param layer_id: Unique ID of the layer
        :param name: Layer name (e.g., "Items")
        :param visible: Whether the layer is visible
        :param opacity: Opacity (0~1)
        :param x: Starting X coordinate of the layer in the map
        :param y: Starting Y coordinate of the layer in the map
        """
        self.type = "objectgroup"
        self.id = layer_id
        self.name = name
        self.visible = visible
        self.opacity = opacity
        self.x = x
        self.y = y

        self.next_id = 1
        self.id_object_map: Dict[int, Object] = {}

    def add_object(self, obj: Object):
        """
        Add an object to the item layer.

        :param obj: Object instance.
        """
        if obj.id:
            if obj.id not in self.id_object_map:
                self.id_object_map[obj.id] = obj
                if obj.id >= self.next_id:
                    self.next_id = obj.id + 1
                    logger.warning("what? this really happens?")

        else:
            obj.id = self.next_id
            self.id_object_map[obj.id] = obj
            self.next_id += 1

    def to_dict(self) -> dict:
        """
        Export to a structure similar to a section in Tiled JSON.
        """
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "objects": [obj.to_dict() for obj in self.id_object_map.values()],
            "visible": self.visible,
            "opacity": self.opacity,
            "x": self.x,
            "y": self.y
        }