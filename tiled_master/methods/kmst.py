import random
import math
import matplotlib.pyplot as plt
import matplotlib.lines as mlines



class KMST:
    def __init__(self, points: list, extra_count: int = 0, random_seed: int = 0):
        # Initialize with a list of (x, y) tuples
        self.points = points  # List of points as (x, y)
        self.extra_count = extra_count
        self.rand = random.Random(random_seed)

    def _build_edges(self):
        # Build edges based on Euclidean distance between points
        edges = []
        n = len(self.points)
        for i in range(n):
            x1, y1 = self.points[i]
            for j in range(i + 1, n):
                x2, y2 = self.points[j]
                dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
                edges.append((dist, i, j))
        edges.sort(key=lambda e: e[0])
        return edges

    def _kruskal_mst(self, edges):
        # Kruskal's algorithm to generate MST using union-find
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

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

        n_nodes = len(self.points)
        parent = list(range(n_nodes))
        rank = [0] * n_nodes
        mst_edges = []

        # Process all edges in increasing order of distance
        for dist, a, b in edges:
            if union(a, b):
                mst_edges.append((a, b))
            if len(mst_edges) == n_nodes - 1:
                break
        return mst_edges

    def _add_extra_edges(self, mst_edges, all_edges):
        # Add extra edges to the MST if needed
        mst_set = set(tuple(sorted(e)) for e in mst_edges)
        candidate_edges = [(a, b) for dist, a, b in all_edges if tuple(sorted((a, b))) not in mst_set]
        self.rand.shuffle(candidate_edges)
        extra_edges = candidate_edges[:self.extra_count]
        return extra_edges

    def plot(self, width, height, extra_edges):
        # Plot points and edges (MST in blue, extra edges in green)
        fig, ax = plt.subplots(figsize=(8, 8))
        for i, (x, y) in enumerate(self.points):
            ax.scatter(x, y, c='red', s=100)
            ax.text(x + 0.1, y + 0.1, str(i), fontsize=12)
        all_edges = self._build_edges()
        mst = self._kruskal_mst(all_edges)
        if mst is None:
            print("Unable to generate valid MST")
            return
        for a, b in mst:
            x1, y1 = self.points[a]
            x2, y2 = self.points[b]
            line = mlines.Line2D([x1, x2], [y1, y2], color='blue', lw=2)
            ax.add_line(line)
        for a, b in extra_edges:
            x1, y1 = self.points[a]
            x2, y2 = self.points[b]
            line = mlines.Line2D([x1, x2], [y1, y2], color='green', lw=2)
            ax.add_line(line)
        ax.set_xlim(0, width)
        ax.set_ylim(0, height)
        ax.set_title('Minimum Spanning Tree with Extra Edges')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.invert_yaxis()
        plt.show()

    def generate_connections(self) -> list:
        # Generate connections (MST with extra edges) and return as list of coordinate pairs
        all_edges = self._build_edges()
        mst = self._kruskal_mst(all_edges)
        extra_edges = self._add_extra_edges(mst, all_edges)
        edges = mst + extra_edges
        connection_pairs = []
        for a, b in edges:
            connection_pairs.append((self.points[a], self.points[b]))
        return connection_pairs
