import os

IMPLEMENT_FOLDER = os.path.dirname(os.path.abspath(__file__))
CONFIG_FOLDER = IMPLEMENT_FOLDER + "/config_jsons"

SUMMER_CONFIG_PATH = CONFIG_FOLDER + "/outdoor_summer.json"
WINTER_CONFIG_PATH = CONFIG_FOLDER + "/outdoor_winter.json"
DESERT_CONFIG_PATH = CONFIG_FOLDER + "/outdoor_desert.json"
MODERN_CONFIG_PATH = CONFIG_FOLDER + "/outdoor_modern.json"
MUD_CONFIG_PATH = CONFIG_FOLDER + "/outdoor_mud.json"

USER_CONFIG_PATH = CONFIG_FOLDER + "/map_user_config.json"

layer_nums = 10
# 导出地图时形成的层
item_layer = 0
obstacle_layer = 1
cover_layer = 2
ground_layer = 3
water_layer = 4
walls_layer = 4
plants_layer = 5
road_layer = 6
tree_layer = 7
structure_layer = 8  # 最后导出地图时会被扔掉
house_layer = 9  # 最后导出地图时会被扔掉