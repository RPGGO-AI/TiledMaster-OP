import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import gc

import tiled_master.framework.config as config

from tiled_master.framework.map_cache import MapCache
from tiled_master.utils.logger import logger_runtime


@logger_runtime()
def visualize_tilemap(tilemap, img_path=None, preview=True):
    # Extract basic map information
    width, height = tilemap['width'], tilemap['height']
    tilewidth, tileheight = tilemap['tilewidth'], tilemap['tileheight']
    tilesets = tilemap['tilesets']

    # ------------------------------------------------
    # 1) Put all tileset tiles into a dictionary tiles_dict
    #    where key = global GID, value = corresponding image
    # ------------------------------------------------
    tiles_dict = {}
    try:
        for ts_info in tilesets:
            firstgid = ts_info['firstgid']
            tilecount = ts_info['tilecount']
            tileset_columns = ts_info['columns']
            # Open the tileset image
            with Image.open(ts_info['image']) as tileset_image:
                # Crop individual tiles and store in dictionary
                for local_id in range(tilecount):
                    col = local_id % tileset_columns
                    row = local_id // tileset_columns
                    left = col * tilewidth
                    upper = row * tileheight
                    right = left + tilewidth
                    lower = upper + tileheight

                    gid = firstgid + local_id  # Global GID
                    tile_image = tileset_image.crop((left, upper, right, lower))
                    tiles_dict[gid] = tile_image

        # ------------------------------------------------
        # 2) Create drawing canvas (normal map, collision map, cover map)
        # ------------------------------------------------
        normal_map = Image.new("RGBA", (width * tilewidth, height * tileheight), (0, 0, 0, 255))
        collision_map = Image.new("RGBA", (width * tilewidth, height * tileheight))
        cover_map = Image.new("RGBA", (width * tilewidth, height * tileheight))

        # ------------------------------------------------
        # 3) Traverse each layer and draw tiles on corresponding canvas
        # ------------------------------------------------
        for layer in tilemap['layers']:
            # Skip if not a tilelayer or layer is not visible (and not an obstacle or cover layer)
            if (layer['id'] not in [config.obstacle_layer, config.cover_layer] and not layer['visible']):
                continue

            if layer['type'] == 'tilelayer':
                data = np.array(layer['data']).reshape((height, width))
                layer_id = layer['id']

                # Select target layer
                target_map = normal_map
                if layer_id == config.obstacle_layer:
                    target_map = collision_map
                elif layer_id == config.cover_layer:
                    target_map = cover_map

                # Draw tiles on target map
                for y in range(height):
                    for x in range(width):
                        gid = data[y, x]
                        if gid == 0:
                            continue  # Skip blank tiles

                        tile_image = tiles_dict.get(gid)
                        if tile_image is not None:
                            target_map.paste(tile_image, (x * tilewidth, y * tileheight), tile_image)

        # Process objectgroup type layers
        for layer in tilemap['layers']:
            if layer['type'] == 'objectgroup':
                for object_data in layer['objects']:
                    # Avoid using "property" as a variable name to prevent overriding built-in function
                    for prop in object_data["properties"]:
                        object_image = None
                        if prop["name"] == "image_path":
                            with Image.open(prop["value"]) as obj_img:
                                object_image = obj_img.convert("RGBA") if obj_img.mode == "P" else obj_img.copy()

                        if object_image:
                            if object_image.mode == "RGBA":
                                # Resize the object image using nearest neighbor interpolation
                                object_image = object_image.resize(
                                    (object_data["width"], object_data["height"]), Image.Resampling.NEAREST
                                )
                                mask = object_image.split()[3]  # Extract Alpha channel as mask
                                normal_map.paste(object_image, (int(object_data["x"]), int(object_data["y"])), mask)
                                # Ensure resource release
                                mask = None
                                object_image = None

        # ------------------------------------------------
        # 4) If preview is not needed, save the image and release resources
        # ------------------------------------------------
        if not preview:
            if img_path is not None:
                # Directly use PIL to save image, avoiding matplotlib
                normal_map.save(img_path)
            
            # Clean up resources
            normal_map.close()
            collision_map.close()
            cover_map.close()
            # Clean up tile dictionary
            for tile in tiles_dict.values():
                if hasattr(tile, 'close'):
                    tile.close()
            tiles_dict.clear()
            # Force garbage collection
            gc.collect()
            return img_path
        
        # ------------------------------------------------
        # 5) If preview is needed, use matplotlib to display
        # ------------------------------------------------
        # Use object-oriented interface to draw images, ensuring each thread manages its own Figure
        # ------------------------------------------------
        fig_width = 8
        fig_height = 4

        try:
            # In preview mode, show normal map, collision map, and cover map
            fig_normal, ax_normal = plt.subplots(figsize=(fig_width, fig_height), dpi=100, facecolor='black')  # Create normal map figure and axes
            ax_normal.imshow(normal_map)  # Plot normal map on its axes
            ax_normal.axis('off')
            fig_normal.subplots_adjust(left=0, right=1, top=1, bottom=0)

            fig_collision, ax_collision = plt.subplots(figsize=(fig_width, fig_height), dpi=100)  # Create collision map figure and axes
            ax_collision.imshow(collision_map)
            ax_collision.set_title('Collision Map')
            ax_collision.axis('off')
            fig_collision.subplots_adjust(left=0, right=1, top=1, bottom=0)

            fig_cover, ax_cover = plt.subplots(figsize=(fig_width, fig_height), dpi=100)  # Create cover map figure and axes
            ax_cover.imshow(cover_map)
            ax_cover.set_title('Cover Map')
            ax_cover.axis('off')
            fig_cover.subplots_adjust(left=0, right=1, top=1, bottom=0)

            # Display all figures from this thread
            plt.show()

            # If save path is specified, save the image
            if img_path is not None:
                fig_normal.savefig(img_path)

            # Before returning, clean up resources
            return img_path
        finally:
            # Ensure resources are released even in exceptional cases
            # Close each Figure to release resources
            if 'fig_normal' in locals():
                plt.close(fig_normal)
            if 'fig_collision' in locals():
                plt.close(fig_collision)
            if 'fig_cover' in locals():
                plt.close(fig_cover)
            
            # Close all matplotlib figures, just in case
            plt.close('all')
            
            # Release PIL image resources
            normal_map.close()
            collision_map.close()
            cover_map.close()
            
            # Clean up tile dictionary
            for tile in tiles_dict.values():
                if hasattr(tile, 'close'):
                    tile.close()
            tiles_dict.clear()
            
            # Force garbage collection
            gc.collect()
    except Exception as e:
        # Ensure we try to clean up resources even if an exception occurs
        print(f"Error during tilemap visualization: {e}")
        # Close all matplotlib figures
        plt.close('all')
        # Force garbage collection
        gc.collect()
        # Re-raise the exception
        raise


def plot_map_cache(map_cache: 'MapCache', target_layer=None):
    """
    Visualize the latest version of the MapCache object.
    Where map_cache.tile_data[layer, y, x] = (tileset_idx, local_id),
    If tileset_idx < 0, it means there is no tile.

    :param map_cache: MapCache object
    :param target_layer: If specified, only render that layer; otherwise, multiple layers are superimposed.
    """
    import matplotlib.pyplot as plt
    import random

    width = map_cache.width
    height = map_cache.height
    layers = map_cache.layer_nums

    # 1) Collect all unique (tileset_idx, local_id) pairs
    unique_pairs = set()
    if target_layer is not None:
        # Only collect the specified layer
        for y in range(height):
            for x in range(width):
                ts_idx, local_id, collide, cover = map_cache.tile_data[target_layer, y, x]
                if ts_idx >= 0:  # There is a tile
                    unique_pairs.add((ts_idx, local_id))
    else:
        # Collect all layers
        for layer_idx in range(layers):
            for y in range(height):
                for x in range(width):
                    ts_idx, local_id, collide, cover = map_cache.tile_data[layer_idx, y, x]
                    if ts_idx >= 0:
                        unique_pairs.add((ts_idx, local_id))

    # 2) Assign a random color to each (ts_idx, local_id) pair
    pair_to_color = {}
    for pair in unique_pairs:
        pair_to_color[pair] = [random.random(), random.random(), random.random()]

    # 3) Build the RGB array for visualization (height, width, 3)
    tile_colors = np.zeros((height, width, 3), dtype=float)

    if target_layer is not None:
        # Only render the specified layer
        for y in range(height):
            for x in range(width):
                ts_idx, local_id, collide, cover = map_cache.tile_data[target_layer, y, x]
                if ts_idx >= 0:
                    tile_colors[y, x] = pair_to_color[(ts_idx, local_id)]
    else:
        # Multiple layers: the uppermost non-empty tile covers the lower layer
        for layer_idx in range(layers):
            for y in range(height):
                for x in range(width):
                    ts_idx, local_id, collide, cover = map_cache.tile_data[layer_idx, y, x]
                    if ts_idx >= 0:
                        tile_colors[y, x] = pair_to_color[(ts_idx, local_id)]

    # 4) Draw
    plt.figure(figsize=(10, 10))
    plt.imshow(tile_colors, interpolation='nearest')
    plt.title("Map Cache Visualization")
    plt.axis("off")
    plt.show()