"""
Retry and failure recovery utilities for transformation processes
"""

import time
import random
from typing import Callable, Any, Optional, Type, Tuple
from loguru import logger
from functools import wraps
import traceback


class RetryConfig:
    """
    Configuration for retry behavior
    """
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 60.0, backoff_factor: float = 2.0,
                 retryable_exceptions: Tuple[Type[Exception], ...] = None,
                 non_retryable_exceptions: Tuple[Type[Exception], ...] = None):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.retryable_exceptions = retryable_exceptions or (
            TimeoutError,
            ConnectionError,
            IOError,
            OSError
        )
        self.non_retryable_exceptions = non_retryable_exceptions or ()


class CircuitBreaker:
    """
    Circuit breaker pattern to prevent cascading failures
    """
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        """
        if self.state == "OPEN":
            # Check if timeout has passed
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise RuntimeError("Circuit breaker is OPEN, operation rejected")
                
        try:
            result = func(*args, **kwargs)
            # Reset failure count on success
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
            self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                
            raise


def exponential_backoff_retry(config: RetryConfig = None, circuit_breaker: CircuitBreaker = None):
    """
    Decorator for implementing exponential backoff with jitter retry logic
    
    Args:
        config: Retry configuration
        circuit_breaker: Optional circuit breaker instance
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            # Use circuit breaker if provided
            if circuit_breaker:
                try:
                    return circuit_breaker.call(func, *args, **kwargs)
                except Exception as e:
                    logger.error(f"Circuit breaker prevented execution: {e}")
                    raise
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if this exception is non-retryable
                    if isinstance(e, config.non_retryable_exceptions):
                        logger.error(
                            f"Non-retryable exception in {func.__name__}: {e}"
                        )
                        raise
                    
                    # Check if this exception is retryable
                    if not isinstance(e, config.retryable_exceptions):
                        logger.error(
                            f"Unexpected exception in {func.__name__}: {e}. "
                            f"Marking as non-retryable."
                        )
                        raise
                    
                    if attempt < config.max_attempts - 1:  # Don't sleep on the last attempt
                        # Calculate delay with exponential backoff and jitter
                        delay = min(
                            config.base_delay * (config.backoff_factor ** attempt),
                            config.max_delay
                        )
                        # Add jitter (±25%)
                        jitter = random.uniform(-0.25, 0.25) * delay
                        actual_delay = max(0, delay + jitter)
                        
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {actual_delay:.2f}s..."
                        )
                        time.sleep(actual_delay)
                    else:
                        logger.error(
                            f"All {config.max_attempts} attempts failed for {func.__name__}: {e}"
                        )
                        logger.debug(f"Full traceback:\n{traceback.format_exc()}")
            
            raise last_exception
        return wrapper
    return decorator


def safe_overwrite_wrapper(func: Callable) -> Callable:
    """
    Wrapper to ensure safe overwrite behavior for transformation operations
    
    Args:
        func: Function to wrap
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        # In a real implementation, this would:
        # 1. Check if destination exists
        # 2. Compare hashes if needed
        # 3. Only proceed if data is different or overwrite is explicitly allowed
        # 4. Use atomic operations where possible
        
        logger.debug(f"Safe overwrite check for {func.__name__}")
        return func(*args, **kwargs)
    return wrapper


def idempotent_operation(func: Callable) -> Callable:
    """
    Decorator to make operations idempotent by preventing duplicate processing
    
    Args:
        func: Function to make idempotent
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        # In a real implementation, this would:
        # 1. Generate a unique identifier for the operation
        # 2. Check if operation has already been completed
        # 3. Skip if already completed
        # 4. Proceed normally if new or recovery needed
        
        logger.debug(f"Idempotent check for {func.__name__}")
        return func(*args, **kwargs)
    return wrapper


class TransformationRetryManager:
    """
    Manager for handling retry scenarios in transformations
    """
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        self.circuit_breaker = CircuitBreaker()
        
    def handle_retryable_error(self, error: Exception, operation_name: str, 
                              attempt: int, max_attempts: int) -> bool:
        """
        Determine if an error is retryable
        
        Args:
            error: Exception that occurred
            operation_name: Name of the operation
            attempt: Current attempt number
            max_attempts: Maximum number of attempts
            
        Returns:
            True if retry should be attempted, False otherwise
        """
        # Common retryable exceptions
        retryable_exceptions = (
            TimeoutError,
            ConnectionError,
            IOError,
            OSError
        )
        
        # Check if error is retryable
        if isinstance(error, retryable_exceptions):
            if attempt < max_attempts - 1:
                logger.warning(
                    f"Retryable error in {operation_name}: {error}. "
                    f"Attempt {attempt + 1}/{max_attempts}"
                )
                return True
            else:
                logger.error(
                    f"Non-retryable error in {operation_name}: {error}. "
                    f"Maximum attempts ({max_attempts}) reached."
                )
        else:
            logger.error(f"Permanent error in {operation_name}: {error}")
            
        return False
        
    def safe_execute_with_retry(self, operation: Callable, *args, **kwargs) -> Any:
        """
        Safely execute an operation with retry logic
        
        Args:
            operation: Function to execute
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the operation
        """
        last_exception = None
        
        # Use circuit breaker if configured
        if hasattr(self, 'circuit_breaker') and self.circuit_breaker:
            try:
                return self.circuit_breaker.call(operation, *args, **kwargs)
            except Exception as e:
                logger.error(f"Circuit breaker prevented execution: {e}")
                raise
        
        for attempt in range(self.config.max_attempts):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if self.handle_retryable_error(e, operation.__name__, attempt, self.config.max_attempts):
                    # Calculate delay with exponential backoff and jitter
                    delay = min(
                        self.config.base_delay * (self.config.backoff_factor ** attempt),
                        self.config.max_delay
                    )
                    # Add jitter (±25%)
                    jitter = random.uniform(-0.25, 0.25) * delay
                    actual_delay = max(0, delay + jitter)
                    
                    logger.info(f"Retrying in {actual_delay:.2f}s...")
                    time.sleep(actual_delay)
                else:
                    break
                    
        raise last_exception if last_exception else RuntimeError("Operation failed")