import hashlib
import numpy as np
import matplotlib.pyplot as plt
from perlin_noise import PerlinNoise
from matplotlib.colors import BoundaryNorm
from tiled_master.utils.logger import logger


def str_to_seed_int(seed_str: str) -> int:
    # Generate fixed-length hash value using md5
    md5_hash = hashlib.md5(seed_str.encode('utf-8')).hexdigest()
    # Convert to integer (can be limited to 32-bit or 64-bit)
    seed_int = int(md5_hash, 16) % (2 ** 32)
    return seed_int


class NoiseMap:
    def __init__(self, width, height, random_seed):
        self.width = width
        self.height = height
        self.noise_map = np.zeros((self.height, self.width))
        if isinstance(random_seed, str):
            self.seed = str_to_seed_int(random_seed)
        else:
            self.seed = random_seed
        self.tiles = []  #(x, y)

    def _generate_perlin_noise(self, scale):
        scale = 1000 / scale
        noise = PerlinNoise(octaves=1, seed=self.seed)

        for y in range(self.height):
            for x in range(self.width):
                noise_value = noise([x / scale, y / scale])
                self.noise_map[y][x] = noise_value

        min_value = np.min(self.noise_map)
        max_value = np.max(self.noise_map)
        normalized_map = (self.noise_map - min_value) / (max_value - min_value)
        self.noise_map = normalized_map

    def _generate_double_perlin_noise(self, major_scale, minor_scale, major_weight=0.7, minor_weight=0.3):
        # Parameter settings: low-frequency layer provides overall shape, high-frequency layer provides details
        coarse_scale = major_scale
        fine_scale = minor_scale
        coarse_weight = major_weight
        fine_weight = minor_weight

        # Generate two layers of noise separately
        coarse_noise = np.zeros((self.height, self.width))
        fine_noise = np.zeros((self.height, self.width))

        # Note: use different octaves and seeds (different results can be obtained through seed offset)
        noise_coarse = PerlinNoise(octaves=2, seed=self.seed)
        noise_fine = PerlinNoise(octaves=4, seed=self.seed + 1)

        scale_coarse = self.width * 10 / coarse_scale
        scale_fine = self.height * 10 / fine_scale

        for y in range(self.height):
            for x in range(self.width):
                coarse_value = noise_coarse([x / scale_coarse, y / scale_coarse])
                fine_value = noise_fine([x / scale_fine, y / scale_fine])
                coarse_noise[y][x] = coarse_value
                fine_noise[y][x] = fine_value

        # Normalize the two layers of noise to [0, 1]
        coarse_min, coarse_max = np.min(coarse_noise), np.max(coarse_noise)
        coarse_noise = (coarse_noise - coarse_min) / (coarse_max - coarse_min)

        fine_min, fine_max = np.min(fine_noise), np.max(fine_noise)
        fine_noise = (fine_noise - fine_min) / (fine_max - fine_min)

        # Noise superposition: combining low-frequency and high-frequency layers
        combined_noise = coarse_weight * coarse_noise + fine_weight * fine_noise
        self.noise_map = combined_noise

    def generate_river(self):
        self._generate_perlin_noise(10)
        min_threshold = 0.55
        max_threshold = 0.7
        river_tiles = []

        for y in range(self.height):
            for x in range(self.width):
                noise_value = self.noise_map[y][x]
                if min_threshold <= noise_value <= max_threshold:
                    self.tiles.append((x, y))
                    river_tiles.append((x, y))

        return river_tiles

    def generate_bushes(self):
        self._generate_perlin_noise(300)
        threshold = 0.78
        bush_tiles = []

        for y in range(self.height):
            for x in range(self.width):
                noise_value = self.noise_map[y][x]
                if noise_value >= threshold:
                    self.tiles.append((x, y))
                    bush_tiles.append((x, y))

        return bush_tiles

    def generate_flowers(self):
        self._generate_perlin_noise(500)
        threshold = 0.85
        bush_tiles = []

        for y in range(self.height):
            for x in range(self.width):
                noise_value = self.noise_map[y][x]
                if noise_value >= threshold:
                    self.tiles.append((x, y))
                    bush_tiles.append((x, y))

        return bush_tiles

    def generate_flowers_area(self):
        self._generate_perlin_noise(30)
        threshold = 0.5
        tree_area = []

        for y in range(self.height):
            for x in range(self.width):
                noise_value = self.noise_map[y][x]
                if noise_value >= threshold:
                    tree_area.append((x, y))

        return tree_area

    def generate_tree_area(self, scale):
        logger.info(f"generate tree area at scale {scale}")
        if scale == 1:
            self._generate_double_perlin_noise(50, 20)
            self.generate_center_editable_area(10)
            threshold = 0.8
        elif scale == 2:
            self._generate_double_perlin_noise(20, 20)
            self.generate_center_editable_area(60)
            threshold = 0.2
        elif scale == 3:
            self._generate_double_perlin_noise(20, 20)
            threshold = 0.5
        elif scale == 4:
            self._generate_double_perlin_noise(20, 20)
            self.generate_center_editable_area(20)
            threshold = 0.2
        else:
            return []
        tree_area = []

        for y in range(self.height):
            for x in range(self.width):
                noise_value = self.noise_map[y][x]
                if noise_value >= threshold:
                    tree_area.append((x, y))

        return tree_area

    def plot_2d_noise_by_5(self):
        """
        Draw a 2D map of noise distribution, with each 0.2 change displayed as a solid color block.
        """
        # Set the boundary values for each block
        boundaries = np.arange(0, 1.2, 0.2)  # Set the range from 0 to 1.0, with a step of 0.2
        norm = BoundaryNorm(boundaries, ncolors=256)

        plt.figure(figsize=(10, 8))
        plt.xlim(0, self.width)
        plt.ylim(0, self.height)

        # Use imshow to draw the noise image and apply BoundaryNorm
        plt.imshow(self.noise_map, cmap='terrain', origin='upper', norm=norm)

        # Add a color bar to display noise values
        plt.colorbar(label='Noise Value')

        # Chart title and axis labels
        plt.title('Perlin Noise 2D Map')
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.show()

    def plot_2d_noise(self):
        """
        Draw a 2D map of noise distribution.
        """
        plt.figure(figsize=(10, 8))
        plt.xlim(0, self.width)
        plt.ylim(0, self.height)
        plt.imshow(self.noise_map, cmap='terrain', origin='upper')
        plt.colorbar(label='Noise Value')  # Add legend for noise values
        plt.title('Perlin Noise 2D Map')
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.show()

    def plot_3d_noise(self):
        # Create grid
        x = np.linspace(0, self.width, self.width)
        y = np.linspace(0, self.height, self.height)
        x, y = np.meshgrid(x, y)

        # Create a 3D figure
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        # Draw 3D surface
        ax.plot_surface(x, y, self.noise_map, cmap='terrain')

        # Set title and labels
        ax.set_title('Perlin Noise 3D Map')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Noise Value')

        plt.show()

    def plot_2d_points(self, points, title="2D Points Distribution"):
        """
        Draw a 2D distribution of the given set of point coordinates.

        :param points: Set of point coordinates, e.g. [(x1, y1), (x2, y2), ...]
        :param title: Title of the chart
        """
        if not points:
            print("No point set to draw!")
            return
        x_coords, y_coords = zip(*points)  # Separate coordinates into X and Y lists
        plt.figure(figsize=(self.width // 10, self.height // 10))
        plt.scatter(x_coords, y_coords, s=10, c='green', alpha=0.6, edgecolors='black')
        plt.title(title)
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.xlim(0, self.width)
        plt.ylim(0, self.height)
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.show()

    def generate_center_editable_area(self, center_sigma=100, base_value=0.0):
        if len(self.noise_map) == 0:
            raise Exception("should have valid base noise first")
        center_x, center_y = self.width / 2, self.height / 2

        for y in range(self.height):
            for x in range(self.width):
                # Calculate the Euclidean distance from the point to the map center
                d = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
                # Use Gaussian function to calculate weight: center area weight close to 1, decaying to 0 outward
                weight = np.exp(- (d / center_sigma) ** 2)
                # Mixed: center area more uses base_value (e.g., smooth terrain), edge area uses noise value
                noise_val = self.noise_map[y][x]
                final_value = weight * base_value + (1 - weight) * noise_val
                self.noise_map[y][x] = final_value

        noise_min, noise_max = np.min(self.noise_map), np.max(self.noise_map)
        self.noise_map = (self.noise_map - noise_min) / (noise_max - noise_min)

    def generate_natural_river(self, scale):
        logger.info(f"generate river area at scale {scale}")
        if scale == 1:
            self._generate_double_perlin_noise(15, 15, major_weight=0.85, minor_weight=0.15)
            min_threshold = 0.8
            max_threshold = 1.0
        elif scale == 2:
            self._generate_double_perlin_noise(2, 10, major_weight=0.85, minor_weight=0.15)
            min_threshold = 0.5
            max_threshold = 0.6
        elif scale == 3:
            self._generate_double_perlin_noise(2, 10, major_weight=0.85, minor_weight=0.15)
            min_threshold = 0.4
            max_threshold = 0.65
        elif scale == 4:
            self._generate_double_perlin_noise(0.25, 1, major_weight=0.85, minor_weight=0.15)
            min_threshold = 0.5
            max_threshold = 0.56
        elif scale == 5:
            self._generate_double_perlin_noise(10, 15, major_weight=0.85, minor_weight=0.15)
            min_threshold = 0.35
            max_threshold = 1.0
        elif scale == 6:
            self._generate_double_perlin_noise(2, 5, major_weight=0.8, minor_weight=0.2)
            min_threshold = 0.45
            max_threshold = 2
        else:
            return []
        river_tiles = []

        for y in range(self.height):
            for x in range(self.width):
                if min_threshold <= self.noise_map[y][x] <= max_threshold:
                    river_tiles.append((x, y))
                    self.tiles.append((x, y))
        return river_tiles

    def generate_terrain(self, depth):
        self._generate_double_perlin_noise(10, 20, major_weight=0.85, minor_weight=0.15)
        self.generate_center_editable_area(base_value=0.5)
        if depth == 0:
            raise Exception("depth should be greater than 0")
        buckets = [[] for _ in range(depth)]
        for y in range(self.height):
            for x in range(self.width):
                index = int(self.noise_map[y][x] * depth) if self.noise_map[y][x] < 1 else depth - 1
                buckets[index].append((x, y))
        return buckets


# if __name__ == '__main__':
#     width = 128
#     height = 64
#     noise_map = NoiseMap(width, height)
#     noise_map.generate_bushes()
#     noise_map.plot_tile_preview()

# if __name__ == '__main__':
#     # generate river
#     width = 80
#     height = 40
#     noise_map = NoiseMap(width, height)
#     river = noise_map.generate_natural_river(4)
#     noise_map.plot_2d_points(river)

# if __name__ == '__main__':
#     noisemap = NoiseMap(128, 64)
#     big_area = set(noisemap.generate_flowers_area())
#     small_area = set(noisemap.generate_flowers())
#     noisemap.plot_2d_points(big_area)
#     my_area = big_area.intersection(small_area)
#     noisemap.plot_2d_points(my_area)

# if __name__ == '__main__':
#     # Create noise map instance
#     nm = NoiseMap(width=128, height=64)
#     # Generate map with centered editable area (parameters can be adjusted as needed)
#     editable_tiles = nm.generate_center_editable_area(noise_scale=30, center_sigma=30, editable_radius=30, base_value=0)
#     # Visualize the generated map
#     nm.plot_2d_noise()
#     nm.plot_2d_points(editable_tiles)

if __name__ == '__main__':
    noise = NoiseMap(width=80, height=40)
    tree_area = noise.generate_natural_river(4)
    noise.plot_3d_noise()
    noise.plot_2d_points(tree_area)
