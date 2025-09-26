from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from . import views

app_name = "test_app"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.index, name="index"),
    path("models/", views.TestModelListView.as_view(), name="test_model_list_view"),
    path("api/models/time_basic_cache", views.test_basic_time_cache, name="test_basic_time_cache"),
    path("api/models/cron_basic_cache", views.test_basic_cron_cache, name="test_basic_cron_cache"),
    path("api/test/class-methods/", views.test_class_method_cache, name="test_class_method_cache"),
]

# Debug Toolbar URLs in der HAUPTKONFIGURATION einbinden
if settings.DEBUG_TOOLBAR_AVAILABLE:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
