# import random
# from app.framework.node import NodeDot
# from app.framework.rect_node import RectNode


# class Drop:
#     def __init__(self, map_cache, random_seed: str):
#         self.map_cache = map_cache
#         self.rand = random.Random(random_seed)
#         self.drops: list[NodeDot] = []

#     def random_batch_drop(self, region: tuple[int, int, int, int], drop_count):
#         """
#         在给定的区域内随机放置一定数量的点。

#         参数:
#           region: (x, y, width, height) - 放置区域的左上角坐标与尺寸。
#           count_range: (min_count, max_count) - 随机放置点数量的范围。

#         返回:
#           放置的点列表。
#         """
#         x, y, width, height = region

#         self.drops.clear()
#         for idx in range(drop_count):
#             drop_x = self.rand.randint(x, x + width - 1)
#             drop_y = self.rand.randint(y, y + height - 1)
#             node_dot = NodeDot(drop_x, drop_y, node_id=idx + 1)
#             self.drops.append(node_dot)

#         return self.drops

#     def randomly_drop_rect(self, region: tuple[int, int, int, int], target_layer, rect_width=None, rect_height=None, obj_texture=None, add_obj_to_cache=False) -> RectNode | None:
#         x, y, width, height = region
#         if rect_width is None:
#             rect_width = self.rand.randint(8, 12)
#         if rect_height is None:
#             rect_height = self.rand.randint(6, 8)
#         rect_x = self.rand.randint(x, x + width - 1 - rect_width)
#         rect_y = self.rand.randint(y, y + height - 1 - rect_height)
#         rect_region = (rect_x, rect_y, rect_width, rect_height)
#         if obj_texture is None:
#             return RectNode.create_placeholder(self.map_cache, rect_region, target_layer)
#         else:
#             return RectNode.created_from_obj_texture(self.map_cache, rect_x, rect_y, target_layer, obj_texture, add_obj_to_cache)
