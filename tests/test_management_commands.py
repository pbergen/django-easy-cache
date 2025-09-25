"""Unit tests for management commands"""

import io
from unittest.mock import Mock, patch
from datetime import timedelta

from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils.timezone import localtime

from easy_cache.models import CacheEntry, CacheEventHistory
from easy_cache.management.commands.easy_cache import Command


class TestEasyCacheCommand(TestCase):
    """Test cases for easy_cache management command"""

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
            expires_at=now + timedelta(hours=1),
        )

        self.entry2 = CacheEntry.objects.create(
            cache_key="test_key_2",
            function_name="test.function2",
            cache_backend="redis",
            timeout=7200,
            hit_count=5,
            miss_count=5,
            access_count=10,
            expires_at=now - timedelta(hours=1),  # Expired
        )

        # Create event history
        self.event1 = CacheEventHistory.objects.create(
            event_name="cache_hit",
            event_type=CacheEventHistory.EventType.HIT,
            function_name="test.function1",
            cache_key="test_key_1",
            duration_ms=10,
        )

        self.event2 = CacheEventHistory.objects.create(
            event_name="cache_miss",
            event_type=CacheEventHistory.EventType.MISS,
            function_name="test.function2",
            cache_key="test_key_2",
            duration_ms=150,
        )

    def test_analytics_subcommand_basic(self):
        """Test analytics subcommand basic functionality"""
        out = io.StringIO()
        call_command("easy_cache", "analytics", stdout=out)
        output = out.getvalue()

        self.assertIn("Cache Analytics", output)
        self.assertIn("Total Entries:", output)

    def test_analytics_subcommand_detailed_output(self):
        """Test analytics subcommand with detailed output"""
        out = io.StringIO()
        call_command("easy_cache", "analytics", stdout=out)
        output = out.getvalue()

        # Check for specific statistics
        self.assertIn("Total Entries:", output)

    def test_analytics_with_days_filter(self):
        """Test analytics command with days filter"""
        out = io.StringIO()
        call_command("easy_cache", "analytics", "--days", "1", stdout=out)
        output = out.getvalue()

        self.assertIn("Cache Analytics", output)

    def test_analytics_with_json_format(self):
        """Test analytics command with JSON format"""
        out = io.StringIO()
        call_command("easy_cache", "analytics", "--format", "json", stdout=out)
        output = out.getvalue()

        # Should be valid JSON
        import json

        try:
            data = json.loads(output)
            self.assertIn("total_entries", data)
        except json.JSONDecodeError:
            self.fail("Output is not valid JSON")

    def test_clear_cache_entries_subcommand(self):
        """Test clear --cache-entries subcommand"""
        original_entries = CacheEntry.objects.count()
        self.assertGreater(original_entries, 0)

        out = io.StringIO()
        call_command("easy_cache", "clear", "--cache-entries", stdout=out)
        output = out.getvalue()

        self.assertIn("cache entries successfully deleted", output)

        # Verify cache entries were cleared
        self.assertEqual(CacheEntry.objects.count(), 0)

    def test_clear_event_history_subcommand(self):
        """Test clear --event-history subcommand"""
        original_events = CacheEventHistory.objects.count()
        self.assertGreater(original_events, 0)

        out = io.StringIO()
        call_command("easy_cache", "clear", "--event-history", stdout=out)
        output = out.getvalue()

        self.assertIn("event history entries successfully deleted", output)

        # Verify event history was cleared
        self.assertEqual(CacheEventHistory.objects.count(), 0)

    def test_clear_without_options(self):
        """Test clear command without specific options shows help"""
        out = io.StringIO()
        call_command("easy_cache", "clear", stdout=out)
        output = out.getvalue()

        self.assertIn("Please select an option", output)

    def test_invalid_subcommand(self):
        """Test handling of invalid subcommand"""
        with self.assertRaises(CommandError):
            call_command("easy_cache", "invalid_command")

    def test_command_with_verbosity_levels(self):
        """Test command with different verbosity levels"""
        # Test verbosity 0 (quiet)
        out = io.StringIO()
        call_command("easy_cache", "analytics", verbosity=0, stdout=out)
        quiet_output = out.getvalue()

        # Test verbosity 2 (verbose)
        out = io.StringIO()
        call_command("easy_cache", "analytics", verbosity=2, stdout=out)
        verbose_output = out.getvalue()

        # Both should produce output, but we can't easily test length differences
        self.assertIn("Cache Analytics", quiet_output)
        self.assertIn("Cache Analytics", verbose_output)

    def test_analytics_with_days_range(self):
        """Test analytics command with days range"""
        out = io.StringIO()
        call_command("easy_cache", "analytics", "--days", "1", stdout=out)
        output = out.getvalue()

        self.assertIn("Cache Analytics", output)

    def test_command_with_no_data(self):
        """Test command behavior with no cache data"""
        # Clear all data
        CacheEntry.objects.all().delete()
        CacheEventHistory.objects.all().delete()

        out = io.StringIO()
        call_command("easy_cache", "analytics", stdout=out)
        output = out.getvalue()

        self.assertIn("No cache entries found", output)

    def test_status_subcommand(self):
        """Test status subcommand"""
        out = io.StringIO()
        call_command("easy_cache", "status", stdout=out)
        output = out.getvalue()

        self.assertIn("Easy Cache Status", output)
        self.assertIn("Backend:", output)

    def test_status_with_backend_filter(self):
        """Test status command with backend filter"""
        out = io.StringIO()
        call_command("easy_cache", "status", "--backend", "default", stdout=out)
        output = out.getvalue()

        self.assertIn("Backend: default", output)

    def test_command_direct_instantiation(self):
        """Test direct command instantiation and execution"""
        command = Command()

        # Test that command has required methods
        self.assertTrue(hasattr(command, "handle"))
        self.assertTrue(hasattr(command, "add_arguments"))

        # Test help text
        self.assertIsNotNone(command.help)
        self.assertIn("Easy Cache", command.help)

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

    @patch("easy_cache.management.commands.easy_cache.Command.handle_analytics")
    def test_subcommand_routing(self, mock_handle_analytics):
        """Test that subcommands are routed correctly"""
        call_command("easy_cache", "analytics")
        mock_handle_analytics.assert_called_once()

    def test_output_formatting(self):
        """Test output formatting consistency"""
        out = io.StringIO()
        call_command("easy_cache", "analytics", stdout=out)
        output = out.getvalue()

        # Check for consistent formatting
        lines = output.split("\n")

        # Should have some structured output
        self.assertGreater(len([l for l in lines if l.strip()]), 0)

    def test_command_with_different_formats(self):
        """Test command with different output formats"""
        # Test table format (default)
        out = io.StringIO()
        call_command("easy_cache", "analytics", stdout=out)
        table_output = out.getvalue()
        self.assertIn("Cache Analytics", table_output)

        # Test JSON format
        out = io.StringIO()
        call_command("easy_cache", "analytics", "--format", "json", stdout=out)
        json_output = out.getvalue()

        import json

        try:
            data = json.loads(json_output)
            self.assertIn("total_entries", data)
        except json.JSONDecodeError:
            self.fail("JSON output is not valid")
