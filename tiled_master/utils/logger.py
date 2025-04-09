import time
import os
from functools import wraps
from loguru import logger

# Reset default logger configuration
logger.remove()

# Custom log format function
def format_record(record):
    # Format log records, ensuring all parts are aligned
    time_str = f"<green>{record['time'].strftime('%Y-%m-%d %H:%M:%S')}</green>"
    level_str = f"<level>{record['level'].name:<8}</level>"
    source_str = f"<cyan>{record['name'].split('.')[-1]:<15}</cyan>:<cyan>{record['function']:<25}</cyan>:<cyan>{record['line']:<4}</cyan>"
    
    return (
        f"{time_str} | {level_str} | {source_str} | <level>{record['message']}</level>\n"
    )

# Add console output
logger.add(
    sink=lambda msg: print(msg, end=""), 
    format=format_record,
    level=os.getenv("LOG_LEVEL", "INFO"),
    colorize=True
)

# Add file logging (optional)
# logger.add("logs/app.log", rotation="10 MB", retention="1 week", format=format_record)

# Method execution time decorator
def logger_runtime():
    def decorator(func):
        @wraps(func)
        def normal_timer(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            logger.info(f"Function {func.__name__} executed in {end_time - start_time:.4f} seconds")
            return result

        return normal_timer

    return decorator

# Async method execution time decorator
def logger_runtime_async():
    def decorator(func):
        @wraps(func)
        async def async_timer(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()
            logger.info(f"Function {func.__name__} executed in {end_time - start_time:.4f} seconds")
            return result

        return async_timer

    return decorator
