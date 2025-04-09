import os

IMPLEMENT_FOLDER = os.path.dirname(os.path.abspath(__file__))
CONFIG_FOLDER = IMPLEMENT_FOLDER + "/config_jsons"

ROOM_CONFIG_PATH = CONFIG_FOLDER + "/interior_room.json"

layer_nums = 10
# 导出地图时形成的层
item_layer = 0
obstacle_layer = 1
cover_layer = 2
floor_layer = 3
wall_layer = 4
void_layer = 5
