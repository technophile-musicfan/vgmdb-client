from structlog import get_logger
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from httpx import AsyncClient

BASE_URL = "https://vgmdb.net/"
DEFAULT_USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"

logger = get_logger(__name__)


class BaseClient:
    """"""
    def __init__(self,
                 base_url: str = BASE_URL,
                 user_agent: str = DEFAULT_USER_AGENT,
                 connection_token: str = None,
                 ):
        self._client = AsyncClient(
            base_url=base_url,
        )
        if user_agent is not None:
            self.update_user_agent(user_agent)
        if connection_token is not None:
            self.update_connection_token(connection_token)

    def _url(self, path: str) -> str:
        """
        :param path:
        :return:
        """
        return f"{self._client.base_url}/{path.lstrip('/')}"

    def update_connection_token(self, token: str):
        """Update the connection token with another."""
        self._client.cookies.set("cf_clearance", token)

    def update_user_agent(self, user_agent: str):
        """Update the user agent."""
        self._client.headers["User-Agent"] = user_agent

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self._client.aclose()

    async def aclose(self):
        await self._client.aclose()

class AlbumClient(BaseClient):
    """

    """

    def get_album(self):
        """"""

    def search_albums(self):
        """"""

    @staticmethod
    def parse_album():
        """"""

class UserClient(BaseClient):
    """"""

