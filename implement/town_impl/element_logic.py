from tiled_master import MapElement, MapCache
from implement.town_impl.config import structure_layer, house_layer

class TownLogic(MapElement):
    def __init__(self):
        super().__init__(name="town_logic")

    def _setup_resources(self):
        pass

    async def build(self, map_cache: MapCache):
        map_cache.clear_layer(structure_layer)
        map_cache.clear_layer(house_layer)


