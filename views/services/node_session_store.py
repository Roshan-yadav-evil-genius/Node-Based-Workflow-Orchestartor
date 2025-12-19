"""
Node Session Store Module
Manages stateful node instances across multiple executions.
"""

import threading
from typing import Any, Dict, Optional


class NodeSessionStore:
    """
    In-memory store for node instances keyed by session_id.
    
    Enables stateful node execution by reusing the same instance
    across multiple execute calls within a session.
    
    Thread-safe singleton pattern.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._sessions: Dict[str, Any] = {}
                    cls._instance._session_lock = threading.Lock()
        return cls._instance
    
    def get(self, session_id: str) -> Optional[Any]:
        """
        Get a node instance by session_id.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Node instance if exists, None otherwise
        """
        with self._session_lock:
            return self._sessions.get(session_id)
    
    def set(self, session_id: str, instance: Any) -> None:
        """
        Store a node instance for a session.
        
        Args:
            session_id: Unique session identifier
            instance: Node instance to store
        """
        with self._session_lock:
            self._sessions[session_id] = instance
    
    def clear(self, session_id: str) -> bool:
        """
        Clear a session and its node instance.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if session existed and was cleared, False otherwise
        """
        with self._session_lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False
    
    def clear_all(self) -> int:
        """
        Clear all sessions.
        
        Returns:
            Number of sessions cleared
        """
        with self._session_lock:
            count = len(self._sessions)
            self._sessions.clear()
            return count
    
    def get_session_count(self) -> int:
        """
        Get the number of active sessions.
        
        Returns:
            Number of active sessions
        """
        with self._session_lock:
            return len(self._sessions)

