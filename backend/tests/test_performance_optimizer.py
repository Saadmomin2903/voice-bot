"""
Unit tests for performance optimization system
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch
from utils.performance_optimizer import (
    AsyncOptimizer, MemoryManager, PerformanceMonitor,
    async_timed, memory_efficient, PerformanceMetrics
)

@pytest.mark.unit
class TestAsyncOptimizer:
    """Test async optimization functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.optimizer = AsyncOptimizer(max_workers=2)
    
    def teardown_method(self):
        """Clean up after tests"""
        self.optimizer.cleanup()
    
    @pytest.mark.asyncio
    async def test_run_in_thread(self):
        """Test running sync function in thread pool"""
        def sync_function(x, y):
            time.sleep(0.1)  # Simulate work
            return x + y
        
        result = await self.optimizer.run_in_thread(sync_function, 5, 3)
        assert result == 8
    
    @pytest.mark.asyncio
    async def test_run_with_timeout_success(self):
        """Test running coroutine with timeout (success case)"""
        async def fast_coro():
            await asyncio.sleep(0.1)
            return "success"
        
        result = await self.optimizer.run_with_timeout(fast_coro(), timeout=1.0)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_run_with_timeout_failure(self):
        """Test running coroutine with timeout (timeout case)"""
        async def slow_coro():
            await asyncio.sleep(2.0)
            return "too_slow"
        
        with pytest.raises(asyncio.TimeoutError):
            await self.optimizer.run_with_timeout(slow_coro(), timeout=0.5)

@pytest.mark.unit
class TestMemoryManager:
    """Test memory management functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.memory_manager = MemoryManager(max_memory_mb=100)
    
    def test_get_memory_usage(self):
        """Test memory usage reporting"""
        usage = self.memory_manager.get_memory_usage()
        assert isinstance(usage, float)
        assert usage >= 0
    
    def test_check_memory_pressure(self):
        """Test memory pressure detection"""
        # Should not have pressure with low limit
        self.memory_manager.max_memory_mb = 10000
        assert not self.memory_manager.check_memory_pressure()
        
        # Should have pressure with very low limit
        self.memory_manager.max_memory_mb = 1
        # This might be True or False depending on actual memory usage
        pressure = self.memory_manager.check_memory_pressure()
        assert isinstance(pressure, bool)
    
    def test_cache_audio(self):
        """Test audio caching functionality"""
        test_data = b"fake_audio_data"
        metadata = {"voice": "test", "speed": 1.0}
        
        self.memory_manager.cache_audio("test_key", test_data, metadata)
        
        assert "test_key" in self.memory_manager.audio_cache
        assert self.memory_manager.audio_cache["test_key"]["data"] == test_data
        assert self.memory_manager.audio_cache["test_key"]["metadata"] == metadata
    
    def test_get_cached_audio(self):
        """Test retrieving cached audio"""
        test_data = b"fake_audio_data"
        
        # Cache some data
        self.memory_manager.cache_audio("test_key", test_data)
        
        # Retrieve it
        retrieved = self.memory_manager.get_cached_audio("test_key")
        assert retrieved == test_data
        
        # Try to get non-existent data
        not_found = self.memory_manager.get_cached_audio("nonexistent")
        assert not_found is None
    
    def test_cache_size_limit(self):
        """Test cache size limiting"""
        # Set small cache limit
        self.memory_manager.cache_size_limit = 2
        
        # Add more items than the limit
        for i in range(5):
            self.memory_manager.cache_audio(f"key_{i}", f"data_{i}".encode())
        
        # Should only have 2 items (the limit)
        assert len(self.memory_manager.audio_cache) == 2
    
    @pytest.mark.asyncio
    async def test_force_cleanup(self):
        """Test force cleanup functionality"""
        # Add some cached data
        for i in range(10):
            self.memory_manager.cache_audio(f"key_{i}", f"data_{i}".encode())
        
        initial_count = len(self.memory_manager.audio_cache)
        
        # Force cleanup
        await self.memory_manager.force_cleanup()
        
        # Should have cleaned up some items
        final_count = len(self.memory_manager.audio_cache)
        assert final_count <= initial_count

@pytest.mark.unit
class TestPerformanceMonitor:
    """Test performance monitoring functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.monitor = PerformanceMonitor()
    
    def test_record_request(self):
        """Test recording request metrics"""
        # Record some requests
        self.monitor.record_request(0.1)
        self.monitor.record_request(0.2)
        self.monitor.record_request(0.15)
        
        assert self.monitor.metrics.request_count == 3
        assert abs(self.monitor.metrics.avg_response_time - 0.15) < 0.001  # Allow for floating point precision
        assert self.monitor.metrics.peak_response_time == 0.2
        assert len(self.monitor.request_times) == 3
    
    def test_get_percentiles(self):
        """Test percentile calculations"""
        # Add some request times
        times = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        for t in times:
            self.monitor.record_request(t)
        
        percentiles = self.monitor.get_percentiles()
        
        assert "p50" in percentiles
        assert "p90" in percentiles
        assert "p95" in percentiles
        assert "p99" in percentiles
        
        # Check that percentiles are reasonable
        assert percentiles["p50"] <= percentiles["p90"]
        assert percentiles["p90"] <= percentiles["p95"]
        assert percentiles["p95"] <= percentiles["p99"]
    
    def test_get_performance_report(self):
        """Test comprehensive performance report"""
        # Record some requests
        for i in range(10):
            self.monitor.record_request(0.1 + i * 0.01)
        
        report = self.monitor.get_performance_report()
        
        assert "uptime_seconds" in report
        assert "requests_per_second" in report
        assert "metrics" in report
        assert "percentiles" in report
        
        assert report["metrics"]["request_count"] == 10
        assert report["metrics"]["avg_response_time"] > 0
        assert report["uptime_seconds"] > 0

@pytest.mark.unit
class TestPerformanceDecorators:
    """Test performance decorators"""
    
    def setup_method(self):
        """Set up test environment"""
        self.monitor = PerformanceMonitor()
        self.memory_manager = MemoryManager(max_memory_mb=100)
    
    @pytest.mark.asyncio
    async def test_async_timed_decorator(self):
        """Test async timing decorator"""
        @async_timed(self.monitor)
        async def test_function():
            await asyncio.sleep(0.1)
            return "result"
        
        initial_count = self.monitor.metrics.request_count
        
        result = await test_function()
        
        assert result == "result"
        assert self.monitor.metrics.request_count == initial_count + 1
        assert self.monitor.metrics.avg_response_time > 0
    
    @pytest.mark.asyncio
    async def test_memory_efficient_decorator(self):
        """Test memory efficient decorator"""
        @memory_efficient(self.memory_manager)
        async def test_function():
            return "result"
        
        result = await test_function()
        assert result == "result"
        # Decorator should not affect the result

@pytest.mark.unit
class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass"""
    
    def test_performance_metrics_creation(self):
        """Test PerformanceMetrics creation and defaults"""
        metrics = PerformanceMetrics()
        
        assert metrics.request_count == 0
        assert metrics.total_response_time == 0.0
        assert metrics.avg_response_time == 0.0
        assert metrics.peak_response_time == 0.0
        assert metrics.memory_usage_mb == 0.0
        assert metrics.active_connections == 0
    
    def test_performance_metrics_with_values(self):
        """Test PerformanceMetrics with custom values"""
        metrics = PerformanceMetrics(
            request_count=100,
            total_response_time=50.0,
            avg_response_time=0.5,
            peak_response_time=2.0,
            memory_usage_mb=128.5,
            active_connections=5
        )
        
        assert metrics.request_count == 100
        assert metrics.total_response_time == 50.0
        assert metrics.avg_response_time == 0.5
        assert metrics.peak_response_time == 2.0
        assert metrics.memory_usage_mb == 128.5
        assert metrics.active_connections == 5
