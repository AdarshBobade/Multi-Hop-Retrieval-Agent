import logging
import time
from functools import wraps



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    filename="logs/research.log",
    filemode="a"
)


def timer(func):
    #Decorator to measure execution time of any function.
    @wraps(func)
    def wrapper(*args, **kwargs):

        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()

        elapsed = (end - start) * 1000 
        logger = logging.getLogger(func.__module__)
        logger.info(
            f"{func.__name__} completed in {elapsed:.2f} ms"
        )

        return result
    return wrapper