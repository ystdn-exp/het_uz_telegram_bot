from typing import Optional

from httpx import AsyncClient, HTTPStatusError, RequestError


class HTTPClient:
    """
    Async HTTP client for handling HTTP requests without blocking the event loop.
    """

    def __init__(self, max_retries: int = 3):
        """
        Initialize HTTP client with configuration.

        Args:
            timeout (float): Request timeout in seconds
            max_retries (int): Maximum number of retry attempts for failed requests
        """
        self.max_retries = max_retries

    async def _request(
        self,
        client: AsyncClient,
        method: str,
        endpoint: str,
        headers: Optional[dict] = None,
        **kwargs,
    ):
        """
        Make an async HTTP request to the specified endpoint.

        Args:
            method (str): The HTTP method to use (e.g., 'GET', 'POST').
            endpoint (str): The API endpoint to request.
            headers (dict): Optional headers to include in request.
            **kwargs: Additional arguments to pass to the request.

        Returns:
            httpx.Response: The response from the API.
        """
        # Create a copy to avoid mutating the original headers dictionary
        request_headers = (headers or {}).copy()
        request_headers["Coato-Code"] = "26280"

        for attempt in range(self.max_retries):
            try:
                response = await client.request(
                    method, endpoint, headers=request_headers, **kwargs
                )
                response.raise_for_status()
                return response
            except HTTPStatusError as e:
                # Return response for 4xx errors (client errors)
                if e.response.status_code < 500:
                    return e.response
                # Retry on 5xx errors (server errors)
                if attempt == self.max_retries - 1:
                    raise
            except RequestError:
                # Retry on network errors
                if attempt == self.max_retries - 1:
                    raise
