import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from enum import Enum
from typing import Optional

from tiled_master.utils.logger import logger
from tiled_master import MapElement, MapCache
from tiled_master.methods import Dwellings


from implement.room_impl.config import floor_layer, wall_layer, void_layer

# ---------------------------
# Data structures for door installation
# ---------------------------
class RoomTreeNode:
    def __init__(self, room):
        self.room = room
        self.children = []  # list of RoomTreeNode
        self.parent = None  # RoomTreeNode
        # Initially, door info is stored as ((c, r), side).
        # Later, it will be updated to a global pixel rectangle.
        self.door_to_parent = None
        self.external_door = None  # 外界门（不在 root 节点生成，而由最南面的房间生成）

    def __repr__(self):
        return f"RoomTreeNode({self.room}, door={self.door_to_parent}, ext_door={self.external_door})"


class RoomTree:
    def __init__(self, root: RoomTreeNode):
        self.root = root

    def traverse(self):
        # Traverse the tree using DFS.
        stack = [self.root]
        while stack:
            node = stack.pop()
            yield node
            stack.extend(node.children)


# ---------------------------
# RoomNode class definition
# ---------------------------
class Room(MapElement):
    """Room element for indoor spaces"""
    class Resources(Enum):
        FLOOR_TILES = "floor"
        WALL_LV1_TILES = "wall_lv1"
        WALL_LV2_TILES = "wall_lv2"
        ROOF_TILES = "roof"
    
    def __init__(self, 
                 name: str,
                 grid_width: int = 12,
                 grid_height: int = 6,
                 cell_width: int = 4,
                 cell_height: int = 5,
                 line_width: int = 1,
                 descriptors: Optional[dict] = None):
        """
        Initialize the room element
        
        Parameters:
        -----------
        grid_width, grid_height: original grid size (unit: cell)
        cell_width, cell_height: pixel size of a single cell (cell can be rectangular)
        line_width: pixel width of the cell border (wall thickness)
        """
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.line_width = line_width
        self.total_width = grid_width * (cell_width + line_width) + line_width
        self.total_height = grid_height * (cell_height + line_width) + line_width
        super().__init__(name=name, descriptors=descriptors)


        
    def _setup_resources(self):
        """Setup the required resources"""
        self._add_tile_group(self.Resources.FLOOR_TILES.value)
        self._add_tile_group(self.Resources.WALL_LV1_TILES.value)
        self._add_tile_group(self.Resources.WALL_LV2_TILES.value)
        self._add_tile_group(self.Resources.ROOF_TILES.value)
        
    
    async def build(self, map_cache: MapCache):
        """Build the room layout on the map"""
        logger.info("generating room layout")
        
        # Generate rooms and connections using Dwellings
        dwellings = Dwellings(
            self.grid_width, 
            self.grid_height, 
            seed=map_cache.random_seed, 
            num_vertices=6
        )
        result = dwellings.divide_room(
            max_area=8, 
            min_overlap_ratio=0.6, 
            shape_ratio_threshold=0.3, 
            max_iterations=100
        )
        rooms = result["rooms"]
        connections = result["connections"]
        
        # Generate the tiled map
        floor_tiles, wall_tiles, tiled_map  = self.to_tiled(rooms, connections)
        
        # Get resources
        floor_tile_group = self.loaded_resources.get(self.Resources.FLOOR_TILES.value)
        wall_lv1_tile_group = self.loaded_resources.get(self.Resources.WALL_LV1_TILES.value)
        wall_lv2_tile_group = self.loaded_resources.get(self.Resources.WALL_LV2_TILES.value)
        roof_tile_group = self.loaded_resources.get(self.Resources.ROOF_TILES.value)
        
        # Place tiles on the map
        map_cache.drop_tiles_from_tilegroup(floor_tile_group, floor_tiles, floor_layer)
        
        # Add wall decorations for vertical walls
        for (x, y) in wall_tiles:
            if map_cache.check_exists(x, y+1, floor_layer):
                map_cache.drop_tiles_from_tilegroup(wall_lv1_tile_group, [(x, y+1)], wall_layer)        
            if map_cache.check_exists(x, y+2, floor_layer):
                map_cache.drop_tiles_from_tilegroup(wall_lv2_tile_group, [(x, y+2)], wall_layer)
        
        # Fill all areas that are not floor or wall
        all_coords = []
        for y in range(self.total_height):
            for x in range(self.total_width):
                if not map_cache.check_exists(x, y, floor_layer) and not map_cache.check_exists(x, y, wall_layer):
                    all_coords.append((x, y))
        
        map_cache.drop_tiles_from_tilegroup(roof_tile_group, all_coords, void_layer)
        
        logger.info("generate room layout done")

    @staticmethod
    def _find_door_between(room1, room2):
        """
        For two adjacent rooms, find a suitable door location.
        The door is defined as a wall cell from room1 with one side.
        Returns ((c, r), side).
        """
        for cell in room1.cells:
            c, r = cell
            if (c, r - 1) in room2.cells:
                return ((c, r), 'top')
            if (c, r + 1) in room2.cells:
                return ((c, r), 'bottom')
            if (c - 1, r) in room2.cells:
                return ((c, r), 'left')
            if (c + 1, r) in room2.cells:
                return ((c, r), 'right')
        for cell in room2.cells:
            c, r = cell
            if (c, r - 1) in room1.cells:
                return ((c, r), 'bottom')
            if (c, r + 1) in room1.cells:
                return ((c, r), 'top')
            if (c - 1, r) in room1.cells:
                return ((c, r), 'right')
            if (c + 1, r) in room1.cells:
                return ((c, r), 'left')
        logger.warning(f"can't find round between {room1}, {room2}")
        return None

    @staticmethod
    def _find_southern_external_door(room):
        """
        For the given room, choose one cell on its southern border
        and return a door with side 'bottom'.
        If multiple cells share the maximum row, pick the first one.
        """
        # Find the maximum row value in the room's cells.
        max_r = max(r for (c, r) in room.cells)
        # Select one candidate cell with maximum row value.
        candidate_cells = [cell for cell in room.cells if cell[1] == max_r]
        cell = candidate_cells[0]
        return (cell, 'bottom')

    def _build_room_tree(self, rooms, connections):
        """
        Build a RoomTree based on the given rooms and MST connections.
        Here we do not assign an external door on the root node.
        """
        # Build the union of all room cells.
        all_room_cells = set()
        for room in rooms:
            all_room_cells |= room.cells

        # Build an undirected graph adjacency list.
        adj = {room: [] for room in rooms}
        for r1, r2 in connections:
            adj[r1].append(r2)
            adj[r2].append(r1)

        # Choose an arbitrary room as root (no external door here).
        root_room = rooms[0]
        room_to_node = {}
        root_node = RoomTreeNode(root_room)
        room_to_node[root_room] = root_node
        # Do NOT assign external door for root here.
        stack = [root_room]
        visited = {root_room}
        while stack:
            current = stack.pop()
            current_node = room_to_node[current]
            for nbr in adj[current]:
                if nbr in visited:
                    continue
                visited.add(nbr)
                child_node = RoomTreeNode(nbr)
                child_node.parent = current_node
                child_node.door_to_parent = self._find_door_between(current, nbr)
                current_node.children.append(child_node)
                room_to_node[nbr] = child_node
                stack.append(nbr)
        tree = RoomTree(root_node)
        return tree

    def _assign_southern_external_door(self, room_tree):
        """
        Traverse the room_tree, find the southernmost room (largest row index)
        and assign its external door with side 'bottom'.
        """
        southern_node = None
        southern_r = -float('inf')
        for node in room_tree.traverse():
            # For each room, get the maximum row value.
            max_r = max(cell[1] for cell in node.room.cells)
            if max_r > southern_r:
                southern_r = max_r
                southern_node = node
        if southern_node is not None:
            southern_node.external_door = self._find_southern_external_door(southern_node.room)

    def to_tiled(self, rooms, connections):
        """
        Transform the list of rooms into a tiled map array:
          0 -> exterior
          1 -> floor
          2 -> wall
          4 -> door

        Returns:
            tuple: (floor_points, wall_points) coordinates for placing tiles
        """
        # Build RoomTree (do not assign external door at root).
        room_tree = self._build_room_tree(rooms, connections)
        # Assign external door to the southernmost room.
        self._assign_southern_external_door(room_tree)

        tiled = np.zeros((self.total_height, self.total_width), dtype=np.uint8)
        # Fill room interiors with floor (1)
        for room in rooms:
            for (c, r) in room.cells:
                x0 = self.line_width + c * (self.cell_width + self.line_width)
                y0 = self.line_width + r * (self.cell_height + self.line_width)
                tiled[y0:y0 + self.cell_height, x0:x0 + self.cell_width] = 1

        # Draw walls for each cell.
        for room in rooms:
            for (c, r) in room.cells:
                x0 = self.line_width + c * (self.cell_width + self.line_width)
                y0 = self.line_width + r * (self.cell_height + self.line_width)
                # Top wall
                if (c, r - 1) in room.cells:
                    tiled[y0 - self.line_width:y0, x0:x0 + self.cell_width] = 1
                else:
                    tiled[y0 - self.line_width:y0, x0:x0 + self.cell_width] = 2
                # Bottom wall
                if (c, r + 1) in room.cells:
                    tiled[y0 + self.cell_height:y0 + self.cell_height + self.line_width, x0:x0 + self.cell_width] = 1
                else:
                    tiled[y0 + self.cell_height:y0 + self.cell_height + self.line_width, x0:x0 + self.cell_width] = 2
                # Left wall
                if (c - 1, r) in room.cells:
                    tiled[y0:y0 + self.cell_height, x0 - self.line_width:x0] = 1
                else:
                    tiled[y0:y0 + self.cell_height, x0 - self.line_width:x0] = 2
                # Right wall
                if (c + 1, r) in room.cells:
                    tiled[y0:y0 + self.cell_height, x0 + self.cell_width:x0 + self.cell_width + self.line_width] = 1
                else:
                    tiled[y0:y0 + self.cell_height, x0 + self.cell_width:x0 + self.cell_width + self.line_width] = 2

        # Process cell corners to avoid gaps.
        for room in rooms:
            for (c, r) in room.cells:
                x0 = self.line_width + c * (self.cell_width + self.line_width)
                y0 = self.line_width + r * (self.cell_height + self.line_width)
                # Top-left corner
                top_region = tiled[y0 - self.line_width:y0, x0:x0 + self.cell_width]
                left_region = tiled[y0:y0 + self.cell_height, x0 - self.line_width:x0]
                corner = tiled[y0 - self.line_width:y0, x0 - self.line_width:x0]
                if np.any(top_region == 2) or np.any(left_region == 2):
                    corner[:] = 2
                else:
                    corner[:] = 1
                # Top-right corner
                top_region = tiled[y0 - self.line_width:y0, x0:x0 + self.cell_width]
                right_region = tiled[y0:y0 + self.cell_height, x0 + self.cell_width:x0 + self.cell_width + self.line_width]
                corner = tiled[y0 - self.line_width:y0, x0 + self.cell_width:x0 + self.cell_width + self.line_width]
                if np.any(top_region == 2) or np.any(right_region == 2):
                    corner[:] = 2
                else:
                    corner[:] = 1
                # Bottom-left corner
                bottom_region = tiled[y0 + self.cell_height:y0 + self.cell_height + self.line_width, x0:x0 + self.cell_width]
                left_region = tiled[y0:y0 + self.cell_height, x0 - self.line_width:x0]
                corner = tiled[y0 + self.cell_height:y0 + self.cell_height + self.line_width, x0 - self.line_width:x0]
                if np.any(bottom_region == 2) or np.any(left_region == 2):
                    corner[:] = 2
                else:
                    corner[:] = 1
                # Bottom-right corner
                bottom_region = tiled[y0 + self.cell_height:y0 + self.cell_height + self.line_width, x0:x0 + self.cell_width]
                right_region = tiled[y0:y0 + self.cell_height, x0 + self.cell_width:x0 + self.cell_width + self.line_width]
                corner = tiled[y0 + self.cell_height:y0 + self.cell_height + self.line_width, x0 + self.cell_width:x0 + self.cell_width + self.line_width]
                if np.any(bottom_region == 2) or np.any(right_region == 2):
                    corner[:] = 2
                else:
                    corner[:] = 1

        # Process door regions if room_tree is provided.
        if room_tree is not None:
            # For each node, compute door region and fill with value 4.
            for node in room_tree.traverse():
                for door in [node.door_to_parent, node.external_door]:
                    if door is not None:
                        ((c, r), side) = door
                        # Compute top-left coordinate of the cell.
                        x0 = self.line_width + c * (self.cell_width + self.line_width)
                        y0 = self.line_width + r * (self.cell_height + self.line_width)
                        # Compute door rectangle based on side.
                        if side == 'top':
                            door_width = 2
                            door_x = x0 + (self.cell_width - door_width) / 2.0
                            door_y = y0 - self.line_width
                            door_w, door_h = door_width, self.line_width
                        elif side == 'bottom':
                            door_width = 2
                            door_x = x0 + (self.cell_width - door_width) / 2.0
                            door_y = y0 + self.cell_height
                            door_w, door_h = door_width, self.line_width
                        elif side == 'left':
                            door_height = 4
                            door_y = y0 + (self.cell_height - door_height) / 2.0
                            door_x = x0 - self.line_width
                            door_w, door_h = self.line_width, door_height
                        elif side == 'right':
                            door_height = 4
                            door_y = y0 + (self.cell_height - door_height) / 2.0
                            door_x = x0 + self.cell_width
                            door_w, door_h = self.line_width, door_height
                        else:
                            continue

                        # Convert door rectangle coordinates to integer indices.
                        x_start = int(round(door_x))
                        y_start = int(round(door_y))
                        x_end = int(round(door_x + door_w))
                        y_end = int(round(door_y + door_h))
                        # Set door region in tiled map to value 4.
                        tiled[y_start:y_end, x_start:x_end] = 4
        logger.debug(f"Generated tiled map with shape: {tiled.shape}")
        
        # Convert the numpy array to coordinate lists
        floor_coords = np.argwhere(tiled == 1)  # Floor
        wall_coords = np.argwhere(tiled == 2)  # Wall
        door_coords = np.argwhere(tiled == 4)  # Door

        floor_points = [(col, row) for row, col in floor_coords]
        wall_points = [(col, row) for row, col in wall_coords]
        door_points = [(col, row) for row, col in door_coords]

        # Add door points to floor points for consistent rendering
        floor_points += door_points
        return floor_points, wall_points, tiled
    def visualize_tiled_map(self, tiled, title="Tiled Map with Doors"):
        """
        Use matplotlib to visualize the tiled map.
        Mapping:
          0 -> exterior (dark gray)
          1 -> floor (light yellow)
          2 -> wall (dark blue)
          4 -> door (red)
        """
        fig, ax = plt.subplots(figsize=(8, 8))
        # Create a colormap list with indices 0,1,2,3,4. Index 3 is unused.
        cmap = ListedColormap(['#2F4F4F', '#FFFFE0', '#00008B', '#FFFFFF', '#FF0000'])
        ax.imshow(tiled, cmap=cmap, origin='upper')
        ax.set_xlim(0, self.total_width)
        ax.set_ylim(self.total_height, 0)
        ax.set_title(title)
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        plt.show()

    def _ascii_visualize(self, tiled):
        """
        Print the tiled map with ASCII characters:
          0 -> ' ' (exterior)
          1 -> '.' (floor)
          2 -> '#' (wall)
          4 -> 'D' (door)
        """
        # Convert tiled array to a character matrix.
        char_map = {0: ' ', 1: '.', 2: '#', 4: 'D'}
        rows = []
        for row in tiled:
            rows.append([char_map.get(val, '?') for val in row])
        # Print each row.
        for row in rows:
            print(''.join(row))


# ---------------------------
# Example usage
# ---------------------------
if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # 创建房间实例
    room = Room(name="test_room")
    
    # 设置房间参数
    grid_width = 12
    grid_height = 8
    cell_width = 4
    cell_height = 5
    line_width = 1
    
    # 手动设置房间属性
    room.grid_width = grid_width
    room.grid_height = grid_height
    room.cell_width = cell_width
    room.cell_height = cell_height
    room.line_width = line_width
    room.total_width = grid_width * (cell_width + line_width) + line_width
    room.total_height = grid_height * (cell_height + line_width) + line_width
    
    # 生成房间
    dwellings = Dwellings(grid_width, grid_height, seed=42, num_vertices=6)
    result = dwellings.divide_room(
        max_area=8, 
        min_overlap_ratio=0.6, 
        shape_ratio_threshold=0.3, 
        max_iterations=100
    )
    rooms = result["rooms"]
    connections = result["connections"]
    
    # 生成房间平面图并获取tiled地图数据
    floor_points, wall_points, tiled = room.to_tiled(rooms, connections)
    
    print(f"房间生成完成，总地图大小: {room.total_width}x{room.total_height}")
    print(f"地板点数量: {len(floor_points)}")
    print(f"墙壁点数量: {len(wall_points)}")
    
    # 可视化房间布局
    room.visualize_tiled_map(tiled, title="房间布局可视化")
    
    # 打印ASCII版本的房间布局
    # 警告：这会产生很多输出！
    print_ascii = False
    if print_ascii:
        print("\nASCII格式房间布局:")
        room._ascii_visualize(tiled)


