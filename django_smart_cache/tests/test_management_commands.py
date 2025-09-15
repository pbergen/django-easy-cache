"""Unit tests for management commands"""
import io
from unittest.mock import Mock, patch, call
from datetime import datetime, timedelta

from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils.timezone import localtime

from django_smart_cache.models import CacheEntry, CacheEventHistory
from django_smart_cache.management.commands.smart_cache import Command


class TestSmartCacheCommand(TestCase):
    """Test cases for smart_cache management command"""

    def setUp(self):
        """Set up test fixtures"""
        # Clear database
        CacheEntry.objects.all().delete()
        CacheEventHistory.objects.all().delete()

        # Create test data
        self.create_test_data()

    def create_test_data(self):
        """Create test cache entries and events"""
        now = localtime()

        # Create cache entries
        self.entry1 = CacheEntry.objects.create(
            cache_key="test_key_1",
            function_name="test.function1",
            cache_backend="default",
            timeout=3600,
            hit_count=10,
            miss_count=2,
            access_count=12,
            expires_at=now + timedelta(hours=1)
        )

        self.entry2 = CacheEntry.objects.create(
            cache_key="test_key_2",
            function_name="test.function2",
            cache_backend="redis",
            timeout=7200,
            hit_count=5,
            miss_count=5,
            access_count=10,
            expires_at=now - timedelta(hours=1)  # Expired
        )

        # Create event history
        self.event1 = CacheEventHistory.objects.create(
            event_name="cache_hit",
            event_type=CacheEventHistory.EventType.HIT,
            function_name="test.function1",
            cache_key="test_key_1",
            duration_ms=10
        )

        self.event2 = CacheEventHistory.objects.create(
            event_name="cache_miss",
            event_type=CacheEventHistory.EventType.MISS,
            function_name="test.function2",
            cache_key="test_key_2",
            duration_ms=150
        )

    def test_command_help(self):
        """Test command help output"""
        out = io.StringIO()
        call_command('smart_cache', '--help', stdout=out)
        help_output = out.getvalue()

        self.assertIn('Smart Cache management command', help_output)
        self.assertIn('--stats', help_output)
        self.assertIn('--clear-expired', help_output)

    def test_stats_subcommand_basic(self):
        """Test stats subcommand basic functionality"""
        out = io.StringIO()
        call_command('smart_cache', 'stats', stdout=out)
        output = out.getvalue()

        self.assertIn('Cache Statistics', output)
        self.assertIn('Total Cache Entries:', output)
        self.assertIn('Total Events:', output)

    def test_stats_subcommand_detailed_output(self):
        """Test stats subcommand with detailed output"""
        out = io.StringIO()
        call_command('smart_cache', 'stats', stdout=out)
        output = out.getvalue()

        # Check for specific statistics
        self.assertIn('2', output)  # Total entries
        self.assertIn('2', output)  # Total events

        # Check for function-specific stats
        self.assertIn('test.function1', output)
        self.assertIn('test.function2', output)

    def test_stats_with_function_filter(self):
        """Test stats command with function name filter"""
        out = io.StringIO()
        call_command('smart_cache', 'stats', '--function', 'test.function1', stdout=out)
        output = out.getvalue()

        self.assertIn('test.function1', output)
        self.assertNotIn('test.function2', output)

    def test_stats_with_backend_filter(self):
        """Test stats command with backend filter"""
        out = io.StringIO()
        call_command('smart_cache', 'stats', '--backend', 'default', stdout=out)
        output = out.getvalue()

        # Should include entries for default backend
        self.assertIn('default', output)

    def test_clear_expired_subcommand(self):
        """Test clear-expired subcommand"""
        # Verify we have expired entries
        expired_count = CacheEntry.objects.filter(
            expires_at__lt=localtime()
        ).count()
        self.assertGreater(expired_count, 0)

        out = io.StringIO()
        call_command('smart_cache', 'clear-expired', stdout=out)
        output = out.getvalue()

        self.assertIn('Cleared', output)
        self.assertIn('expired', output)

        # Verify expired entries were removed
        remaining_expired = CacheEntry.objects.filter(
            expires_at__lt=localtime()
        ).count()
        self.assertEqual(remaining_expired, 0)

    def test_clear_expired_dry_run(self):
        """Test clear-expired with dry-run option"""
        original_count = CacheEntry.objects.count()

        out = io.StringIO()
        call_command('smart_cache', 'clear-expired', '--dry-run', stdout=out)
        output = out.getvalue()

        self.assertIn('Would clear', output)
        self.assertIn('expired', output)

        # Verify no entries were actually removed
        self.assertEqual(CacheEntry.objects.count(), original_count)

    def test_clear_all_subcommand(self):
        """Test clear-all subcommand"""
        original_entries = CacheEntry.objects.count()
        original_events = CacheEventHistory.objects.count()

        self.assertGreater(original_entries, 0)
        self.assertGreater(original_events, 0)

        out = io.StringIO()
        call_command('smart_cache', 'clear-all', '--force', stdout=out)
        output = out.getvalue()

        self.assertIn('Cleared all', output)

        # Verify all data was cleared
        self.assertEqual(CacheEntry.objects.count(), 0)
        self.assertEqual(CacheEventHistory.objects.count(), 0)

    def test_clear_all_requires_force(self):
        """Test that clear-all requires --force flag"""
        with self.assertRaises(CommandError):
            call_command('smart_cache', 'clear-all')

    def test_clear_all_with_confirmation_prompt(self):
        """Test clear-all with user confirmation"""
        with patch('builtins.input', return_value='yes'):
            out = io.StringIO()
            call_command('smart_cache', 'clear-all', stdout=out)
            output = out.getvalue()

            self.assertIn('Cleared all', output)

    def test_clear_all_with_negative_confirmation(self):
        """Test clear-all with user declining confirmation"""
        original_count = CacheEntry.objects.count()

        with patch('builtins.input', return_value='no'):
            out = io.StringIO()
            call_command('smart_cache', 'clear-all', stdout=out)
            output = out.getvalue()

            self.assertIn('Operation cancelled', output)
            self.assertEqual(CacheEntry.objects.count(), original_count)

    def test_export_subcommand(self):
        """Test export subcommand"""
        out = io.StringIO()
        call_command('smart_cache', 'export', stdout=out)
        output = out.getvalue()

        # Should contain JSON data
        self.assertIn('{', output)
        self.assertIn('}', output)
        self.assertIn('cache_entries', output)
        self.assertIn('events', output)

    def test_export_with_function_filter(self):
        """Test export with function filter"""
        out = io.StringIO()
        call_command('smart_cache', 'export', '--function', 'test.function1', stdout=out)
        output = out.getvalue()

        self.assertIn('test.function1', output)
        self.assertNotIn('test.function2', output)

    def test_export_format_json(self):
        """Test export in JSON format"""
        out = io.StringIO()
        call_command('smart_cache', 'export', '--format', 'json', stdout=out)
        output = out.getvalue()

        import json
        try:
            data = json.loads(output)
            self.assertIn('cache_entries', data)
            self.assertIn('events', data)
        except json.JSONDecodeError:
            self.fail("Output is not valid JSON")

    def test_export_format_csv(self):
        """Test export in CSV format"""
        out = io.StringIO()
        call_command('smart_cache', 'export', '--format', 'csv', stdout=out)
        output = out.getvalue()

        # Should contain CSV headers
        self.assertIn('cache_key', output)
        self.assertIn('function_name', output)
        self.assertIn('hit_count', output)

    def test_invalid_subcommand(self):
        """Test handling of invalid subcommand"""
        with self.assertRaises(CommandError):
            call_command('smart_cache', 'invalid_command')

    def test_command_with_verbosity_levels(self):
        """Test command with different verbosity levels"""
        # Test verbosity 0 (quiet)
        out = io.StringIO()
        call_command('smart_cache', 'stats', verbosity=0, stdout=out)
        quiet_output = out.getvalue()

        # Test verbosity 2 (verbose)
        out = io.StringIO()
        call_command('smart_cache', 'stats', verbosity=2, stdout=out)
        verbose_output = out.getvalue()

        self.assertLess(len(quiet_output), len(verbose_output))

    def test_stats_with_date_range(self):
        """Test stats command with date range filter"""
        yesterday = localtime() - timedelta(days=1)
        tomorrow = localtime() + timedelta(days=1)

        out = io.StringIO()
        call_command(
            'smart_cache', 'stats',
            '--since', yesterday.strftime('%Y-%m-%d'),
            '--until', tomorrow.strftime('%Y-%m-%d'),
            stdout=out
        )
        output = out.getvalue()

        self.assertIn('Cache Statistics', output)

    def test_command_error_handling(self):
        """Test command error handling"""
        # Test with invalid date format
        with self.assertRaises(CommandError):
            call_command('smart_cache', 'stats', '--since', 'invalid-date')

    def test_performance_stats_calculation(self):
        """Test performance statistics calculation"""
        out = io.StringIO()
        call_command('smart_cache', 'stats', '--performance', stdout=out)
        output = out.getvalue()

        self.assertIn('Performance Statistics', output)
        self.assertIn('Average Duration', output)

    def test_hit_rate_calculation_in_stats(self):
        """Test hit rate calculation in stats output"""
        out = io.StringIO()
        call_command('smart_cache', 'stats', stdout=out)
        output = out.getvalue()

        # Should show hit rates for functions
        self.assertIn('%', output)  # Hit rate percentage

    def test_command_with_no_data(self):
        """Test command behavior with no cache data"""
        # Clear all data
        CacheEntry.objects.all().delete()
        CacheEventHistory.objects.all().delete()

        out = io.StringIO()
        call_command('smart_cache', 'stats', stdout=out)
        output = out.getvalue()

        self.assertIn('No cache entries', output)

    def test_clear_by_function_pattern(self):
        """Test clearing entries by function pattern"""
        out = io.StringIO()
        call_command(
            'smart_cache', 'clear',
            '--function-pattern', 'test.function1',
            '--force',
            stdout=out
        )
        output = out.getvalue()

        self.assertIn('Cleared', output)

        # Verify only matching entries were cleared
        remaining = CacheEntry.objects.filter(
            function_name__contains='test.function1'
        ).count()
        self.assertEqual(remaining, 0)

    def test_command_direct_instantiation(self):
        """Test direct command instantiation and execution"""
        command = Command()

        # Test that command has required methods
        self.assertTrue(hasattr(command, 'handle'))
        self.assertTrue(hasattr(command, 'add_arguments'))

        # Test help text
        self.assertIsNotNone(command.help)
        self.assertIn('Smart Cache', command.help)

    def test_command_argument_parsing(self):
        """Test command argument parsing"""
        command = Command()

        # Create a mock parser to test add_arguments
        parser = Mock()
        subparsers = Mock()
        parser.add_subparsers.return_value = subparsers

        # Test that add_arguments doesn't raise errors
        try:
            command.add_arguments(parser)
        except Exception as e:
            self.fail(f"add_arguments raised an exception: {e}")

    @patch('django_smart_cache.management.commands.smart_cache.Command.handle_stats')
    def test_subcommand_routing(self, mock_handle_stats):
        """Test that subcommands are routed correctly"""
        call_command('smart_cache', 'stats')
        mock_handle_stats.assert_called_once()

    def test_output_formatting(self):
        """Test output formatting consistency"""
        out = io.StringIO()
        call_command('smart_cache', 'stats', stdout=out)
        output = out.getvalue()

        # Check for consistent formatting
        lines = output.split('\n')

        # Should have headers and separators
        has_headers = any('=' in line for line in lines)
        self.assertTrue(has_headers)

    def test_command_with_color_output(self):
        """Test command with colored output support"""
        out = io.StringIO()
        call_command('smart_cache', 'stats', '--color', stdout=out)
        output = out.getvalue()

        # Should still produce valid output even if colors aren't visible in test
        self.assertIn('Cache Statistics', output)
