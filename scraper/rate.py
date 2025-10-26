import random
import time
from typing import Callable, Optional

from tenacity import retry, stop_after_attempt, wait_exponential


class RateLimiter:
    """Sleep with jitter between actions."""

    def __init__(self, delay_min: float = 1.5, delay_max: float = 3.0) -> None:
        self.delay_min = delay_min
        self.delay_max = delay_max

    def sleep(self) -> None:
        delay = random.uniform(self.delay_min, self.delay_max)
        time.sleep(delay)


def retryable(func: Optional[Callable] = None, *, attempts: int = 3):
    """Decorator applying tenacity retry with exponential backoff."""

    def decorator(fn: Callable) -> Callable:
        return retry(
            reraise=True,
            stop=stop_after_attempt(attempts),
            wait=wait_exponential(multiplier=1, min=1, max=10),
        )(fn)

    if func is None:
        return decorator
    return decorator(func)
