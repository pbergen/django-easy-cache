import time

from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.generic import ListView

from easy_cache import easy_cache
from .models import TestModel


def index(request):
    """Simple index view."""
    return render(request, "test_app/index.html", {"title": "Django Easy Cache Test Project"})


class DataProcessor:
    """Beispiel-Klasse mit Cache-Dekoratoren auf Methoden"""

    def __init__(self, user_id: int):
        self.user_id = user_id

    @easy_cache.time_based(
        invalidate_at="02:00",
    )
    def get_user_stats(self):
        """Benutzer-Statistiken täglich um 2 Uhr invalidieren"""
        # Simuliere DB-Abfrage
        time.sleep(0.2)
        return {
            "user_id": self.user_id,
            "stats": {"views": 1234, "clicks": 567},
            "calculated_at": timezone.now().isoformat(),
        }

    def get_user_stats_simple(self):
        """Einfache Methode OHNE Cache-Dekorator zum Testen"""
        time.sleep(0.2)
        return {
            "user_id": self.user_id,
            "stats": {"views": 1234, "clicks": 567},
            "calculated_at": timezone.now().isoformat(),
        }

    @easy_cache.cron_based(cron_expression="*/1 * * * *")
    def get_live_metrics(self, metric_type: str):
        """Live-Metriken alle 15 Minuten aktualisieren"""
        time.sleep(0.3)
        return {
            "user_id": self.user_id,
            "metric_type": metric_type,
            "value": time.time(),
            "updated_at": timezone.now().isoformat(),
        }

    @easy_cache.time_based(
        invalidate_at="00:00",
    )
    def generate_daily_report(self, date_str: str):
        """Tagesbericht - täglich um Mitternacht invalidieren"""
        time.sleep(0.5)  # Schwere Berechnung simulieren
        return {
            "user_id": self.user_id,
            "date": date_str,
            "report_data": f"Report for {date_str}",
            "generated_at": timezone.now().isoformat(),
        }


@easy_cache.time_based(
    invalidate_at="22:40",
)
def test_basic_time_cache(request):
    """Test der Grundfunktionalität - Ihr Use-Case!"""
    # Simuliere teure Operation
    time.sleep(0.1)

    current_time = timezone.now()

    return JsonResponse(
        {
            "message": "Cache Test erfolgreich!",
            "timestamp": current_time.isoformat(),
            "cache_status": "MISS (first call)",
            "test": "basic_time_cache",
        }
    )


@easy_cache.cron_based(cron_expression="*/5 * * * *")
def test_basic_cron_cache(request):
    """Test der Grundfunktionalität - Ihr Use-Case!"""
    # Simuliere teure Operation
    time.sleep(0.1)

    current_time = timezone.now()

    return JsonResponse(
        {
            "message": "Cache Test erfolgreich!",
            "timestamp": current_time.isoformat(),
            "cache_status": "MISS (first call)",
            "test": "basic_cron_cache",
        }
    )


# Test für Klassen-Methoden
def test_class_method_cache(request):
    """Test Cache-Dekoratoren auf Klassen-Methoden"""
    user_id = int(request.GET.get("user_id", 1))

    # DataProcessor-Instanz erstellen
    processor = DataProcessor(user_id)

    # Verschiedene Methoden testen
    start_time = time.time()

    # Test 1: get_user_stats (Zeit-basiert, täglich um 02:00)
    stats = processor.get_user_stats()
    stats_time = time.time() - start_time

    # Test 2: get_live_metrics (Cron-basiert, alle 15 Min)
    start_time = time.time()
    metrics = processor.get_live_metrics("page_views")
    metrics_time = time.time() - start_time

    # Test 3: generate_daily_report (Zeit-basiert, täglich um 00:00)
    start_time = time.time()
    report = processor.generate_daily_report("2025-09-03")
    report_time = time.time() - start_time

    return JsonResponse(
        {
            "message": "Class method caching test successful!",
            "user_id": user_id,
            "tests": {
                "user_stats": {
                    "result": stats,
                    "execution_time": round(stats_time, 3),
                    "cache_type": "time_based (daily 02:00)",
                },
                "live_metrics": {
                    "result": metrics,
                    "execution_time": round(metrics_time, 3),
                    "cache_type": "cron_based (* * * * *)",
                },
                "daily_report": {
                    "result": report,
                    "execution_time": round(report_time, 3),
                    "cache_type": "time_based (daily 00:00)",
                },
            },
            "note": "Subsequent calls should be much faster due to caching!",
        }
    )


class TestModelListView(ListView):
    """Class-based view for testing easy_cache with CBVs."""

    model = TestModel
    template_name = "test_app/test_model_list.html"
    context_object_name = "models"
    paginate_by = 10

    @easy_cache.cron_based(cron_expression="*/5 * * * *")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
