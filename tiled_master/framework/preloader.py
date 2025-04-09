import os
import asyncio
from PIL import Image
from typing import List, Tuple

from tiled_master.framework.schema import (
    TextureTile, TextureAutoTile, TileGroup,
    TextureObject, ObjectGroup, Blueprint, Tileset
)
from tiled_master.utils.logger import logger
from tiled_master.framework.config import temp_asset_file_folder_template, place_holder_tile_path, temp_tileset_folder_template, temp_subimage_file_folder_template
from tiled_master.framework.utils import get_image_path
from tiled_master.framework.schema import (
    TileDescriptor, AutoTileDescriptor, TileGroupDescriptor,
    ObjectDescriptor, ObjectGroupDescriptor
)


class Preloader:
    def __init__(self, map_id: str):
        self.map_id = map_id
        # Dynamic tileset: all regular tiles use the same tileset with fixed tileset_id = 1
        self.dynamic_tileset_id = 1
        # Dictionary to record local_id for each dynamic image
        self.dynamic_local_ids = {
            place_holder_tile_path: 1,
        }
        # Counter for allocating local_id to different images in the dynamic tileset
        self.dynamic_counter = 2
        # Each autotile gets a new tileset_id (incremented from 2)
        self.autotile_counter = 0
        # Save all autotile information
        self.autotiles = []
        
        self.asset_save_dir = temp_asset_file_folder_template.format(map_id=self.map_id)
        os.makedirs(self.asset_save_dir, exist_ok=True)
        self.subimage_save_dir = temp_subimage_file_folder_template.format(map_id=self.map_id)
        os.makedirs(self.subimage_save_dir, exist_ok=True)
        self.tileset_save_dir = temp_tileset_folder_template.format(map_id=self.map_id)
        os.makedirs(self.tileset_save_dir, exist_ok=True)


    async def _get_image_path(self, image: str, folder_path: str) -> str:
        """
        Process the input image path using the utility function.
        
        Args:
            image: The image path or URL
            
        Returns:
            str: The local path of the image
        """
        return await get_image_path(image, folder_path)

    def _get_next_local_id(self, image_path: str) -> Tuple[int, int]:
        """
        For images in the dynamic tileset, assign a local_id based on the image_path.
        Each different image_path gets a unique local_id (new ID for first occurrence, 
        reuse for subsequent occurrences).
        
        Returns:
            Tuple[int, int]: (dynamic_tileset_id, local_id)
        """
        if image_path not in self.dynamic_local_ids:
            self.dynamic_local_ids[image_path] = self.dynamic_counter
            self.dynamic_counter += 1
        local_id = self.dynamic_local_ids[image_path]
        return self.dynamic_tileset_id, local_id

    async def load_tile_texture(self, descriptor: TileDescriptor) -> TextureTile:
        """
        Load a single tile texture from a TileDescriptor.
        
        Args:
            descriptor: TileDescriptor containing texture information
        
        Returns:
            TextureTile: The loaded tile texture object
        """
        if not descriptor.image:
            raise ValueError(f"Tile descriptor '{descriptor.resource_id}' image texture should not be empty")
        
        logger.debug(f"Loading tile texture: {descriptor.image}")
        local_path = await self._get_image_path(descriptor.image, self.asset_save_dir)
        ts_id, local_id = self._get_next_local_id(local_path)
        
        return TextureTile(
            name=descriptor.name or descriptor.resource_id,
            type="tile",
            image_path=local_path,
            collision=descriptor.collision,
            cover=descriptor.cover,
            rate=descriptor.rate,
            tileset_id=ts_id,
            local_id=local_id
        )

    async def load_autotile(self, descriptor: AutoTileDescriptor) -> TextureAutoTile:
        """
        Load an autotile texture from an AutoTileDescriptor.
        
        Args:
            descriptor: AutoTileDescriptor containing autotile texture information
        
        Returns:
            TextureAutoTile: The loaded autotile texture object
        """
        if not descriptor.image:
            raise ValueError(f"AutoTile descriptor '{descriptor.resource_id}' image texture should not be empty")
        
        logger.debug(f"Loading autotile texture: {descriptor.image}")
        local_path = await self._get_image_path(descriptor.image, self.tileset_save_dir)
        
        # Assign a new tileset_id for the autotile
        self.autotile_counter += 1
        autotile_tileset_id = self.dynamic_tileset_id + self.autotile_counter
        
        # Record autotile tileset information
        method = descriptor.method
        if method == "tile48":
            tilecount = 48
            columns = 8
            imagewidth = 16 * 8
            imageheight = 16 * 6
        elif method == "inner16":
            tilecount = 16
            columns = 4
            imagewidth = 16 * 4
            imageheight = 16 * 4
        elif method == "blob47":
            tilecount = 57
            columns = 11
            imagewidth = 16 * 11
            imageheight = 16 * 5
        else:
            raise Exception("invalid autotile method input")
            
        autotile_tileset = {
            "tileset_id": autotile_tileset_id,
            "tileset_path": local_path,
            "columns": columns,
            "tilecount": tilecount,
            "imagewidth": imagewidth,
            "imageheight": imageheight
        }
        self.autotiles.append(autotile_tileset)
        
        return TextureAutoTile(
            name=descriptor.name or descriptor.resource_id,
            type="autotile",
            method=method,
            image_path=local_path,
            collision=descriptor.collision,
            cover=descriptor.cover,
            rate=descriptor.rate,
            tileset_id=autotile_tileset_id
        )

    async def load_tile_group(self, descriptor: TileGroupDescriptor) -> TileGroup:
        """
        Load a tile group from a TileGroupDescriptor with concurrent loading.
        
        Args:
            descriptor: TileGroupDescriptor containing tile group information
        
        Returns:
            TileGroup: The loaded tile group object
        """
        # Create tasks for loading tiles and auto tiles
        load_tasks = []
        
        # Add tasks for loading tiles
        load_tasks.extend([
            self.load_tile_texture(tile_desc) 
            for tile_desc in descriptor.tiles
        ])
        
        # Add tasks for loading auto tiles
        load_tasks.extend([
            self.load_autotile(auto_tile_desc) 
            for auto_tile_desc in descriptor.auto_tiles
        ])
        
        # Concurrently load all textures
        loaded_textures = await asyncio.gather(*load_tasks)
        
        return TileGroup(
            type="tilegroup",
            textures=loaded_textures,
            scale=descriptor.scale
        )

    async def load_object(self, descriptor: ObjectDescriptor) -> TextureObject:
        """
        Load an object from an ObjectDescriptor.
        
        Args:
            descriptor: ObjectDescriptor containing object information
        
        Returns:
            TextureObject: The loaded object
        """
        # Get the local path of the large image (download if it's a URL)
        logger.debug(f"Loading object texture: {descriptor.image}")
        url = descriptor.image or ""
        tile_width = 16
        tile_height = 16
        # Prepare blueprint list
        blueprints = []
        
        if url:
            try:
                big_image_path = await self._get_image_path(
                    url, 
                    self.asset_save_dir
                )

                img = Image.open(big_image_path)
                original_width, original_height = img.size

                grid_width = descriptor.width
                target_width_px = grid_width * tile_width
                scale_factor = target_width_px / original_width if original_width else 1.0

                target_height_px = int(original_height * scale_factor)
                grid_height = target_height_px // tile_height + 1

                # Resize the image
                img_resized = img.resize((target_width_px, target_height_px), Image.Resampling.LANCZOS)

                if descriptor.resource_type == "object":
                    img_resized.save(big_image_path)

                base_dir = self.subimage_save_dir
                base_filename, _ = os.path.splitext(os.path.basename(big_image_path))
                
                # Cut the image into grid cells
                for y in range(grid_height):
                    for x in range(grid_width):
                        left = x * tile_width
                        upper = y * tile_width
                        right = (x + 1) * tile_width
                        lower = (y + 1) * tile_width
                        tile_img = img_resized.crop((left, upper, right, lower))

                        # Create filename for the sub-image
                        tile_filename = f"{base_filename}_{x}_{y}.png"
                        tile_path = os.path.join(base_dir, tile_filename)

                        # Ensure the directory exists
                        os.makedirs(base_dir, exist_ok=True)

                        # Save the cropped image if it doesn't exist
                        if not os.path.exists(tile_path):
                            tile_img.save(tile_path)

                        # Dynamically assign tileset_id and local_id
                        ts_id, local_id = self._get_next_local_id(tile_path)

                        # Create TextureTile object for the sub-image
                        tile_texture = TextureTile(
                            name=f"{descriptor.name or descriptor.resource_id}_{x}_{y}",
                            type="tile",
                            image_path=tile_path,
                            collision=descriptor.collision,
                            cover=descriptor.cover,
                            rate=descriptor.rate or 1,
                            tileset_id=ts_id,
                            local_id=local_id
                        )

                        # Create blueprint
                        blueprint = Blueprint(
                            texture=tile_texture,
                            relative_x=x,
                            relative_y=y
                        )
                        blueprints.append(blueprint)

            except Exception as e:
                logger.error(f"Failed to load object image: {e}")
                # Fallback to placeholder
                grid_width = descriptor.width
                grid_height = descriptor.height
                tile_path = place_holder_tile_path
                big_image_path = os.path.join(self.asset_save_dir, f"{descriptor.name or descriptor.resource_id}.png")
                
                img = Image.open(tile_path)
                target_width_px = grid_width * tile_width
                target_height_px = grid_height * tile_height
                original_width, original_height = target_width_px, target_height_px
                img_resized = img.resize((target_width_px, target_height_px), Image.Resampling.LANCZOS)
                img_resized.save(big_image_path)
                
                for y in range(grid_height):
                    for x in range(grid_width):
                        # Dynamically assign tileset_id and local_id
                        ts_id, local_id = self._get_next_local_id(tile_path)
                        # Create TextureTile object
                        tile_texture = TextureTile(
                            name=f"{descriptor.name or descriptor.resource_id}_{x}_{y}",
                            type="tile",
                            image_path=tile_path,
                            collision=descriptor.collision,
                            cover=descriptor.cover,
                            rate=descriptor.rate or 1,
                            tileset_id=ts_id,
                            local_id=local_id
                        )
                        # Create blueprint
                        blueprint = Blueprint(
                            texture=tile_texture,
                            relative_x=x,
                            relative_y=y
                        )
                        blueprints.append(blueprint)

        else:
            # Create a placeholder image
            grid_width = descriptor.width
            grid_height = descriptor.height
            tile_path = place_holder_tile_path
            try:
                img = Image.open(tile_path)
            except Exception as e:
                raise ValueError(f"Cannot open image {tile_path}: {e}")
                
            target_width_px = grid_width * tile_width
            target_height_px = grid_height * tile_height
            original_width, original_height = target_width_px, target_height_px
            img_resized = img.resize((target_width_px, target_height_px), Image.Resampling.LANCZOS)
            big_image_path = os.path.join(self.asset_save_dir, f"{descriptor.name or descriptor.resource_id}.png")
            img_resized.save(big_image_path)
            
            for y in range(grid_height):
                for x in range(grid_width):
                    # Dynamically assign tileset_id and local_id
                    ts_id, local_id = self._get_next_local_id(tile_path)
                    # Create TextureTile object
                    tile_texture = TextureTile(
                        name=f"{descriptor.name or descriptor.resource_id}_{x}_{y}",
                        type="tile",
                        image_path=tile_path,
                        collision=descriptor.collision,
                        cover=descriptor.cover,
                        rate=descriptor.rate or 1,
                        tileset_id=ts_id,
                        local_id=local_id
                    )
                    # Create blueprint
                    blueprint = Blueprint(
                        texture=tile_texture,
                        relative_x=x,
                        relative_y=y
                    )
                    blueprints.append(blueprint)

        # Return TextureObject
        return TextureObject(
            name=descriptor.name or descriptor.resource_id,
            type=descriptor.resource_type,
            shape="rectangle",
            image_path=big_image_path,
            image_url=url,
            width=grid_width,
            height=grid_height,
            original_width=original_width,
            original_height=original_height,
            functions=descriptor.functions,
            collision=descriptor.collision,
            cover=descriptor.cover,
            rate=descriptor.rate or 1,
            blueprints=blueprints
        )

    async def load_object_group(self, descriptor: ObjectGroupDescriptor) -> ObjectGroup:
        """
        Load an object group from an ObjectGroupDescriptor with concurrent loading.
        
        Args:
            descriptor: ObjectGroupDescriptor containing object group information
        
        Returns:
            ObjectGroup: The loaded object group
        """
        # Create tasks for loading objects
        load_tasks = [
            self.load_object(obj_desc) 
            for obj_desc in descriptor.objects
        ]
        
        # Concurrently load all objects
        loaded_objects = await asyncio.gather(*load_tasks)
        
        return ObjectGroup(
            type="objectdata",
            textures=loaded_objects,
            scale=descriptor.scale
        )

    def _assemble_dynamic_tileset(self) -> Tileset:
        """
        Assemble dynamic tileset from all the registered tiles.
        Creates a combined image with tiles arranged in a grid format.
        
        Returns:
            Tileset: The assembled dynamic tileset
        """
        # Calculate tile properties
        tile_width = 16  # default tile width
        tile_height = 16  # default tile height
        columns = 16  # predefined number of columns for the tileset
        tile_count = len(self.dynamic_local_ids)  # count of dynamic tiles

        if tile_count == 0:
            raise ValueError("No tiles available to assemble dynamic tileset")

        # Calculate rows needed for all tiles
        rows = (tile_count + columns - 1) // columns

        # Create a blank image for all tiles
        total_width = columns * tile_width
        total_height = rows * tile_height
        combined_image = Image.new("RGBA", (total_width, total_height))

        # Create tileset name and path
        tileset_name = f"dynamic_tileset_{self.dynamic_tileset_id}"
        combined_image_path = os.path.join(self.tileset_save_dir, f"{tileset_name}.png")

        # Place each tile at the correct position
        for tile_image_path, local_id in self.dynamic_local_ids.items():
            x = ((local_id - 1) % columns) * tile_width
            y = ((local_id - 1) // columns) * tile_height

            # Open the tile image and paste it in the combined image
            try:
                tile_image = Image.open(tile_image_path)
                combined_image.paste(tile_image, (x, y))
            except Exception as e:
                logger.error(f"Error processing tile {tile_image_path}: {e}")

        # Save the combined image
        combined_image.save(combined_image_path)
        logger.info(f"Dynamic tileset saved at: {combined_image_path}")

        
        tileset = Tileset(
            tileset_id=self.dynamic_tileset_id,
            name="default_tileset",
            columns=16,
            firstgid=1,
            image=combined_image_path,
            imagewidth=total_width,
            imageheight=total_height,
            margin=0,
            spacing=0,
            tilecount=tile_count,
            tilewidth=tile_width,
            tileheight=tile_height
        )
        return tileset

    def process_tilesets(self) -> List[Tileset]:
        """
        Process all tilesets, including dynamic tileset and autotiles.
        
        Returns:
            List: List of all Tileset objects
        """
        all_tilesets = []

        # Include dynamic tileset
        dynamic_tileset = self._assemble_dynamic_tileset()
        all_tilesets.append(dynamic_tileset)
        gid_count = dynamic_tileset.tilecount

        for autotile_data in self.autotiles:
            autotile = Tileset(
                tileset_id=autotile_data["tileset_id"],
                name=f"autotile_{autotile_data['tileset_id']}",
                columns=autotile_data["columns"],
                firstgid=1 + gid_count,
                image=autotile_data["tileset_path"],
                imagewidth=autotile_data["imagewidth"],
                imageheight=autotile_data["imageheight"],
                margin=0,
                spacing=0,
                tilecount=autotile_data["tilecount"],
                tilewidth=16,
                tileheight=16
            )
            gid_count += autotile.tilecount
            all_tilesets.append(autotile)

        return all_tilesets
