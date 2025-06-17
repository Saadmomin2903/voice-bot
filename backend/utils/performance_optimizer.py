"""
Performance optimization utilities for Voice Bot API
Provides async optimization, connection pooling, and memory management
"""

import asyncio
import time
import gc
import threading
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
import logging
import weakref

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    request_count: int = 0
    total_response_time: float = 0.0
    avg_response_time: float = 0.0
    peak_response_time: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    active_connections: int = 0
    cache_hit_rate: float = 0.0

class AsyncOptimizer:
    """Async operation optimization and management"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.semaphore = asyncio.Semaphore(max_workers * 2)  # Allow some queuing
        self.active_tasks = weakref.WeakSet()
        
    async def run_in_thread(self, func: Callable, *args, **kwargs):
        """
        Run synchronous function in thread pool with semaphore control
        
        Args:
            func: Synchronous function to run
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        async with self.semaphore:
            loop = asyncio.get_event_loop()
            task = loop.run_in_executor(self.thread_pool, func, *args, **kwargs)
            self.active_tasks.add(task)
            try:
                return await task
            finally:
                self.active_tasks.discard(task)
    
    async def run_with_timeout(self, coro, timeout: float = 30.0):
        """
        Run coroutine with timeout
        
        Args:
            coro: Coroutine to run
            timeout: Timeout in seconds
            
        Returns:
            Coroutine result
            
        Raises:
            asyncio.TimeoutError: If timeout exceeded
        """
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Operation timed out after {timeout} seconds")
            raise
    
    def cleanup(self):
        """Clean up thread pool"""
        self.thread_pool.shutdown(wait=True)

class MemoryManager:
    """Memory management and optimization"""
    
    def __init__(self, max_memory_mb: int = 512):
        self.max_memory_mb = max_memory_mb
        self.audio_cache = {}
        self.cache_size_limit = 50  # Max cached audio files
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
        
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            # Fallback if psutil not available
            return 0.0
        except Exception:
            return 0.0
    
    def check_memory_pressure(self) -> bool:
        """Check if memory usage is high"""
        current_memory = self.get_memory_usage()
        return current_memory > self.max_memory_mb
    
    async def cleanup_if_needed(self):
        """Clean up memory if needed"""
        current_time = time.time()
        
        # Periodic cleanup
        if current_time - self.last_cleanup > self.cleanup_interval:
            await self.force_cleanup()
            self.last_cleanup = current_time
        
        # Emergency cleanup if memory pressure
        elif self.check_memory_pressure():
            logger.warning("Memory pressure detected, forcing cleanup")
            await self.force_cleanup()
    
    async def force_cleanup(self):
        """Force memory cleanup"""
        # Clear audio cache
        if len(self.audio_cache) > self.cache_size_limit:
            # Remove oldest entries
            sorted_cache = sorted(
                self.audio_cache.items(),
                key=lambda x: x[1].get('last_accessed', 0)
            )
            
            to_remove = len(sorted_cache) - self.cache_size_limit
            for i in range(to_remove):
                key = sorted_cache[i][0]
                del self.audio_cache[key]
            
            logger.info(f"Cleaned up {to_remove} cached audio files")
        
        # Force garbage collection
        collected = gc.collect()
        logger.info(f"Garbage collection freed {collected} objects")
        
        # Log memory status
        memory_usage = self.get_memory_usage()
        logger.info(f"Memory usage after cleanup: {memory_usage:.1f} MB")
    
    def cache_audio(self, key: str, data: bytes, metadata: Dict[str, Any] = None):
        """Cache audio data with size limits"""
        if len(self.audio_cache) >= self.cache_size_limit:
            # Remove oldest entry
            oldest_key = min(
                self.audio_cache.keys(),
                key=lambda k: self.audio_cache[k].get('last_accessed', 0)
            )
            del self.audio_cache[oldest_key]
        
        self.audio_cache[key] = {
            'data': data,
            'metadata': metadata or {},
            'cached_at': time.time(),
            'last_accessed': time.time(),
            'size_bytes': len(data)
        }
    
    def get_cached_audio(self, key: str) -> Optional[bytes]:
        """Get cached audio data"""
        if key in self.audio_cache:
            self.audio_cache[key]['last_accessed'] = time.time()
            return self.audio_cache[key]['data']
        return None

class ConnectionPool:
    """HTTP connection pooling for external APIs"""
    
    def __init__(self, max_connections: int = 10, max_keepalive: int = 5):
        import httpx
        
        # Configure connection limits
        limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive,
            keepalive_expiry=30.0
        )
        
        # Configure timeout
        timeout = httpx.Timeout(
            connect=10.0,
            read=30.0,
            write=10.0,
            pool=5.0
        )
        
        # Create async client with connection pooling
        self.client = httpx.AsyncClient(
            limits=limits,
            timeout=timeout,
            http2=True,  # Enable HTTP/2 for better performance
            verify=True  # Always verify SSL in production
        )
        
        self.stats = {
            'requests_made': 0,
            'connections_created': 0,
            'connections_reused': 0
        }
    
    async def request(self, method: str, url: str, **kwargs):
        """Make HTTP request using connection pool"""
        self.stats['requests_made'] += 1

        try:
            response = await self.client.request(method, url, **kwargs)
            return response
        except Exception as e:
            logger.error(f"HTTP request failed: {e}")
            raise
    
    async def close(self):
        """Close connection pool"""
        await self.client.aclose()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        return self.stats.copy()

class PerformanceMonitor:
    """Performance monitoring and metrics collection"""
    
    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.request_times = []
        self.max_history = 1000  # Keep last 1000 request times
        self.start_time = time.time()
        
    def record_request(self, response_time: float):
        """Record request performance metrics"""
        self.metrics.request_count += 1
        self.metrics.total_response_time += response_time
        self.metrics.avg_response_time = (
            self.metrics.total_response_time / self.metrics.request_count
        )
        
        if response_time > self.metrics.peak_response_time:
            self.metrics.peak_response_time = response_time
        
        # Keep rolling history
        self.request_times.append(response_time)
        if len(self.request_times) > self.max_history:
            self.request_times.pop(0)
    
    def update_system_metrics(self):
        """Update system-level metrics"""
        try:
            import psutil
            process = psutil.Process()
            self.metrics.memory_usage_mb = process.memory_info().rss / 1024 / 1024
        except ImportError:
            pass
        except Exception:
            pass
    
    def get_percentiles(self) -> Dict[str, float]:
        """Get response time percentiles"""
        if not self.request_times:
            return {}
        
        sorted_times = sorted(self.request_times)
        length = len(sorted_times)
        
        return {
            'p50': sorted_times[int(length * 0.5)],
            'p90': sorted_times[int(length * 0.9)],
            'p95': sorted_times[int(length * 0.95)],
            'p99': sorted_times[int(length * 0.99)]
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        self.update_system_metrics()
        
        uptime = time.time() - self.start_time
        
        return {
            'uptime_seconds': uptime,
            'requests_per_second': self.metrics.request_count / uptime if uptime > 0 else 0,
            'metrics': {
                'request_count': self.metrics.request_count,
                'avg_response_time': round(self.metrics.avg_response_time, 3),
                'peak_response_time': round(self.metrics.peak_response_time, 3),
                'memory_usage_mb': round(self.metrics.memory_usage_mb, 1),
                'cpu_usage_percent': round(self.metrics.cpu_usage_percent, 1)
            },
            'percentiles': self.get_percentiles()
        }

# Performance decorators
def async_timed(monitor: PerformanceMonitor):
    """Decorator to time async functions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                response_time = end_time - start_time
                monitor.record_request(response_time)
        return wrapper
    return decorator

def memory_efficient(memory_manager: MemoryManager):
    """Decorator to ensure memory efficiency"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Check memory before operation
            await memory_manager.cleanup_if_needed()
            
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                # Check memory after operation
                if memory_manager.check_memory_pressure():
                    await memory_manager.force_cleanup()
        return wrapper
    return decorator

# Global performance components
async_optimizer = AsyncOptimizer(max_workers=4)
memory_manager = MemoryManager(max_memory_mb=512)
connection_pool = ConnectionPool(max_connections=10)
performance_monitor = PerformanceMonitor()
