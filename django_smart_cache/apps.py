from django.apps import AppConfig
from django.conf import settings
from django.core.checks import Error, register


class DjangoSmartCacheConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'django_smart_cache'
    verbose_name = 'Django Smart Cache'

    def ready(self):
        """Initialize Django Smart Cache when Django starts"""
        # Import signal handlers
        # from . import signals  # noqa

        # Initialize cache analytics if enabled
        # if self._is_analytics_enabled():
            # from .analytics import CacheAnalytics
            # CacheAnalytics.initialize()

        # Setup debug toolbar integration
        if self._is_debug_toolbar_enabled():
            self._setup_debug_toolbar()

        # Initialize real-time features
        if self._is_realtime_enabled():
            self._setup_realtime()

    def _is_analytics_enabled(self) -> bool:
        """Check if cache analytics are enabled"""
        smart_cache_settings = getattr(settings, 'SMART_CACHE', {})
        return smart_cache_settings.get('ANALYTICS_ENABLED', False)

    def _is_debug_toolbar_enabled(self) -> bool:
        """Check if debug toolbar integration is enabled"""
        if 'debug_toolbar' not in settings.INSTALLED_APPS:
            return False

        smart_cache_settings = getattr(settings, 'SMART_CACHE', {})
        return smart_cache_settings.get('DEBUG_TOOLBAR_INTEGRATION', False)

    def _is_realtime_enabled(self) -> bool:
        """Check if real-time features are enabled"""
        smart_cache_settings = getattr(settings, 'SMART_CACHE', {})
        return smart_cache_settings.get('REALTIME', {}).get('ENABLED', False)

    def _setup_debug_toolbar(self):
        """Setup debug toolbar integration"""
        try:
            from debug_toolbar import settings as toolbar_settings
            from .panels import SmartCacheDebugPanel

            # Add our panel to debug toolbar
            if SmartCacheDebugPanel not in toolbar_settings.PANELS_DEFAULTS:
                toolbar_settings.PANELS_DEFAULTS.append(
                    'django_smart_cache.panels.SmartCacheDebugPanel'
                )
        except ImportError:
            pass

    def _setup_realtime(self):
        """Setup real-time features"""
        try:
            # Verify channels is installed
            import channels  # noqa

            # Register WebSocket routing
            from .routing import websocket_urlpatterns

        except ImportError:
            if settings.DEBUG:
                print("Warning: Real-time features enabled but 'channels' not installed")


@register()
def check_smart_cache_settings(app_configs, **kwargs):
    """Django system check for Smart Cache configuration"""
    errors = []

    smart_cache_settings = getattr(settings, 'SMART_CACHE', {})

    # Check if caches are configured
    if not hasattr(settings, 'CACHES') or not settings.CACHES:
        errors.append(
            Error(
                'No cache backends configured',
                hint='Configure at least one cache backend in settings.CACHES',
                id='django_smart_cache.E001',
            )
        )

    # Check default cache backend
    default_backend = smart_cache_settings.get('DEFAULT_BACKEND', 'default')
    if default_backend not in settings.CACHES:
        errors.append(
            Error(
                f'Smart Cache default backend "{default_backend}" not found in CACHES',
                hint=f'Add "{default_backend}" to settings.CACHES or change SMART_CACHE.DEFAULT_BACKEND',
                id='django_smart_cache.E002',
            )
        )

    # Check real-time configuration
    realtime_config = smart_cache_settings.get('REALTIME', {})
    if realtime_config.get('ENABLED', False):
        if 'channels' not in settings.INSTALLED_APPS:
            errors.append(
                Error(
                    'Real-time features enabled but channels not in INSTALLED_APPS',
                    hint='Add "channels" to INSTALLED_APPS or disable real-time features',
                    id='django_smart_cache.E003',
                )
            )

    return errors
