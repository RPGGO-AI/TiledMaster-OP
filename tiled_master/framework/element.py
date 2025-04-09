from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TypeVar
from tiled_master.framework.preloader import Preloader
from tiled_master.framework.map_cache import MapCache
from tiled_master.framework.schema import *
from tiled_master.utils.logger import logger

# Type variable for method chaining
T = TypeVar('T', bound='MapElement')


class MapElement(ABC):
    """
    Abstract base class for all map elements.
    Provides framework capabilities for resource management and building.
    """
    
    class Resources:
        """Base class for resource ID definitions."""
        pass
    
    def __init__(self, 
                 name: str,
                 descriptors: Optional[Dict[str, ResourceDescriptor]] = None,
                 **data):
        """
        Initialize the element and set up resources
        
        Args:
            name: The name of the element
            descriptors: Dictionary of pre-defined resource descriptors that must
                        completely override any pre-registered descriptors.
                        Keys are resource_ids, values are ResourceDescriptor instances.
            **data: Additional data for initialization
            
        Raises:
            ValueError: If descriptors doesn't completely cover all required resource descriptors
                        or if descriptor types don't match expected types
        """
        self.name = name
        # Define attributes that were previously PrivateAttr
        self._resource_descriptors = {}
        self._resource_types = {}
        # Define attributes that were previously Field
        self.loaded_resources = {}
        
        # Handle any additional data passed
        for key, value in data.items():
            setattr(self, key, value)
        
        # First set up resources to determine required descriptors
        self._setup_resources()
        
        # Get the set of required resource_ids
        required_resource_ids = set(self._resource_descriptors.keys())
        
        # Check if descriptors completely cover the required resources
        if descriptors:
            provided_resource_ids = set(descriptors.keys())
            missing_resource_ids = required_resource_ids - provided_resource_ids
            
            if missing_resource_ids:
                raise ValueError(f"Missing required descriptors: {', '.join(missing_resource_ids)}")
            
            # Validate descriptor types match expected types
            type_errors = []
            for resource_id in required_resource_ids:
                expected_type = self._resource_types.get(resource_id)
                if expected_type and not isinstance(descriptors[resource_id], expected_type):
                    type_errors.append(
                        f"Resource '{resource_id}' expected type {expected_type.__name__}, "
                        f"got {type(descriptors[resource_id]).__name__}"
                    )
            
            if type_errors:
                raise ValueError(f"Type mismatch in provided descriptors:\n" + "\n".join(type_errors))
            
            # Replace all descriptors with the provided ones
            self._resource_descriptors = {}
            for resource_id, descriptor in descriptors.items():
                self._resource_descriptors[resource_id] = descriptor
        
        # No need to call _setup_resources() again as we've already done it
    
    def __getattr__(self, name):
        """Allow resource access through attributes"""
        if name in self.loaded_resources:
            return self.loaded_resources[name]
        raise AttributeError(f"{self.__class__.__name__} has no attribute or resource '{name}'")
    
    def _get_resource(self, resource_id):
        """Safely get a resource by ID, supporting both enum and string IDs"""
        if hasattr(resource_id, "value"):  # Support for enums
            key = resource_id.value
        else:
            key = resource_id
        
        if key not in self.loaded_resources:
            raise KeyError(f"Resource '{key}' not found in {self.__class__.__name__}")
        
        return self.loaded_resources[key]
    
    @abstractmethod
    def _setup_resources(self):
        """
        Abstract method to set up resources for this element.
        Must be implemented by subclasses to define required resources.
        
        Note: If external descriptors were provided in __init__, they will already
        be populated in self._resource_descriptors before this method is called.
        Implementations should check or be aware of this to avoid duplications.
        """
        pass
    
    def _add_tile_group(self, resource_id: str, scale: int = -1) -> TileGroupDescriptor:
        """
        Add a tile group resource descriptor.
        
        Args:
            resource_id: Unique identifier for this resource
            scale: Scale factor for the tile group
            
        Returns:
            The created TileGroupDescriptor for method chaining
        """
        # If this resource_id already exists, log a warning and override it
        if resource_id in self._resource_descriptors:
            logger.warning(f"Resource ID '{resource_id}' already exists and will be overridden")
            
        descriptor = TileGroupDescriptor(resource_id=resource_id, scale=scale)
        self._resource_descriptors[resource_id] = descriptor
        self._resource_types[resource_id] = TileGroupDescriptor
        return descriptor
    
    def _add_object_group(self, resource_id: str, scale: int = -1) -> ObjectGroupDescriptor:
        """
        Add an object group resource descriptor.
        
        Args:
            resource_id: Unique identifier for this resource
            scale: Scale factor for the object group
            
        Returns:
            The created ObjectGroupDescriptor for method chaining
        """
        # If this resource_id already exists, log a warning and override it
        if resource_id in self._resource_descriptors:
            logger.warning(f"Resource ID '{resource_id}' already exists and will be overridden")
            
        descriptor = ObjectGroupDescriptor(resource_id=resource_id, scale=scale)
        self._resource_descriptors[resource_id] = descriptor
        self._resource_types[resource_id] = ObjectGroupDescriptor
        return descriptor
    
    def _add_tile(self, resource_id: str, image: str, **kwargs) -> TileDescriptor:
        """
        Add a single tile resource descriptor.
        
        Args:
            resource_id: Unique identifier for this resource
            image: Path or URL to the tile image
            **kwargs: Additional tile properties
            
        Returns:
            The created TileDescriptor
        """
        # If this resource_id already exists, log a warning and override it
        if resource_id in self._resource_descriptors:
            logger.warning(f"Resource ID '{resource_id}' already exists and will be overridden")
            
        descriptor = TileDescriptor(resource_id=resource_id, image=image, **kwargs)
        self._resource_descriptors[resource_id] = descriptor
        self._resource_types[resource_id] = TileDescriptor
        return descriptor
    
    def _add_auto_tile(self, resource_id: str, image: str, **kwargs) -> AutoTileDescriptor:
        """
        Add an auto tile resource descriptor.
        
        Args:
            resource_id: Unique identifier for this resource
            image: Path or URL to the auto tile image
            **kwargs: Additional auto tile properties
            
        Returns:
            The created AutoTileDescriptor
        """
        # If this resource_id already exists, log a warning and override it
        if resource_id in self._resource_descriptors:
            logger.warning(f"Resource ID '{resource_id}' already exists and will be overridden")
            
        descriptor = AutoTileDescriptor(resource_id=resource_id, image=image, **kwargs)
        self._resource_descriptors[resource_id] = descriptor
        self._resource_types[resource_id] = AutoTileDescriptor
        return descriptor
    
    def _add_object(self, resource_id: str, name: Optional[str] = None, image: Optional[str] = None, **kwargs) -> ObjectDescriptor:
        """
        Add a single object resource descriptor.
        
        Args:
            resource_id: Unique identifier for this resource
            name: Display name of the object (defaults to resource_id if None)
            image: Path or URL to the object image
            **kwargs: Additional object properties
            
        Returns:
            The created ObjectDescriptor
        """
        # If this resource_id already exists, log a warning and override it
        if resource_id in self._resource_descriptors:
            logger.warning(f"Resource ID '{resource_id}' already exists and will be overridden")
            
        descriptor = ObjectDescriptor(
            resource_id=resource_id, 
            name=name, 
            image=image, 
            rate=kwargs.get('rate', 1),
            **kwargs
        )
        self._resource_descriptors[resource_id] = descriptor
        self._resource_types[resource_id] = ObjectDescriptor
        return descriptor
    
    async def preload(self, preloader: Preloader):
        """
        Asynchronously preload all resources defined in this element with concurrent loading.
        
        Args:
            preloader: The preloader instance to use
            
        Raises:
            ValueError: If a resource descriptor has an empty image field
        """
        import asyncio
        
        async def load_resource(resource_id, descriptor):
            """
            Internal async loading function to handle loading of different resource types.
            
            Args:
                resource_id: Unique identifier for the resource
                descriptor: Resource descriptor containing loading information
            
            Returns:
                Tuple of (resource_id, loaded_resource)
            
            Raises:
                ValueError: If resource image is empty or invalid
            """
            if descriptor.resource_type == "tile":
                if not descriptor.image:
                    raise ValueError(f"Tile resource '{resource_id}' image texture should not be empty")
                return resource_id, await preloader.load_tile_texture(descriptor)
            
            elif descriptor.resource_type == "auto_tile":
                if not descriptor.image:
                    raise ValueError(f"AutoTile resource '{resource_id}' image texture should not be empty")
                return resource_id, await preloader.load_autotile(descriptor)
            
            elif descriptor.resource_type == "tile_group":
                # Check tile group validity
                if not descriptor.tiles and not descriptor.auto_tiles:
                    logger.warning(f"TileGroup '{resource_id}' has no tiles or auto_tiles")
                
                # Validate each tile's image
                for tile in descriptor.tiles:
                    if not tile.image:
                        raise ValueError(f"Tile '{tile.resource_id}' in tile group '{resource_id}' image texture should not be empty")
                
                # Validate each auto_tile's image
                for auto_tile in descriptor.auto_tiles:
                    if not auto_tile.image:
                        raise ValueError(f"AutoTile '{auto_tile.resource_id}' in tile group '{resource_id}' image texture should not be empty")
                
                return resource_id, await preloader.load_tile_group(descriptor)
            
            elif descriptor.resource_type == "object":
                if not descriptor.image:
                    raise ValueError(f"Object resource '{resource_id}' image texture should not be empty")
                return resource_id, await preloader.load_object(descriptor)
            
            elif descriptor.resource_type == "object_group":
                # Check object group validity
                if not descriptor.objects:
                    logger.warning(f"ObjectGroup '{resource_id}' has no objects")
                
                # Validate each object's image
                for obj in descriptor.objects:
                    if not obj.image:
                        raise ValueError(f"Object '{obj.resource_id}' in object group '{resource_id}' image texture should not be empty")
                
                return resource_id, await preloader.load_object_group(descriptor)
            
            else:
                raise ValueError(f"Unknown resource type: {descriptor.resource_type}")

        # Create tasks for loading resources
        load_tasks = [
            load_resource(resource_id, descriptor) 
            for resource_id, descriptor in self._resource_descriptors.items()
        ]
        
        # Add custom preload implementation task
        load_tasks.append(self._preload_impl(preloader))
        
        # Concurrently execute all loading tasks
        results = await asyncio.gather(*load_tasks)
        
        # Process resource loading results (exclude the last result, which is _preload_impl's return)
        for resource_id, loaded_resource in results[:-1]:
            self.loaded_resources[resource_id] = loaded_resource
    
    async def _preload_impl(self, preloader: Preloader):
        """
        Optional hook for additional preload logic.
        Subclasses can override this method to add custom preload behavior.
        """
        pass
    
    @abstractmethod
    async def build(self, map_cache: MapCache):
        """
        Build this element into the map.
        Must be implemented by subclasses to define how the element is constructed.
        
        Args:
            map_cache: The map cache instance to build into
        """
        pass

    @classmethod
    def get_default_descriptors(cls) -> Dict[str, ResourceDescriptor]:
        """
        Get the default resource descriptors required by this element type.
        
        This method creates a temporary instance of the class to determine what
        resources would be set up, and returns a copy of those descriptors.
        
        Returns:
            A dictionary of default descriptors that users can modify and use for instantiation
        """
        # Create a temporary instance to extract resource requirements
        temp = cls.__new__(cls)
        temp.name = "temporary_instance"  # Set required name attribute
        temp._resource_descriptors = {}
        temp._resource_types = {}
        temp._setup_resources()
        
        # Return a copy of the descriptors to avoid modifying the originals
        return {k: v.copy() for k, v in temp._resource_descriptors.items()}