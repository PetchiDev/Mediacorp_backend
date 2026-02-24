from pathlib import Path
from typing import Dict, List, Optional
from src.core.logging import logger

# Supported file types and their extensions
SUPPORTED_TYPES: Dict[str, List[str]] = {
    'video': ['.mp4', '.mov', '.avi', '.mkv'],
    'audio': ['.mp3', '.wav', '.m4a', '.flac'],
    'image': ['.jpg', '.jpeg', '.png', '.webp', '.tiff'],
    'text': ['.txt', '.md', '.html', '.json']
}

# Max file sizes per category
MAX_FILE_SIZES: Dict[str, int] = {
    'video': 10 * 1024 * 1024 * 1024,    # 10 GB
    'audio': 2 * 1024 * 1024 * 1024,     # 2 GB
    'image': 100 * 1024 * 1024,          # 100 MB
    'text': 500 * 1024 * 1024            # 500 MB
}

def validate_file_type(filename: str) -> str:
    """
    Validate file extension and return its category.
    
    Args:
        filename: The name of the file to validate.
        
    Returns:
        The category of the file (e.g., 'video', 'audio').
        
    Raises:
        ValueError: If the file type is unsupported.
    """
    ext = Path(filename).suffix.lower()
    
    for category, extensions in SUPPORTED_TYPES.items():
        if ext in extensions:
            return category
    
    logger.warning(f"Unsupported file type attempted: {ext} for file {filename}")
    raise ValueError(f"Unsupported file type: {ext}")

def validate_file_size(file_size: int, category: Optional[str] = None) -> bool:
    """
    Validate file size against predefined limits.
    
    Args:
        file_size: Size in bytes.
        category: Optional category to check against specific limits.
        
    Returns:
        True if valid.
        
    Raises:
        ValueError: If file size exceeds limits.
    """
    if category:
        max_size = MAX_FILE_SIZES.get(category, MAX_FILE_SIZES['video'])
        if file_size > max_size:
            logger.warning(f"File size {file_size} exceeds {category} limit {max_size}")
            raise ValueError(f"File size exceeds limit for {category}: {max_size} bytes")
    
    # Global max limit (10 GB)
    global_max = 10 * 1024 * 1024 * 1024
    if file_size > global_max:
        logger.warning(f"File size {file_size} exceeds global limit {global_max}")
        raise ValueError("File size exceeds global limit of 10 GB")
    
    return True
