"""
API services for het.uz cabinet.
"""

from httpx import AsyncClient

from src.services.constants import HET_BASE_URL
from src.services.http import HTTPClient


class HETService(HTTPClient):
    """
    HETService class for handling API requests to het.uz cabinet.
    """

    def __init__(self, base_url: str) -> None:
        """
        Initialize the HETService with base URL.

        Args:
            base_url (str): The base URL of the API.
        """
        super().__init__()
        self.api_path = "household-consumer/v1/mobile-cabinet"
        self.base_url = base_url
        self.base_endpoint = f"{self.base_url}/{self.api_path}"

    async def authorize(self, client: AsyncClient, username: str, password: str):
        """
        Authorize the user and return the token.

        Args:
            client (AsyncClient): HTTP client
            username (str): HET account username
            password (str): HET account password

        Returns:
            tuple: (response_dict, status_code)
        """
        response = await self._request(
            client,
            "POST",
            f"{self.base_endpoint}/user-login",
            json={"login": username, "password": password},
        )
        return response.json(), response.status_code

    async def refresh_token(self, client: AsyncClient, refresh_token: str):
        """
        Refresh the access token.

        Args:
            client (AsyncClient): HTTP client
            refresh_token (str): The refresh token

        Returns:
            tuple: (response_dict, status_code)
        """
        response = await self._request(
            client,
            "POST",
            f"{self.base_endpoint}/refresh-token",
            json={"refreshToken": refresh_token},
        )
        return response.json(), response.status_code

    async def get_user_details(self, client: AsyncClient, access_token: str):
        """
        Fetch user details including meter info, tariff, balance, status.

        Args:
            client (AsyncClient): HTTP client
            access_token (str): User's access token

        Returns:
            tuple: (response_dict, status_code)
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await self._request(
            client, "GET", f"{self.base_endpoint}/user-details", headers=headers
        )
        return response.json(), response.status_code

    async def get_consumer_state(self, client: AsyncClient, access_token: str):
        """
        Fetch consumer state including last reading, payment, balance, current month usage.

        Args:
            client (AsyncClient): HTTP client
            access_token (str): User's access token

        Returns:
            tuple: (response_dict, status_code)
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await self._request(
            client, "GET", f"{self.base_endpoint}/consumer-state", headers=headers
        )
        return response.json(), response.status_code

    async def get_monthly_consumption(
        self, client: AsyncClient, access_token: str, year: int
    ):
        """
        Fetch monthly consumption data by tariff for a specific year.

        Args:
            client (AsyncClient): HTTP client
            access_token (str): User's access token
            year (int): Year to fetch data for

        Returns:
            tuple: (response_dict, status_code)
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await self._request(
            client,
            "GET",
            f"{self.base_endpoint}/get-monthly-consumption-by-tariff-new",
            headers=headers,
            params={"year": year},
        )
        return response.json(), response.status_code

    async def get_eco_monthly_consumption(
        self, client: AsyncClient, access_token: str, year: int
    ):
        """
        Fetch eco monthly consumption data for a specific year (multi-tariff).

        Args:
            client (AsyncClient): HTTP client
            access_token (str): User's access token
            year (int): Year to fetch data for

        Returns:
            tuple: (response_dict, status_code)
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await self._request(
            client,
            "GET",
            f"{self.base_endpoint}/eco-monthly-consumption",
            headers=headers,
            params={"year": year},
        )
        return response.json(), response.status_code

    async def get_payments(
        self, client: AsyncClient, access_token: str, page: int = 0, size: int = 10
    ):
        """
        Fetch payment history with pagination.

        Args:
            client (AsyncClient): HTTP client
            access_token (str): User's access token
            page (int): Page number (0-indexed)
            size (int): Number of records per page

        Returns:
            tuple: (response_dict, status_code)
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await self._request(
            client,
            "GET",
            f"{self.base_endpoint}/payments-page",
            headers=headers,
            params={"page": page, "size": size},
        )
        return response.json(), response.status_code

    async def get_reading_histories(
        self, client: AsyncClient, access_token: str, page: int = 0, size: int = 10
    ):
        """
        Fetch meter reading history with pagination.

        Args:
            client (AsyncClient): HTTP client
            access_token (str): User's access token
            page (int): Page number (0-indexed)
            size (int): Number of records per page

        Returns:
            tuple: (response_dict, status_code)
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await self._request(
            client,
            "GET",
            f"{self.base_endpoint}/reading-histories",
            headers=headers,
            params={"page": page, "size": size},
        )
        return response.json(), response.status_code


het_service = HETService(base_url=HET_BASE_URL)
