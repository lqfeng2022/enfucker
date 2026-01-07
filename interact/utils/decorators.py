import time
from django.db import OperationalError, transaction


class RetryOnDeadlock:
    MYSQL_DEADLOCK_CODES = ('1213', '1205')

    def __init__(self, retries=3, delay=0.05):
        self.retries = retries
        self.delay = delay

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            for attempt in range(self.retries):
                try:
                    with transaction.atomic():
                        return func(*args, **kwargs)
                except OperationalError as e:
                    if not any(code in str(e) for code in self.MYSQL_DEADLOCK_CODES):
                        raise
                    if attempt + 1 == self.retries:
                        raise
                    time.sleep(self.delay)
        return wrapper
