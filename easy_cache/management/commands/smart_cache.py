from datetime import timedelta

from django.core.management.base import BaseCommand
from django.core.cache import caches, cache
from django.conf import settings
from django.db import models
import json

from django.utils import timezone
from easy_cache.models import CacheEntry, CacheEventHistory


class Command(BaseCommand):
    help = "Easy Cache management operations"

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest="action", help="Available actions")

        # Status command
        status_parser = subparsers.add_parser("status", help="Show cache status")
        status_parser.add_argument("--backend", help="Specific cache backend to check")

        # Clear command
        clear_parser = subparsers.add_parser("clear", help="Clear cache entries")
        clear_parser.add_argument(
            "--cache-entries",
            action="store_true",
            help="Clear only CacheEntry database records and their corresponding cache keys",
        )
        clear_parser.add_argument(
            "--event-history", action="store_true", help="Clear only CacheEventHistory database records"
        )

        # Analytics command
        analytics_parser = subparsers.add_parser("analytics", help="Show cache analytics")
        analytics_parser.add_argument("--days", type=int, default=7, help="Number of days to analyze")
        analytics_parser.add_argument("--format", choices=["table", "json"], default="table", help="Output format")

    def handle(self, *args, **options):
        action = options["action"]

        if action == "status":
            self.handle_status(**options)
        elif action == "clear":
            self.handle_clear(**options)
        elif action == "analytics":
            self.handle_analytics(**options)
        else:
            self.print_help("manage.py", "easy_cache")

    def handle_status(self, **options):
        """Show cache status"""
        backend_name = options.get("backend")

        if backend_name:
            backends = [backend_name]
        else:
            backends = list(settings.CACHES.keys())

        self.stdout.write(self.style.SUCCESS(f"Easy Cache Status - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"))

        for backend in backends:
            try:
                cache_backend = caches[backend]
                self.stdout.write(f"\nBackend: {backend}")
                self.stdout.write(f"  Status: Connected")
                self.stdout.write(f"  Type: {cache_backend.__class__.__name__}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Backend {backend}: Error - {str(e)}"))

    def handle_clear(self, **options):
        """Clear cache entries"""
        clear_cache_entries = options.get("cache_entries", False)
        clear_event_history = options.get("event_history", False)

        # Wenn keine spezifische Option gewählt wurde, zeige Hilfe
        if not any([clear_cache_entries, clear_event_history]):
            self.stdout.write(self.style.WARNING("Please select an option: --all, --cache-entries, or --event-history"))
            return

        if clear_cache_entries:
            self._clear_cache_entries()
        elif clear_event_history:
            self._clear_event_history()

    def _clear_cache_entries(self):
        """Clear CacheEntry objects and their corresponding cache keys"""
        cache_entries = CacheEntry.objects.all()
        total_entries = cache_entries.count()

        if total_entries > 0:
            self.stdout.write(f"Deleting {total_entries} cache entries...")

            cleared_count = 0
            for entry in cache_entries:
                try:
                    cache_backend = caches[entry.cache_backend]
                    cache_backend.delete(entry.cache_key)
                    cleared_count += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Error deleting cache key '{entry.cache_key}': {str(e)}"))

            cache_entries.delete()

            self.stdout.write(
                self.style.SUCCESS(f"{cleared_count} of {total_entries} cache entries successfully deleted")
            )
        else:
            self.stdout.write(self.style.SUCCESS("No cache entries found to delete"))

    def _clear_event_history(self):
        """Clear CacheEventHistory objects"""
        event_entries = CacheEventHistory.objects.all()
        total_events = event_entries.count()

        if total_events > 0:
            self.stdout.write(f"Delete {total_events} event history entries...")
            event_entries.delete()
            self.stdout.write(self.style.SUCCESS(f"{total_events} event history entries successfully deleted"))
        else:
            self.stdout.write(self.style.SUCCESS("No event history entries found to delete"))

    def handle_analytics(self, **options):
        """Show cache analytics"""
        days = options.get("days", 7)
        format_type = options.get("format", "table")

        try:
            from easy_cache.models import CacheEntry, CacheEventHistory

            # Get cache entries from last N days
            cutoff_date = timezone.now() - timedelta(days=days)
            entries = CacheEntry.objects.filter(created_at__gte=cutoff_date)

            if format_type == "json":
                data = {
                    "total_entries": entries.count(),
                    "average_hit_rate": entries.aggregate(
                        avg_hit_rate=models.Avg(
                            models.Case(
                                models.When(
                                    hit_count__gt=0,
                                    then=models.F("hit_count") * 100 / (models.F("hit_count") + models.F("miss_count")),
                                ),
                                default=0,
                                output_field=models.FloatField(),
                            )
                        )
                    )["avg_hit_rate"]
                    or 0,
                }
                self.stdout.write(json.dumps(data, indent=2))
            else:
                self.stdout.write(f"\nCache Analytics (last {days} days)")
                self.stdout.write("-" * 40)

                total_entries = entries.count()
                self.stdout.write(f"Total Entries: {total_entries}")

                if total_entries > 0:
                    analytics_data = entries.aggregate(
                        total_hits=models.Sum("hit_count"), total_misses=models.Sum("miss_count")
                    )

                    total_hits = analytics_data.get("total_hits") or 0
                    total_misses = analytics_data.get("total_misses") or 0
                    total_accesses = total_hits + total_misses

                    avg_hit_rate = (total_hits / total_accesses * 100) if total_accesses > 0 else 0

                    self.stdout.write(f"Total Hits: {total_hits}")
                    self.stdout.write(f"Total Misses: {total_misses}")
                    self.stdout.write(f"Average Hit Rate: {avg_hit_rate:.1f}%")
                else:
                    self.stdout.write("No cache entries found")

        except ImportError:
            self.stdout.write(self.style.ERROR("Analytics models not available"))
