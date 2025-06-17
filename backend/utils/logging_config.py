"""
Structured logging configuration for Voice Bot API
Provides consistent, searchable, and analyzable log format
"""

import os
import sys
import json
import logging
import logging.config
from datetime import datetime
from typing import Dict, Any, Optional
from pythonjsonlogger import jsonlogger

class StructuredFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional context"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add application context
        log_record['application'] = 'voice-bot-api'
        log_record['environment'] = os.getenv('ENVIRONMENT', 'development')
        log_record['version'] = os.getenv('APP_VERSION', '1.0.0')
        
        # Add process information
        log_record['process_id'] = os.getpid()
        log_record['thread_id'] = record.thread
        
        # Handle exception information
        if record.exc_info:
            log_record['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info) if record.exc_info else None
            }

class ColoredConsoleFormatter(logging.Formatter):
    """Colored console formatter for development"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{level_color}{record.levelname}{self.COLORS['RESET']}"
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S.%f')[:-3]
        
        # Build formatted message
        message = super().format(record)
        
        # Add request ID if available
        request_id = getattr(record, 'request_id', None)
        if request_id:
            message = f"[{request_id[:8]}] {message}"
        
        return f"{level_color}[{timestamp}]{self.COLORS['RESET']} {message}"

def setup_logging(
    log_level: str = None,
    log_format: str = None,
    enable_json_logging: bool = None,
    log_file: Optional[str] = None
):
    """
    Setup structured logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format ('json' or 'console')
        enable_json_logging: Whether to use JSON formatting
        log_file: Optional log file path
    """
    
    # Get configuration from environment or use defaults
    log_level = log_level or os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = log_format or os.getenv('LOG_FORMAT', 'console').lower()
    enable_json_logging = enable_json_logging if enable_json_logging is not None else os.getenv('JSON_LOGGING', 'false').lower() == 'true'
    log_file = log_file or os.getenv('LOG_FILE')
    
    # Determine if we should use JSON formatting
    use_json = enable_json_logging or log_format == 'json' or os.getenv('ENVIRONMENT', 'development') == 'production'
    
    # Configure formatters
    formatters = {
        'json': {
            '()': StructuredFormatter,
            'format': '%(timestamp)s %(level)s %(logger)s %(message)s'
        },
        'console': {
            '()': ColoredConsoleFormatter,
            'format': '%(name)s - %(levelname)s - %(message)s'
        },
        'simple': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    }
    
    # Configure handlers
    handlers = {
        'console': {
            'class': 'logging.StreamHandler',
            'level': log_level,
            'formatter': 'json' if use_json else 'console',
            'stream': sys.stdout
        }
    }
    
    # Add file handler if specified
    if log_file:
        handlers['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': log_level,
            'formatter': 'json',
            'filename': log_file,
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf8'
        }
    
    # Configure loggers
    loggers = {
        '': {  # Root logger
            'level': log_level,
            'handlers': list(handlers.keys()),
            'propagate': False
        },
        'uvicorn': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False
        },
        'uvicorn.access': {
            'level': 'WARNING',  # Reduce noise from access logs
            'handlers': ['console'],
            'propagate': False
        },
        'httpx': {
            'level': 'WARNING',  # Reduce noise from HTTP client
            'handlers': ['console'],
            'propagate': False
        }
    }
    
    # Build logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': formatters,
        'handlers': handlers,
        'loggers': loggers
    }
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Log configuration info
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        extra={
            'log_level': log_level,
            'log_format': 'json' if use_json else 'console',
            'log_file': log_file,
            'environment': os.getenv('ENVIRONMENT', 'development')
        }
    )

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

def log_function_call(func_name: str, args: Dict[str, Any] = None, **kwargs):
    """
    Log function call with parameters
    
    Args:
        func_name: Name of the function being called
        args: Function arguments
        **kwargs: Additional logging context
    """
    logger = logging.getLogger('function_calls')
    logger.debug(
        f"Function called: {func_name}",
        extra={
            'function': func_name,
            'arguments': args or {},
            **kwargs
        }
    )

def log_performance_metric(metric_name: str, value: float, unit: str = 'ms', **kwargs):
    """
    Log performance metrics
    
    Args:
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement
        **kwargs: Additional context
    """
    logger = logging.getLogger('performance')
    logger.info(
        f"Performance metric: {metric_name}",
        extra={
            'metric_name': metric_name,
            'metric_value': value,
            'metric_unit': unit,
            'metric_type': 'performance',
            **kwargs
        }
    )

def log_security_event(event_type: str, details: Dict[str, Any], severity: str = 'medium', **kwargs):
    """
    Log security-related events
    
    Args:
        event_type: Type of security event
        details: Event details
        severity: Event severity (low, medium, high, critical)
        **kwargs: Additional context
    """
    logger = logging.getLogger('security')
    
    log_method = {
        'low': logger.info,
        'medium': logger.warning,
        'high': logger.error,
        'critical': logger.critical
    }.get(severity, logger.warning)
    
    log_method(
        f"Security event: {event_type}",
        extra={
            'event_type': event_type,
            'event_category': 'security',
            'severity': severity,
            'details': details,
            **kwargs
        }
    )

# Initialize logging when module is imported
if not logging.getLogger().handlers:
    setup_logging()
