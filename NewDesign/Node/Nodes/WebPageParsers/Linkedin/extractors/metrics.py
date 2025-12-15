from .base import BaseExtractor
from .registry import SELECTORS
from .utils import parse_int


class MetricsExtractor(BaseExtractor):
    def extract(self):
        data = {}
        metrics_sels = SELECTORS["metrics"]

        followers_raw = self.extract_with_fallback(
            "followers", metrics_sels["followers"]
        )
        connections_raw = self.extract_with_fallback(
            "connections", metrics_sels["connections"]
        )

        # We store both raw (cleaned) and parsed numeric values if strict typing is needed
        # For now, let's stick to the user's request of "normalizing" -> int

        data["followers"] = parse_int(followers_raw)
        data["connections"] = parse_int(connections_raw)

        return data
