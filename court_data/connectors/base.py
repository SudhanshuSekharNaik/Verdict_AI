from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseCourtConnector(ABC):
    """Base interface for all permitted court data connectors."""

    @abstractmethod
    async def fetch_documents(self, search_query: str, **kwargs) -> List[Dict[str, Any]]:
        """Fetches permitted open court records matching the query."""
        pass

    @abstractmethod
    def validate_access(self) -> bool:
        """Validates that no anti-bot or access controls are violated."""
        pass
