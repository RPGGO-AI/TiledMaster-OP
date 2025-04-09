import random
import math
from collections import deque

# ---------------------------
# Grid class definition
# ---------------------------
class Grid:
    def __init__(self, width, height, seed=None, rand=None):
        # Initialize grid dimensions and create an empty grid.
        self.width = width
        self.height = height
        self.grid = [[False] * width for _ in range(height)]
        # Create a Random instance using seed or provided rand.
        self.rand = rand if rand is not None else random.Random(seed)

    @classmethod
    def create_from_random_polygon(cls, region, num_vertices=8, rand=None):
        # Create a Grid instance directly from a randomly generated polygon.
        x0, y0, width, height = region
        x1, y1 = x0 + width, y0 + height
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        points = []
        rgen = rand if rand is not None else random
        for _ in range(num_vertices):
            x = rgen.randint(x0, x1)
            y = rgen.randint(y0, y1)
            angle = math.atan2(y - cy, x - cx)
            points.append((x, y, angle))
        points.sort(key=lambda p: p[2])
        polygon = [(p[0], p[1]) for p in points]
        instance = cls(width, height, rand=rand)
        instance._fill_polygon(polygon)
        return instance

    @classmethod
    def create_room_polygon(cls, width, height, seed=None, num_vertices=6):
        # Create a room polygon with a valid grid cell count.
        rgen = random.Random(seed)
        while True:
            grid_obj = cls.create_from_random_polygon((0, 0, width, height), num_vertices=num_vertices, rand=rgen)
            grid_obj._smooth(iterations=2)
            grid_obj._remove_small_regions()
            grid_obj._fill_holes()
            if 32 >= grid_obj._count_valid() >= 8:
                break
        grid_obj._center_effective_area()
        return grid_obj

    @staticmethod
    def _is_point_in_polygon(x, y, polygon):
        # Ray-casting algorithm to check if a point is inside a polygon.
        num = len(polygon)
        j = num - 1
        inside = False
        for i in range(num):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi):
                inside = not inside
            j = i
        return inside

    def _fill_polygon(self, polygon):
        # Fill the grid cells that are inside the given polygon.
        self.grid = [[False] * self.width for _ in range(self.height)]
        for r in range(self.height):
            for c in range(self.width):
                if Grid._is_point_in_polygon(c + 0.5, r + 0.5, polygon):
                    self.grid[r][c] = True

    def _count_valid(self):
        # Count number of True cells in the grid.
        return sum(sum(1 for cell in row if cell) for row in self.grid)

    def _smooth(self, iterations=1):
        # Smooth the grid using cellular automata.
        for _ in range(iterations):
            new_grid = [[False] * self.width for _ in range(self.height)]
            for r in range(self.height):
                for c in range(self.width):
                    count = 0
                    for dr in (-1, 0, 1):
                        for dc in (-1, 0, 1):
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < self.height and 0 <= nc < self.width and self.grid[nr][nc]:
                                count += 1
                    new_grid[r][c] = True if count >= 5 else False
            self.grid = new_grid

    def _remove_small_regions(self):
        # Remove small regions by keeping only the largest connected True region.
        visited = [[False] * self.width for _ in range(self.height)]
        components = []
        for r in range(self.height):
            for c in range(self.width):
                if self.grid[r][c] and not visited[r][c]:
                    q = deque()
                    q.append((r, c))
                    visited[r][c] = True
                    comp = [(r, c)]
                    while q:
                        cr, cc = q.popleft()
                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < self.height and 0 <= nc < self.width:
                                if self.grid[nr][nc] and not visited[nr][nc]:
                                    visited[nr][nc] = True
                                    q.append((nr, nc))
                                    comp.append((nr, nc))
                    components.append(comp)
        if not components:
            return
        largest = max(components, key=lambda comp: len(comp))
        new_grid = [[False] * self.width for _ in range(self.height)]
        for r, c in largest:
            new_grid[r][c] = True
        self.grid = new_grid

    def _fill_holes(self):
        # Fill holes inside the grid using flood fill.
        visited = [[False] * self.width for _ in range(self.height)]

        def flood_fill(r, c):
            q = deque()
            q.append((r, c))
            visited[r][c] = True
            while q:
                cr, cc = q.popleft()
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < self.height and 0 <= nc < self.width:
                        if not visited[nr][nc] and not self.grid[nr][nc]:
                            visited[nr][nc] = True
                            q.append((nr, nc))

        # Flood fill from boundaries.
        for r in range(self.height):
            if not visited[r][0] and not self.grid[r][0]:
                flood_fill(r, 0)
            if not visited[r][self.width - 1] and not self.grid[r][self.width - 1]:
                flood_fill(r, self.width - 1)
        for c in range(self.width):
            if not visited[0][c] and not self.grid[0][c]:
                flood_fill(0, c)
            if not visited[self.height - 1][c] and not self.grid[self.height - 1][c]:
                flood_fill(self.height - 1, c)
        for r in range(self.height):
            for c in range(self.width):
                if not self.grid[r][c] and not visited[r][c]:
                    self.grid[r][c] = True

    def _center_effective_area(self):
        # Center the effective (True) area within the full grid.
        min_r, max_r = self.height, -1
        min_c, max_c = self.width, -1
        for r in range(self.height):
            for c in range(self.width):
                if self.grid[r][c]:
                    min_r = min(min_r, r)
                    max_r = max(max_r, r)
                    min_c = min(min_c, c)
                    max_c = max(max_c, c)
        if max_r == -1 or max_c == -1:
            return
        current_center_r = (min_r + max_r + 1) / 2.0
        current_center_c = (min_c + max_c + 1) / 2.0
        desired_center_r = self.height / 2.0
        desired_center_c = self.width / 2.0
        offset_r = int(round(desired_center_r - current_center_r))
        offset_c = int(round(desired_center_c - current_center_c))
        new_grid = [[False] * self.width for _ in range(self.height)]
        for r in range(self.height):
            for c in range(self.width):
                if self.grid[r][c]:
                    nr, nc = r + offset_r, c + offset_c
                    if 0 <= nr < self.height and 0 <= nc < self.width:
                        new_grid[nr][nc] = True
        self.grid = new_grid


# ---------------------------
# Room class definition
# ---------------------------
class Room:
    def __init__(self, cells):
        # cells is a set of (c, r) tuples representing grid cell coordinates.
        self.cells = set(cells)

    @property
    def area(self):
        return len(self.cells)

    @property
    def bbox(self):
        # Return the bounding box (min_x, min_y, max_x, max_y) for this room.
        if not self.cells:
            return None
        xs = [c for (c, r) in self.cells]
        ys = [r for (c, r) in self.cells]
        return (min(xs), min(ys), max(xs), max(ys))

    def shape_ratio(self):
        # Return the ratio of the shorter side to the longer side of the bounding box.
        bb = self.bbox
        if bb is None:
            return 0
        width = bb[2] - bb[0] + 1
        height = bb[3] - bb[1] + 1
        return min(width, height) / max(width, height)

    @property
    def is_one_cell_wide(self):
        # Check if the room is a single-cell-wide rectangle (but not a 1x1 square).
        bb = self.bbox
        if bb is None:
            return False
        min_x, min_y, max_x, max_y = bb
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        if self.area != width * height:
            return False
        return (width == 1 and height > 1) or (height == 1 and width > 1)

    def __repr__(self):
        return f"Room(area={self.area}, bbox={self.bbox})"


# ---------------------------
# Dwellings class definition
# ---------------------------
class Dwellings:
    def __init__(self, width, height, seed=None, num_vertices=6):
        # Generate blueprint grid and initial room.
        self.width = width
        self.height = height
        self.seed = seed
        self.grid_obj = Grid.create_room_polygon(width, height, seed=seed, num_vertices=num_vertices)
        self.grid = self.grid_obj.grid
        bbox = Dwellings._get_polygon_bounding_box(self.grid)
        if bbox is None:
            raise ValueError("No valid polygon found!")
        self.initial_room = Dwellings._create_room_from_bbox(bbox)
        self.rooms = [self.initial_room]

    @staticmethod
    def _get_polygon_bounding_box(grid):
        # Compute bounding box for all True cells in grid.
        height = len(grid)
        width = len(grid[0])
        min_x, min_y = width, height
        max_x, max_y = -1, -1
        for r in range(height):
            for c in range(width):
                if grid[r][c]:
                    min_x = min(min_x, c)
                    max_x = max(max_x, c)
                    min_y = min(min_y, r)
                    max_y = max(max_y, r)
        return None if max_x == -1 else (min_x, min_y, max_x, max_y)

    @staticmethod
    def _create_room_from_bbox(bbox):
        # Create a Room from the bounding box.
        x0, y0, x1, y1 = bbox
        cells = {(c, r) for r in range(y0, y1 + 1) for c in range(x0, x1 + 1)}
        return Room(cells)

    @staticmethod
    def _clip_room_to_polygon(room, grid):
        # Clip room cells so that only cells inside the grid (True) remain.
        bb = room.bbox
        if bb is None:
            return None
        min_x, min_y, max_x, max_y = bb
        valid = False
        for r in range(min_y, max_y + 1):
            for c in range(min_x, max_x + 1):
                if grid[r][c]:
                    valid = True
                    min_x = min(min_x, c)
                    max_x = max(max_x, c)
                    min_y = min(min_y, r)
                    max_y = max(max_y, r)
        if not valid:
            return None
        return Dwellings._create_room_from_bbox((min_x, min_y, max_x, max_y))

    @staticmethod
    def _subdivide_room(room, direction):
        # Subdivide room into two parts along the specified direction.
        bb = room.bbox
        if bb is None:
            return None, None
        min_x, min_y, max_x, max_y = bb
        if direction == "horizontal":
            if max_y == min_y:
                return room, None
            split_line = random.randint(min_y, max_y - 1)
            room1_cells = {(c, r) for (c, r) in room.cells if r <= split_line}
            room2_cells = {(c, r) for (c, r) in room.cells if r > split_line}
        else:
            if max_x == min_x:
                return room, None
            split_line = random.randint(min_x, max_x - 1)
            room1_cells = {(c, r) for (c, r) in room.cells if c <= split_line}
            room2_cells = {(c, r) for (c, r) in room.cells if c > split_line}
        return Room(room1_cells), Room(room2_cells)

    @staticmethod
    def _count_overlap(room, grid):
        # Count grid cells within room that are True.
        count = 0
        x0, y0, x1, y1 = room.bbox
        for r in range(y0, y1 + 1):
            for c in range(x0, x1 + 1):
                if grid[r][c]:
                    count += 1
        return count

    @staticmethod
    def _is_room_valid(room, grid, max_area, min_overlap_ratio, shape_ratio_threshold):
        # Check if the room meets area, overlap and shape ratio criteria.
        if room.area > max_area:
            return False
        if room.shape_ratio() < shape_ratio_threshold:
            return False
        if Dwellings._count_overlap(room, grid) < room.area * min_overlap_ratio:
            return False
        return True

    @staticmethod
    def _subdivide_rooms_iterative(rooms, grid, max_area, min_overlap_ratio, shape_ratio_threshold=0.3):
        # Iteratively subdivide rooms that do not meet criteria.
        new_rooms = []
        for room in rooms:
            clipped = Dwellings._clip_room_to_polygon(room, grid)
            if clipped is None:
                continue
            if Dwellings._is_room_valid(clipped, grid, max_area, min_overlap_ratio, shape_ratio_threshold):
                new_rooms.append(clipped)
            else:
                bb = clipped.bbox
                if bb is None:
                    continue
                direction = "vertical" if (bb[2] - bb[0]) > (bb[3] - bb[1]) else "horizontal"
                room1, room2 = Dwellings._subdivide_room(clipped, direction)
                if room1 and room1.area > 0:
                    new_clipped = Dwellings._clip_room_to_polygon(room1, grid)
                    if new_clipped is not None:
                        new_rooms.append(new_clipped)
                if room2 and room2.area > 0:
                    new_clipped = Dwellings._clip_room_to_polygon(room2, grid)
                    if new_clipped is not None:
                        new_rooms.append(new_clipped)
        return new_rooms

    @staticmethod
    def _rooms_are_adjacent(room1, room2):
        # Check if two rooms are adjacent (4-connected).
        for (c, r) in room1.cells:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                if (c + dx, r + dy) in room2.cells:
                    return True
        return False

    @staticmethod
    def _compute_room_center(room):
        # Compute center point of the room based on its bounding box.
        bb = room.bbox
        if bb is None:
            return (0, 0)
        min_x, min_y, max_x, max_y = bb
        center_x = (min_x + max_x + 1) / 2.0
        center_y = (min_y + max_y + 1) / 2.0
        return (center_x, center_y)

    def subdivide(self, max_area, min_overlap_ratio, shape_ratio_threshold=0.3, max_iterations=100):
        # Iteratively subdivide the initial room until convergence or maximum iterations.
        current_rooms = self.rooms
        for i in range(max_iterations):
            new_rooms = Dwellings._subdivide_rooms_iterative(
                current_rooms, self.grid, max_area, min_overlap_ratio, shape_ratio_threshold
            )
            if len(new_rooms) == len(current_rooms):
                break
            current_rooms = new_rooms
        self.rooms = current_rooms
        return self.rooms

    def merge_adjacent_one_cell_wide_rooms(self):
        # Merge adjacent rooms that are one-cell wide.
        # First, separate rooms into candidates (one-cell-wide) and others.
        candidates = [room for room in self.rooms if room.is_one_cell_wide]
        others = [room for room in self.rooms if not room.is_one_cell_wide]
        # Build connected components among candidate rooms.
        n = len(candidates)
        visited = [False] * n
        components = []
        for i in range(n):
            if not visited[i]:
                comp = []
                stack = [i]
                visited[i] = True
                while stack:
                    cur = stack.pop()
                    comp.append(cur)
                    for j in range(n):
                        if not visited[j] and Dwellings._rooms_are_adjacent(candidates[cur], candidates[j]):
                            visited[j] = True
                            stack.append(j)
                components.append(comp)
        # Merge rooms within each connected component.
        merged_rooms = []
        for comp in components:
            merged_cells = set()
            for idx in comp:
                merged_cells.update(candidates[idx].cells)
            merged_rooms.append(Room(merged_cells))
        # Update self.rooms: combine non-one-cell-wide rooms and merged candidate rooms.
        self.rooms = others + merged_rooms

    def generate_room_mst(self, extra_count: int = 0) -> list:
        """
        Generate MST connections between rooms based on adjacency relations, all edge weights are 1.
        :param extra_count: Number of additional edges to add (optional)
        :return: List of room connection pairs, each element is (room1, room2)
        """
        # Build edge list: only add adjacent room pairs, all edge weights are 1
        rooms = self.rooms
        edges = []
        n = len(rooms)
        for i in range(n):
            for j in range(i + 1, n):
                # Call the adjacency detection function in the Dwelling class
                if Dwellings._rooms_are_adjacent(rooms[i], rooms[j]):
                    edges.append((1, i, j))

        # Use union-find to construct MST
        parent = list(range(n))
        rank = [0] * n

        # union-find find function
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        # union-find merge function
        def union(a, b):
            rootA = find(a)
            rootB = find(b)
            if rootA != rootB:
                if rank[rootA] > rank[rootB]:
                    parent[rootB] = rootA
                elif rank[rootA] < rank[rootB]:
                    parent[rootA] = rootB
                else:
                    parent[rootB] = rootA
                    rank[rootA] += 1
                return True
            return False

        # Since all edge weights are 1, we can directly process without sorting
        mst_edge_indices = []
        for weight, i, j in edges:
            if union(i, j):
                mst_edge_indices.append((i, j))

        # If extra edges are needed, randomly select from the remaining edges
        if extra_count > 0:
            mst_set = {tuple(sorted(e)) for e in mst_edge_indices}
            candidate_edges = []
            for weight, i, j in edges:
                if tuple(sorted((i, j))) not in mst_set:
                    candidate_edges.append((i, j))
            rand = random.Random(self.seed)
            rand.shuffle(candidate_edges)
            extra_edges = []
            for i, j in candidate_edges:
                extra_edges.append((i, j))
                if len(extra_edges) >= extra_count:
                    break
            mst_edge_indices.extend(extra_edges)

        # Convert edge indices to room object pairs
        connection_pairs = [(rooms[i], rooms[j]) for i, j in mst_edge_indices]
        return connection_pairs

    def divide_room(self, max_area=8, min_overlap_ratio=0.5, shape_ratio_threshold=0.3, max_iterations=100):
        """
        Run the complete process:
        - subdivide the initial room,
        - merge adjacent one-cell-wide rooms,
        - generate room MST connections.
        Return a dictionary with keys:
          "rooms": list of Room objects,
          "connections": list of (Room, Room) tuples.
        """
        self.rooms = self.subdivide(max_area, min_overlap_ratio, shape_ratio_threshold, max_iterations)
        self.merge_adjacent_one_cell_wide_rooms()
        connections = self.generate_room_mst()
        return {"rooms": self.rooms, "connections": connections}
