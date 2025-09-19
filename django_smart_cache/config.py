"""Django Smart Cache Configuration System"""

import copy
import threading
import logging
from typing import Any
from django.conf import settings
from django.core.cache import caches
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class SmartCacheConfig:
    """Centralized configuration management for Django Smart Cache"""

    _instance = None
    _lock = threading.Lock()

    # Default configuration
    DEFAULT_CONFIG = {
        "DEFAULT_BACKEND": "default",
        "KEY_PREFIX": "smart_cache",
        # Value length for each key
        "MAX_VALUE_LENGTH": 100,
        # Analytics & Monitoring
        "DEBUG_TOOLBAR_INTEGRATION": True,
        # Logging / TRACKING / ANALYTICS
        "TRACKING": {
            "TRACK_CACHE_HITS": True,
            "TRACK_CACHE_MISSES": True,
            "TRACK_PERFORMANCE": True,
        },
        "EVENTS": {
            "EVENT_CACHE_HITS": True,
            "EVENT_CACHE_MISSES": True,
            "EVENT_CACHE_ERRORS": True,
        },
    }

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._config = {}
                    cls._instance._cache_backends = {}
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._load_config()
            self._initialized = True

    def _load_config(self):
        """Load configuration from Django settings"""
        smart_cache_settings = getattr(settings, "SMART_CACHE", {})

        # Merge with defaults
        self._config = copy.deepcopy(self.DEFAULT_CONFIG)
        self._deep_update(base_dict=self._config, update_dict=smart_cache_settings)

        # Validate configuration
        self._validate_config()

        # Initialize cache backends
        self._initialize_cache_backends()

    def _deep_update(self, *, base_dict: dict[str, Any], update_dict: dict[str, Any]) -> None:
        """Deep update dictionary"""
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                self._deep_update(base_dict=base_dict[key], update_dict=value)
            else:
                base_dict[key] = value

    def _validate_config(self):
        """Validate configuration settings with comprehensive checks"""
        # Validate cache backend exists
        default_backend = self._config["DEFAULT_BACKEND"]
        if default_backend not in settings.CACHES:
            raise ImproperlyConfigured(f"Smart Cache default backend '{default_backend}' not found in CACHES setting")

    def _initialize_cache_backends(self):
        """Initialize and validate cache backends"""
        for backend_name in settings.CACHES.keys():
            try:
                backend = caches[backend_name]
                self._cache_backends[backend_name] = backend
            except Exception as e:
                if backend_name == self._config["DEFAULT_BACKEND"]:
                    raise ImproperlyConfigured(f"Cannot initialize default cache backend '{backend_name}': {e}")
                else:
                    logger.warning(f"Failed to initialize cache backend '{backend_name}': {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        with self._lock:
            keys = key.split(".")
            config = self._config

            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                elif not isinstance(config[k], dict):
                    raise ValueError(f"Cannot set '{key}': intermediate key '{k}' is not a dictionary")
                config = config[k]

            config[keys[-1]] = value

    def is_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled"""
        return self.get(feature, False)

    def get_cache_backend(self, name: str | None = None) -> Any:
        """Get cache backend instance"""
        backend_name = name or self._config["DEFAULT_BACKEND"]
        return self._cache_backends.get(backend_name)

    def get_all_cache_backends(self) -> dict[str, Any]:
        """Get all available cache backends"""
        return self._cache_backends.copy()

    def get_tracking_config(self) -> dict[str, Any]:
        """Get logging configuration"""
        return self._config["TRACKING"].copy()

    def should_track(self, event_type: str) -> bool:
        """Check if event should be logged"""
        logging_config = self.get_tracking_config()
        return logging_config.get(f"TRACK_{event_type.upper()}", False)

    def get_event_config(self) -> dict[str, Any]:
        """Get logging configuration"""
        return self._config["EVENTS"].copy()

    def should_log_event(self, event_type: str) -> bool:
        """Check if event should be logged"""
        logging_config = self.get_event_config()
        return logging_config.get(f"EVENT_{event_type.upper()}", False)

    def reload_config(self):
        """Reload configuration from Django settings"""
        with self._lock:
            # Backup current state
            old_config = copy.deepcopy(self._config)
            old_backends = self._cache_backends.copy()
            try:
                self._cache_backends.clear()
                self._load_config()
            except Exception as e:
                # Restore old state on failure
                self._config = old_config
                self._cache_backends = old_backends
                raise

    def get_full_config(self) -> dict[str, Any]:
        """Get full configuration (for debugging)"""
        return self._config.copy()


# Global configuration instance
config = SmartCacheConfig()


def get_config() -> SmartCacheConfig:
    """Get the global configuration instance"""
    return config


def reload_config():
    """Reload configuration from Django settings"""
    config.reload_config()
