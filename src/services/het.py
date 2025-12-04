"""
API services for het.uz cabinet.
"""

class HETService:
    """
    HETService class for handling API requests to het.uz cabinet.
    """

    def __init__(self, base_url: str) -> None:
        """
        Initialize the HETService with base URL and token.

        Args:
            base_url (str): The base URL of the API.
            token (str): The authentication token for the API.
        """
        self.base_url = base_url

    def authorize() -> str:
        """
        Authorize the user and return the token.

        Returns:
            str: The authorization token.
        """


    def request(endpoint: str, method: str, **kwargs)
