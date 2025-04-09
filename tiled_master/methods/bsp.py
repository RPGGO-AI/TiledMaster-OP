import random
import matplotlib.pyplot as plt
import matplotlib.patches as patches


class BSP:
    def __init__(self, min_size: int, random_seed: str):
        self.min_size = min_size
        self.corners: set[(int, int)] = set()
        self.regions: list[(int, int, int, int)] = list()
        self.rand = random.Random(random_seed)

    def add_corners(self, x, y, width, height):
        """
        Add the four corner points of the current rectangle to the set.
        """
        corners = [
            (x, y),
            (x + width, y),
            (x, y + height),
            (x + width, y + height)
        ]
        # Add corner points to the set, which will automatically remove duplicates
        self.corners.update(corners)

    def _bsp_partition(self, region):
        """
        Perform BSP partitioning on the given region, return all leaf regions.

        Parameters:
          region - A 4-tuple (x, y, width, height), with the origin at the top-left.
        Returns:
          A list, each element is a leaf region in (x, y, width, height) format.
        """
        x, y, width, height = region
        # If the region is too small (width or height less than 2 * min_size), stop splitting
        if width < 2 * self.min_size or height < 2 * self.min_size:
            self.add_corners(x, y, width, height)
            self.regions.append((x, y, width, height))
            return [region]

        # Randomly choose split direction, can also prefer based on region shape
        split_horizontally = self.rand.choice([True, False])
        if width > height:
            split_horizontally = False  # Prefer vertical split when wider
        elif height > width:
            split_horizontally = True  # Prefer horizontal split when taller

        if split_horizontally:
            # Horizontal split: split along y-axis, ensure both parts are at least min_size
            split = self.rand.randint(self.min_size, height - self.min_size)
            region1 = (x, y, width, split)
            region2 = (x, y + split, width, height - split)
        else:
            # Vertical split: split along x-axis
            split = self.rand.randint(self.min_size, width - self.min_size)
            region1 = (x, y, split, height)
            region2 = (x + split, y, width - split, height)

        # Recursively process sub-regions
        return self._bsp_partition(region1) + self._bsp_partition(region2)

    def plot(self, width, height):
        """
        Visualize BSP regions and roads.
        """
        fig, ax = plt.subplots()
        ax.set_xlim(0, width)  # Set x-axis range
        ax.set_ylim(0, height)  # Set y-axis range
        ax.invert_yaxis()
        # Draw regions
        for region in self.regions:
            x, y, width, height = region
            ax.add_patch(patches.Rectangle((x, y), width, height, linewidth=1, edgecolor='blue', facecolor='none'))
        plt.show()

    def __call__(self, region, map_width, map_height):
        """region: (x, y, width, height)"""
        # region = (region[0]-2, region[1]-2, region[2]+4, region[3]+4)
        # region = (region[0] + 1, region[1] + 1, region[2] - 2, region[3] - 2)
        self._bsp_partition(region)
        # self.plot(map_width, map_height)
        corner_dots = []
        for idx, (x, y) in enumerate(self.corners):
            if ((x == region[0] and y == region[1])
                    or (x == region[0] and y == region[1] + region[3])
                    or (x == region[0] + region[2] and y == region[1])
                    or (x == region[0] + region[2] and y == region[1] + region[3])):
                pass
            else:
                corner_dots.append((x, y))
        return self.regions, corner_dots


if __name__ == '__main__':
    bsp = BSP(min_size=10)
    bsp((0, 0, 80, 40), 80, 40)
    print(bsp.corners)
