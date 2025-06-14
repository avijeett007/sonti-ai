"""Provider registry for dynamic provider loading and management"""

import importlib
import inspect
import logging
from typing import Dict, Type, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from .base import (
    BaseProvider, BaseLLMProvider, BaseSTTProvider, BaseTTSProvider,
    ProviderType, ProviderCapability, ProviderError
)


@dataclass
class ProviderInfo:
    """Information about a registered provider"""
    name: str
    provider_type: ProviderType
    provider_class: Type[BaseProvider]
    supported_models: List[str] = field(default_factory=list)
    capabilities: List[ProviderCapability] = field(default_factory=list)
    required_config: List[str] = field(default_factory=list)
    optional_config: List[str] = field(default_factory=list)
    description: str = ""
    version: str = "1.0.0"


class ProviderRegistry:
    """Registry for managing AI providers"""
    
    _instance = None
    _providers: Dict[Tuple[str, ProviderType], ProviderInfo] = {}
    _logger = logging.getLogger("knova.providers.registry")
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._load_builtin_providers()
    
    @classmethod
    def get_instance(cls) -> "ProviderRegistry":
        """Get singleton instance of the registry"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def register_provider(
        self,
        name: str,
        provider_type: ProviderType,
        provider_class: Type[BaseProvider],
        info: Optional[ProviderInfo] = None
    ) -> None:
        """Register a new provider"""
        key = (name.lower(), provider_type)
        
        if key in self._providers:
            self._logger.warning(f"Provider {name} ({provider_type.value}) already registered, overwriting")
        
        if info is None:
            # Extract info from class if not provided
            info = ProviderInfo(
                name=name,
                provider_type=provider_type,
                provider_class=provider_class
            )
            
            # Try to extract metadata from class
            if hasattr(provider_class, 'SUPPORTED_MODELS'):
                info.supported_models = provider_class.SUPPORTED_MODELS
            if hasattr(provider_class, 'CAPABILITIES'):
                info.capabilities = provider_class.CAPABILITIES
            if hasattr(provider_class, 'REQUIRED_CONFIG'):
                info.required_config = provider_class.REQUIRED_CONFIG
            if hasattr(provider_class, 'OPTIONAL_CONFIG'):
                info.optional_config = provider_class.OPTIONAL_CONFIG
            if hasattr(provider_class, '__doc__') and provider_class.__doc__:
                info.description = provider_class.__doc__.strip()
        
        self._providers[key] = info
        self._logger.info(f"Registered provider: {name} ({provider_type.value})")
    
    def get_provider_class(
        self,
        name: str,
        provider_type: ProviderType
    ) -> Type[BaseProvider]:
        """Get provider class by name and type"""
        key = (name.lower(), provider_type)
        
        if key not in self._providers:
            raise ProviderError(
                f"Provider {name} ({provider_type.value}) not found in registry",
                name
            )
        
        return self._providers[key].provider_class
    
    def get_provider_info(
        self,
        name: str,
        provider_type: ProviderType
    ) -> ProviderInfo:
        """Get provider information"""
        key = (name.lower(), provider_type)
        
        if key not in self._providers:
            raise ProviderError(
                f"Provider {name} ({provider_type.value}) not found in registry",
                name
            )
        
        return self._providers[key]
    
    def create_provider(
        self,
        name: str,
        provider_type: ProviderType,
        **config
    ) -> BaseProvider:
        """Create a provider instance"""
        provider_class = self.get_provider_class(name, provider_type)
        provider_info = self.get_provider_info(name, provider_type)
        
        # Validate required config
        missing_config = []
        for required in provider_info.required_config:
            if required not in config:
                missing_config.append(required)
        
        if missing_config:
            raise ProviderError(
                f"Missing required configuration for {name}: {', '.join(missing_config)}",
                name
            )
        
        # Create instance
        try:
            # Check if we need to pass specific parameters
            init_signature = inspect.signature(provider_class.__init__)
            init_params = list(init_signature.parameters.keys())[1:]  # Skip 'self'
            
            # Build kwargs based on what the provider expects
            provider_kwargs = {}
            for param in init_params:
                if param in config:
                    provider_kwargs[param] = config[param]
                elif param == "provider_name":
                    provider_kwargs[param] = name
                elif param == "api_key" and "api_key" in config:
                    provider_kwargs[param] = config["api_key"]
            
            # Add any extra config that might be used
            for key, value in config.items():
                if key not in provider_kwargs:
                    provider_kwargs[key] = value
            
            return provider_class(**provider_kwargs)
        except Exception as e:
            raise ProviderError(
                f"Failed to create provider {name}: {e}",
                name
            )
    
    def list_providers(
        self,
        provider_type: Optional[ProviderType] = None
    ) -> List[ProviderInfo]:
        """List all registered providers"""
        providers = []
        
        for (name, ptype), info in self._providers.items():
            if provider_type is None or ptype == provider_type:
                providers.append(info)
        
        return providers
    
    def load_custom_providers(self, directory: str) -> None:
        """Load custom providers from a directory"""
        provider_dir = Path(directory)
        
        if not provider_dir.exists() or not provider_dir.is_dir():
            self._logger.warning(f"Provider directory {directory} does not exist")
            return
        
        # Look for Python files in the directory
        for file_path in provider_dir.glob("*.py"):
            if file_path.name.startswith("_"):
                continue
            
            module_name = file_path.stem
            
            try:
                # Import the module
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Look for provider classes
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseProvider) and 
                        obj not in [BaseProvider, BaseLLMProvider, BaseSTTProvider, BaseTTSProvider]):
                        
                        # Determine provider type
                        if issubclass(obj, BaseLLMProvider):
                            provider_type = ProviderType.LLM
                        elif issubclass(obj, BaseSTTProvider):
                            provider_type = ProviderType.STT
                        elif issubclass(obj, BaseTTSProvider):
                            provider_type = ProviderType.TTS
                        else:
                            continue
                        
                        # Register the provider
                        provider_name = getattr(obj, 'PROVIDER_NAME', name.lower())
                        self.register_provider(provider_name, provider_type, obj)
                        
            except Exception as e:
                self._logger.error(f"Failed to load providers from {file_path}: {e}")
    
    def _load_builtin_providers(self) -> None:
        """Load built-in providers"""
        # This will be called to load the standard providers
        # We'll implement this after creating the actual provider implementations
        pass
    
    def validate_provider_config(
        self,
        name: str,
        provider_type: ProviderType,
        config: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Validate provider configuration"""
        try:
            info = self.get_provider_info(name, provider_type)
            errors = []
            
            # Check required fields
            for required in info.required_config:
                if required not in config:
                    errors.append(f"Missing required field: {required}")
            
            # Check model support if applicable
            if info.supported_models and "model" in config:
                if config["model"] not in info.supported_models:
                    errors.append(
                        f"Unsupported model: {config['model']}. "
                        f"Supported models: {', '.join(info.supported_models)}"
                    )
            
            return len(errors) == 0, errors
            
        except ProviderError:
            return False, [f"Unknown provider: {name} ({provider_type.value})"]


# Convenience functions
def register_provider(
    name: str,
    provider_type: ProviderType,
    provider_class: Type[BaseProvider],
    info: Optional[ProviderInfo] = None
) -> None:
    """Register a provider with the global registry"""
    registry = ProviderRegistry.get_instance()
    registry.register_provider(name, provider_type, provider_class, info)


def create_provider(
    name: str,
    provider_type: ProviderType,
    **config
) -> BaseProvider:
    """Create a provider using the global registry"""
    registry = ProviderRegistry.get_instance()
    return registry.create_provider(name, provider_type, **config)


def list_providers(provider_type: Optional[ProviderType] = None) -> List[ProviderInfo]:
    """List providers from the global registry"""
    registry = ProviderRegistry.get_instance()
    return registry.list_providers(provider_type)