import codecs
import json
import numpy
import os
import hashlib
import shutil
from PIL import Image

from tiled_master.utils.globalvaris import CACHE_FOLDER


def stable_hash(content: str):
    # Create a stable hash value
    m = hashlib.sha256()
    combined = f"{content}".encode('utf-8')
    m.update(combined)
    # Generate an integer as a random seed
    return int.from_bytes(m.digest()[:8], 'big')


def write_json(file_path, data_json):
    def default_serializer(obj):
        if isinstance(obj, (numpy.integer)):
            return int(obj)  # Convert NumPy integers to Python int
        if isinstance(obj, (numpy.floating)):
            return float(obj)  # Convert NumPy floats to Python float
        if isinstance(obj, (numpy.ndarray)):
            return obj.tolist()  # Convert NumPy arrays to lists
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    with codecs.open(file_path, 'w+', encoding="utf-8") as fp:
        content = json.dumps(data_json, ensure_ascii=False, indent=4, default=default_serializer)
        fp.write(content)


def crop_to_non_transparent_area(image_path, output_path):
    # Open the image
    img = Image.open(image_path).convert("RGBA")

    # Get the pixel data of the image
    data = img.getdata()

    # Find the boundary of non-transparent pixels
    non_transparent_pixels = [
        (x, y) for y in range(img.height) for x in range(img.width)
        if data[y * img.width + x][3] != 0
    ]

    if not non_transparent_pixels:
        raise ValueError("Image is completely transparent, no non-transparent part")

    x_coords, y_coords = zip(*non_transparent_pixels)
    left, upper = min(x_coords), min(y_coords)
    right, lower = max(x_coords), max(y_coords)

    # Crop the image
    cropped_img = img.crop((left, upper, right + 1, lower + 1))

    # Save the cropped image
    cropped_img.save(output_path, "PNG")
    print(f"Cropped image has been saved to {output_path}")


def is_transparent(image: Image.Image) -> bool:
    if image.mode != "RGBA":
        return False

    alpha_channel = image.getchannel("A")
    return not alpha_channel.getbbox()


def get_filename_without_extension(file_path):
    """Returns the filename without its extension"""
    return os.path.splitext(os.path.basename(file_path))[0]


def getCacheFolder(sub_folder):
    folder_path = os.path.join(CACHE_FOLDER, sub_folder)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    return folder_path


def removeFolder(folder_path: str):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)


def read_json(config_path):
    with open(config_path, "r", encoding='utf-8', errors='ignore') as f:
        return json.load(f)
