from enum import Enum
import os
from dotenv import load_dotenv

load_dotenv()

CURRENT_PATH = __file__

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_PATH)))

CACHE_FOLDER = ROOT_PATH + "/cache"
WORKSPACE_FOLDER = ROOT_PATH + "/tiled_master"
IMPLEMENT_FOLDER = ROOT_PATH + "/implement"

# Define a class-level property descriptor.
class classproperty:
    # A descriptor to allow a method to be accessed as a class-level property.
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, instance, owner):
        return self.fget(owner)


class SceneLevel(Enum):
    Summer = "Summer"

    @classproperty
    def list(cls):
        return [member.value for member in cls]

class LAYOUT(Enum):
    Village = "Village"
    Town = "Town"

    @classproperty
    def list(cls):
        return [member.value for member in cls]


class WaterLevel(Enum):
    Scattered = "Pond"
    Standard = "Stream"
    Wide = "River"
    Straight = "Creek"
    Island = "Ocean"
    Coastal = "Coast"

    @classproperty
    def list(cls):
        return [member.value for member in cls]


class TreeLevel(Enum):
    Sparse = "Sparse"
    Patchy = "Slightly Dense"
    Encircle = "Dense"
    Dense_Encircle = "Lush"

    @classproperty
    def list(cls):
        return [member.value for member in cls]