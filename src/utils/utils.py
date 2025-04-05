"""
Utility functions for the Lead Nurturing System.

This module provides utility functions used throughout the system.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, Type

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.getenv("LOG_FILE", "lead_nurturing_system.log")),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Type variable for generic functions
T = TypeVar('T')


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique ID with an optional prefix.
    
    Args:
        prefix: Optional prefix for the ID
        
    Returns:
        A unique ID string
    """
    unique_id = str(uuid.uuid4())
    if prefix:
        return f"{prefix}_{unique_id}"
    return unique_id


def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        The loaded JSON data as a dictionary
        
    Raises:
        FileNotFoundError: If the file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    logger.debug(f"Loading JSON file: {file_path}")
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in file {file_path}: {e}")
        raise


def save_json_file(data: Dict[str, Any], file_path: str) -> None:
    """
    Save data to a JSON file.
    
    Args:
        data: The data to save
        file_path: Path to the JSON file
        
    Raises:
        IOError: If the file cannot be written
    """
    logger.debug(f"Saving JSON file: {file_path}")
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        logger.error(f"Error writing to file {file_path}: {e}")
        raise


def load_objects_from_json(file_path: str, cls: Type[T]) -> List[T]:
    """
    Load objects from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        cls: The class to instantiate for each object
        
    Returns:
        A list of objects of type T
        
    Raises:
        FileNotFoundError: If the file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    logger.debug(f"Loading objects from JSON file: {file_path}")
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            logger.warning(f"Expected list in {file_path}, but got {type(data)}")
            return []
        
        objects = []
        for item in data:
            try:
                if hasattr(cls, 'from_dict'):
                    obj = cls.from_dict(item)
                else:
                    obj = cls(**item)
                objects.append(obj)
            except Exception as e:
                logger.error(f"Error creating object from {item}: {e}")
        
        return objects
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}, returning empty list")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in file {file_path}: {e}")
        return []


def save_objects_to_json(objects: List[T], file_path: str) -> None:
    """
    Save objects to a JSON file.
    
    Args:
        objects: The objects to save
        file_path: Path to the JSON file
        
    Raises:
        IOError: If the file cannot be written
    """
    logger.debug(f"Saving objects to JSON file: {file_path}")
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        data = []
        for obj in objects:
            if hasattr(obj, 'to_dict'):
                data.append(obj.to_dict())
            elif hasattr(obj, '__dict__'):
                data.append(obj.__dict__)
            else:
                logger.warning(f"Object {obj} has no to_dict method or __dict__ attribute")
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        logger.error(f"Error writing to file {file_path}: {e}")
        raise


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a datetime object as a string.
    
    Args:
        dt: The datetime object to format
        format_str: The format string to use
        
    Returns:
        The formatted datetime string
    """
    return dt.strftime(format_str)


def parse_datetime(dt_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """
    Parse a datetime string into a datetime object.
    
    Args:
        dt_str: The datetime string to parse
        format_str: The format string to use
        
    Returns:
        The parsed datetime object
        
    Raises:
        ValueError: If the string cannot be parsed
    """
    try:
        return datetime.strptime(dt_str, format_str)
    except ValueError:
        # Try ISO format as fallback
        try:
            return datetime.fromisoformat(dt_str)
        except ValueError as e:
            logger.error(f"Error parsing datetime {dt_str}: {e}")
            raise