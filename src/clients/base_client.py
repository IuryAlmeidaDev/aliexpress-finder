from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseSearchClient(ABC):
    @abstractmethod
    def search(self, query: str, max_items: int = 30) -> List[Dict[str, Any]]:
        pass
