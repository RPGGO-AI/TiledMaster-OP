import os
import aiohttp
import aiofiles
from urllib.parse import urlparse
from tiled_master.utils.logger import logger
from PIL import Image
import asyncio


def is_url(image_str: str) -> bool:
    """
    Determine if a string is a valid URL.
    
    Args:
        image_str: The string to check
        
    Returns:
        bool: True if the string is a URL, False otherwise
    """
    try:
        result = urlparse(image_str)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


async def get_image_path(image: str, save_dir: str) -> str:
    """
    Process the input image path. If it's a URL, download the image,
    otherwise return the original input.
    
    Args:
        image: The image path or URL
        save_dir: The directory to save the image to if it's a URL
        
    Returns:
        str: The local path of the image
    """
    if is_url(image):
        return await download_and_validate_file(image, save_dir)
    return image


async def download_image(url: str, save_dir: str) -> str:
    """
    Download an image from a URL and save it to the specified directory.
    
    Args:
        url: The URL of the image
        save_dir: The directory to save the image to
        
    Returns:
        str: The local path of the downloaded image
    """
    logger.debug(f"Start downloading: {url}")
    # Ensure save directory exists
    os.makedirs(save_dir, exist_ok=True)

    # Extract filename
    filename = os.path.basename(urlparse(url).path) or "downloaded_image"
    local_path = os.path.join(save_dir, filename)
    
    # Skip download if file exists in local debug environment
    if os.path.exists(local_path):
        return local_path
    
    try:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        try:
                            async with aiofiles.open(local_path, "wb") as f:
                                await f.write(await response.read())
                            logger.debug(f"Download {url} to {local_path}")
                            return local_path
                        except Exception as file_error:
                            raise ValueError(f"Failed to write downloaded data to {local_path}: {file_error or 'Unknown file write error'}")
                    else:
                        raise ValueError(f"Failed to download image {url}, status code: {response.status}")
            except aiohttp.ClientError as client_error:
                raise ValueError(f"HTTP client error when downloading {url}: {client_error or 'Unknown HTTP client error'}")
            except asyncio.TimeoutError:
                raise ValueError(f"Timeout when downloading {url} (exceeded 5 seconds)")
    except Exception as session_error:
        # Capture ClientSession creation or other unforeseen errors
        if not str(session_error):  # If error message is empty
            raise ValueError(f"Unknown error creating session or downloading {url}: {type(session_error).__name__}")
        raise ValueError(f"Session error when downloading {url}: {session_error}")


async def download_and_validate_file(
    url: str, 
    save_dir: str, 
    max_attempts: int = 3, 
    validator_func: callable = None,
    file_type: str = 'image'
) -> str:
    """
    Download a file from a URL with robust validation and retry mechanism.
    
    Args:
        url: The URL of the file to download
        save_dir: The directory to save the file
        max_attempts: Maximum number of download attempts
        validator_func: Optional custom validation function
        file_type: Type of file for logging purposes
    
    Returns:
        str: The local path of the downloaded and validated file
    
    Raises:
        Exception: If file cannot be downloaded or validated after max attempts
    """
    os.makedirs(save_dir, exist_ok=True)
    
    # Default validator for images
    def default_image_validator(file_path):
        try:
            # Use context manager to ensure image is properly closed
            with Image.open(file_path) as img:
                # Check image mode and size
                if img.mode not in ('1', 'L', 'P', 'RGB', 'RGBA'):
                    logger.error(f"Unsupported image mode: {img.mode}")
                    return False
                
                # Verify image dimensions
                width, height = img.size
                if width <= 0 or height <= 0:
                    logger.error(f"Invalid image dimensions: {width}x{height}")
                    return False
                
                # Attempt to load pixel data
                try:
                    img.load()
                except Exception as e:
                    logger.error(f"Failed to load image pixels: {e}")
                    return False
                
            return True
        except Exception as e:
            logger.error(f"Invalid image file: {file_path}, Error: {e}")
            return False
    
    # Use custom validator or default image validator
    validator = validator_func or (default_image_validator if file_type == 'image' else lambda x: True)
    
    attempts = 0
    while attempts < max_attempts:
        try:
            # Download the file
            local_path = await download_image(url, save_dir)
            
            # Validate the file
            if validator(local_path):
                return local_path
            
            # If validation fails, remove the file
            if os.path.exists(local_path):
                os.remove(local_path)
            
            attempts += 1
            await asyncio.sleep(0.2)
        
        except Exception as e:
            error_msg = str(e) if str(e) else f"Unknown {type(e).__name__} exception (no error message)"
            logger.error(f"Downloading {url} attempt {attempts + 1}/{max_attempts} failed: {error_msg}")
            # Log additional debug information
            if not str(e):
                logger.error(f"Detailed error type: {type(e).__name__}, dir(e): {dir(e)}")
            attempts += 1
            await asyncio.sleep(0.2)
    
    raise Exception(f"Failed to download valid {file_type} from {url} after {max_attempts} attempts. Last attempt error: {error_msg if 'error_msg' in locals() else 'Not recorded'}")
