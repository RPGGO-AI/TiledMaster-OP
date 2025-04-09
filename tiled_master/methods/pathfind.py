import heapq
from tiled_master.utils.logger import logger


class Pathfinder:
    def __init__(self, map_cache, map_width, map_height, width=2):
        """
        Initialize Pathfinder instance.

        :param map_cache: map data object providing check_exists method.
        :param map_width: width of the map grid.
        :param map_height: height of the map grid.
        :param width: path width (default=2).
        """
        self.map_cache = map_cache
        self.map_width = map_width
        self.map_height = map_height
        self.width = width

    def _heuristic(self, p1, p2):
        """Compute heuristic Manhattan distance."""
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

    def _neighbors(self, position):
        """
        Get neighboring positions around the current node.
        Handles integer and half-grid coordinates.
        """
        x, y = position
        if self.width % 2 == 0:
            # Even width: half-grid neighbors
            deltas = [(-0.5, 0), (0.5, 0), (0, -0.5), (0, 0.5)]
        else:
            # Odd width: integer grid neighbors
            deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for dx, dy in deltas:
            nx, ny = x + dx, y + dy
            yield (nx, ny)

    def _is_valid(self, position, layer_interval):
        x, y = position

        # First check if it's outside the map boundaries
        if not (0 <= x < int(self.map_width*1.2) and 0 <= y < int(self.map_height*1.2)):
            return False

        if self.width % 2 == 0:
            tiles = [
                (int(x - 0.5), int(y - 0.5)),
                (int(x - 0.5), int(y + 0.5)),
                (int(x + 0.5), int(y - 0.5)),
                (int(x + 0.5), int(y + 0.5)),
            ]
            validity = all(
                0 <= tx < int(self.map_width*1.2) and 0 <= ty < int(self.map_height*1.2) and
                all(not self.map_cache.check_exists(tx, ty, layer) for layer in layer_interval)
                for tx, ty in tiles
            )
        else:
            tx, ty = int(x), int(y)
            validity = (
                    0 <= tx < int(self.map_width*1.2) and 0 <= ty < int(self.map_height*1.2) and
                    all(not self.map_cache.check_exists(tx, ty, layer) for layer in layer_interval)
            )

        return validity

    def find_corridor_path(self, start, goal, layer_interval):
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        closed_set = set()


        while open_set:
            _, current = heapq.heappop(open_set)

            if current in closed_set:
                continue

            closed_set.add(current)

            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                return self._expand_path(path, layer_interval)

            for neighbor in self._neighbors(current):
                if neighbor in closed_set:
                    continue

                if not self._is_valid(neighbor, layer_interval):
                    continue

                tentative_g_score = g_score[current] + 1
                if tentative_g_score < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    heapq.heappush(open_set, (tentative_g_score + self._heuristic(neighbor, goal), neighbor))

        logger.warning(f"Failed to find path between {start} and {goal}")
        return set()


    def _expand_path(self, path, layer_interval):
        """
        Expand path width, handling even-width half-grid points by selecting adjacent tiles.
        """
        expanded_tiles = set()

        for pos in path:
            x, y = pos
            if self.width % 2 == 0:
                # For half-grid positions (even width), expand into four surrounding tiles
                tiles = [
                    (int(x - 0.5), int(y - 0.5)),
                    (int(x - 0.5), int(y + 0.5)),
                    (int(x + 0.5), int(y - 0.5)),
                    (int(x + 0.5), int(y + 0.5)),
                ]
            else:
                # Odd width, symmetric expansion around central tile
                half_width = self.width // 2
                cx, cy = int(x), int(y)
                tiles = [
                    (sx, sy)
                    for sx in range(cx - half_width, cx + half_width + 1)
                    for sy in range(cy - half_width, cy + half_width + 1)
                ]

            for tx, ty in tiles:
                if (all(not self.map_cache.check_exists(tx, ty, layer) for layer in layer_interval)):
                    expanded_tiles.add((tx, ty))

        return expanded_tiles
