from httpx import HTTPError
from tenacity import retry, retry_if_exception_type, stop_after_delay, wait_exponential


def httpx_retry_on_failure():
    return retry(
        reraise=True,
        wait=wait_exponential(multiplier=1, min=1, max=60),
        stop=stop_after_delay(60),
        retry=retry_if_exception_type(HTTPError),
    )
