import asyncio
import logging
import threading
import aiohttp

logger = logging.getLogger(__file__)


class RequestMixin:
    """
    Class: RequestMixin
    -----------
    Mixin that extending parent class to methods for asynchronous requests
    """

    # Requests params
    __RETRY_ATTEMPTS = 5
    __RETRY_START_TIMEOUT = 0.9
    __RETRY_MAX_TIMEOUT = 30
    __RETRY_FACTOR = 2

    def __init__(self, **kwargs):
        # Server`s attrs
        self._token = kwargs.get('auth_token')
        self.__loop = None
        self.__session = None

    def __calculate_delay(self, used_attempts=1):
        """
        Calculate delay between requests
        """
        timeout = self.__RETRY_START_TIMEOUT * (self.__RETRY_FACTOR ** (used_attempts - 1))
        return min(timeout, self.__RETRY_MAX_TIMEOUT)

    def _get_event_loop(self):
        """
        Get/Create async session
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = None
            if not isinstance(threading.current_thread(), threading._MainThread):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        return loop

    def _get_session(self):
        """
        Get/Create async session
        """
        loop = self._get_event_loop()
        if not self.__session or self.__session.closed:
            self.__session = aiohttp.ClientSession(loop=loop)
        return self.__session

    async def _request(self, url, attempt=0, session=None, headers=None):
        """
        Get response from server (async)
        """
        if attempt > self.__RETRY_ATTEMPTS:
            logger.debug(f'Failed request at url: {url}. Number of retries exceeded')
            raise Exception('Number of retries exceeded')

        session = session if session else self._get_session()
        async with session.get(url, ssl=False, **({'headers': headers} if headers else {})) as response:
            logger.info(f'Request at url: {url}')
            if response.status not in (200,):
                logger.debug(f'Failed request at url: {url}. Status code: {response.status}')
                return await self._request(url, attempt + 1)
            return await response.read()
