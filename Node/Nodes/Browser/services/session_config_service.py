import requests
from typing import Optional, Dict, Any
import structlog

logger = structlog.get_logger(__name__)


class SessionConfigService:
    """Service to fetch browser session configuration from backend API."""
    
    BASE_URL = "http://127.0.0.1:7878/api/browser-sessions"
    
    @staticmethod
    def get_session_config(session_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch full session config from backend.
        
        Args:
            session_id: The UUID of the browser session
            
        Returns:
            Session config dict with browser_type, playwright_config, etc.
            Returns None if session not found or API unreachable.
        """
        try:
            response = requests.get(
                f"{SessionConfigService.BASE_URL}/{session_id}/config/", 
                timeout=5
            )
            if response.status_code == 200:
                config = response.json()
                logger.debug(
                    "Fetched session config",
                    session_id=session_id,
                    browser_type=config.get('browser_type'),
                    has_playwright_config=bool(config.get('playwright_config'))
                )
                return config
            else:
                logger.warning(
                    "Failed to fetch session config",
                    session_id=session_id,
                    status_code=response.status_code
                )
        except requests.exceptions.Timeout:
            logger.error(
                "Timeout fetching session config",
                session_id=session_id
            )
        except requests.exceptions.ConnectionError:
            logger.error(
                "Connection error fetching session config",
                session_id=session_id
            )
        except Exception as e:
            logger.error(
                "Unexpected error fetching session config",
                session_id=session_id,
                error=str(e)
            )
        return None

