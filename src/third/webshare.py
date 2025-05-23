from httpx import Client

from src.core.logger import logger
from src.core.retrier import httpx_retry_on_failure


class WebShare:
    def __init__(self, api_key: str):
        self._client = Client(headers={"Authorization": f"Token {api_key}"})

    @httpx_retry_on_failure()
    def get_proxy_list(self, page_size: int) -> list[dict]:
        endpoint = "https://proxy.webshare.io/api/v2/proxy/list/"
        params = {"mode": "backbone", "page": 1, "page_size": page_size}
        response = self._client.get(endpoint, params=params)
        resp_data = response.json()
        return resp_data["results"]

    def get_proxies(self, page_size: int) -> list[str]:
        logger.info("GET PROXIES FROM WEBSHARE...")
        proxies_info = self.get_proxy_list(page_size)
        proxies = []
        for proxy_info in proxies_info:
            username = proxy_info["username"]
            password = proxy_info["password"]
            port = proxy_info["port"]
            proxy_url = f"http://{username}:{password}@p.webshare.io:{port}"
            proxies.append(proxy_url)
        logger.info(f"GOTTEN {len(proxies)} PROXIES")
        return proxies
