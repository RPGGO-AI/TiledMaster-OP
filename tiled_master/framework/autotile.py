import json
from tiled_master.framework.map_cache import MapCache
from tiled_master.utils.globalvaris import WORKSPACE_FOLDER

autotile_path_mapping = {
    "inner16": f"{WORKSPACE_FOLDER}/configs/autotile_mapping/inner16.json",
    "blob47": f"{WORKSPACE_FOLDER}/configs/autotile_mapping/blob47.json"
}


class AutoTile:
    def __init__(self, autotile_type="tile48"):
        self.neighbors_offsets = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]
        autotile_mapping_path = autotile_path_mapping[autotile_type]
        with open(autotile_mapping_path, "r") as file:
            data = json.load(file)
        self.decimal_to_local_id = data

    def get_autotile_local_id(self,
                              map_cache: MapCache,
                              x: int,
                              y: int,
                              layer: int) -> int | None:
        bitmask = 0
        for bit_index, (dx, dy) in enumerate(self.neighbors_offsets):
            nx, ny = x + dx, y + dy
            if not (0 <= nx < map_cache.width and 0 <= ny < map_cache.height):
                bitmask |= (1 << bit_index)
                continue
            if map_cache.check_exists(nx, ny, layer):
                bitmask |= (1 << bit_index)
        if bitmask == 255:
            return None
        else:
            local_id = self.decimal_to_local_id.get(str(bitmask), None)
            return local_id
        
    def get_base_tile_local_id(self):
        return self.decimal_to_local_id.get("255", None)