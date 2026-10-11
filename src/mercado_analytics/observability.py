import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)

def retry(attempts=3, delay=2):
    def deco(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            last = None
            for attempt in range(1, attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    last = exc
                    logger.warning("Attempt %s/%s failed: %s", attempt, attempts, exc)
                    if attempt < attempts:
                        time.sleep(delay * attempt)
            raise last
        return wrapped
    return deco
