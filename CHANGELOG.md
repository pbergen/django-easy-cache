# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.1.0 
-------------------

**New features**

* Time-based cache invalidation with timezone support
* Cron-based cache invalidation with flexible scheduling
* Database analytics and performance tracking
* Django Admin integration for cache entries and event history
* Management commands for cache status, analytics, and clearing
* `@easy_cache.time_based()` decorator for daily invalidation at specific times
* `@easy_cache.cron_based()` decorator for flexible cron-based invalidation
* Automatic cache key generation with collision avoidance
* Database models for cache analytics (CacheEntry, CacheEventHistory)
* Management commands: `status`, `analytics`, `clear`
* Django Admin interface at `/admin/django_easy_cache/`

**Bug fixes**

* Fix package name configuration for Sphinx documentation
* Resolve CI database conflicts and modernize database configuration
* Allow CI to run pre-commit on protected branches while enforcing local branch restrictions

**Technical improvements**

* Built on Django's cache framework for backend compatibility
* Support for Redis, Memcached, Database, and Local Memory cache backends
* Atomic database operations for analytics tracking
* Thread-safe cache operations
* Comprehensive cache key validation
* Type hints throughout the codebase
* Modular architecture with separated concerns
* Robust error handling with graceful degradation
* Comprehensive test suite with pytest
* Replace pre-commit branch restrictions with GitHub rulesets
