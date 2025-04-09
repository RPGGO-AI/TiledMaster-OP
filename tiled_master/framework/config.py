import os
from tiled_master.utils.globalvaris import WORKSPACE_FOLDER
from tiled_master.utils.utils import getCacheFolder
from tiled_master.framework.schema import *

# default values
item_layer = 0
obstacle_layer = 1
cover_layer = 2
tile_width = 16
tile_height = 16

# path
temp_file_folder_name = "map_gen"
temp_subimage_file_folder_template = os.path.join(getCacheFolder(temp_file_folder_name), "{map_id}/subimage")
temp_asset_file_folder_template = os.path.join(getCacheFolder(temp_file_folder_name), "{map_id}/asset")
temp_tileset_folder_template = os.path.join(f"{getCacheFolder(temp_file_folder_name)}", "{map_id}/tileset")

temp_root_folder_template = os.path.join(getCacheFolder(temp_file_folder_name), "{map_id}")
temp_map_json_template = os.path.join(getCacheFolder(temp_file_folder_name), "{map_id}/map.json")
temp_preview_image_template = os.path.join(getCacheFolder(temp_file_folder_name), "{map_id}/preview.png")

place_holder_tile_path = f"{WORKSPACE_FOLDER}/assets/placeholder.png"
place_holder_texture = TextureTile(
    name="placeholder",
    type="tile",
    image_path=place_holder_tile_path,
    tileset_id=1,
    local_id=1
)