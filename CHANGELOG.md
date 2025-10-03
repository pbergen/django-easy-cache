==========
Change Log
==========

0.2.0 (TBD)
===========

Features
--------

* Deterministic serialization for complex object types including sets, frozensets, dataclasses, and custom objects
* Centralized type exclusion configuration for better maintainability

Technical
---------

* Removed deprecated SerializationProtocol in favor of centralized configuration
* Added comprehensive Sphinx documentation structure

0.1.0
=====

Features
--------

* Time-based cache invalidation with timezone support
* Cron-based cache invalidation with flexible scheduling
* Database analytics and performance tracking
* Django Admin integration for cache entries and event history
* Management commands for cache status, analytics, and clearing
* ``@easy_cache.time_based()`` decorator for daily invalidation at specific times
* ``@easy_cache.cron_based()`` decorator for flexible cron-based invalidation
* Automatic cache key generation with collision avoidance
* Database models for cache analytics (CacheEntry, CacheEventHistory)
* Management commands: ``status``, ``analytics``, ``clear``
* Django Admin interface at ``/admin/django_easy_cache/``

Bugfixes
--------

* Fixed package name configuration for Sphinx documentation
* Resolved CI database conflicts and modernized database configuration
* Allowed CI to run pre-commit on protected branches while enforcing local branch restrictions

Technical
---------

* Built on Django's cache framework for backend compatibility
* Support for Redis, Memcached, Database, and Local Memory cache backends
* Atomic database operations for analytics tracking
* Thread-safe cache operations
* Comprehensive cache key validation
* Type hints throughout the codebase
* Modular architecture with separated concerns
* Robust error handling with graceful degradation
* Comprehensive test suite with pytest
* Replaced pre-commit branch restrictions with GitHub rulesets
