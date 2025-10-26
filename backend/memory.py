"""
Memory management system for PRISM
Stores and retrieves past interactions for personalization
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages PRISM's memory database"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent / "prism_memory.db"
        
        self.db_path = str(db_path)
        self.conn = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize the SQLite database"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_input TEXT NOT NULL,
                    response TEXT NOT NULL,
                    action TEXT,
                    command TEXT
                )
            """)
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON interactions(timestamp DESC)
            """)
            self.conn.commit()
            logger.info(f"Memory database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def save_interaction(
        self,
        user_input: str,
        response: str,
        action: str = "",
        command: str = None
    ):
        """
        Save an interaction to memory
        
        Args:
            user_input: What the user said
            response: PRISM's response
            action: Type of action taken
            command: System command executed (if any)
        """
        try:
            self.conn.execute(
                """
                INSERT INTO interactions (user_input, response, action, command)
                VALUES (?, ?, ?, ?)
                """,
                (user_input, response, action, command)
            )
            self.conn.commit()
            logger.debug(f"Saved interaction: {user_input[:50]}...")
        except Exception as e:
            logger.error(f"Failed to save interaction: {e}")
    
    def get_recent_interactions(self, limit: int = 5) -> List[Tuple]:
        """
        Get recent interactions
        
        Args:
            limit: Number of recent interactions to retrieve
            
        Returns:
            List of tuples (timestamp, user_input, response, action, command)
        """
        try:
            cursor = self.conn.execute(
                """
                SELECT timestamp, user_input, response, action, command
                FROM interactions
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,)
            )
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Failed to get recent interactions: {e}")
            return []
    
    def search_interactions(self, query: str, limit: int = 5) -> List[Tuple]:
        """
        Search for interactions matching a query
        
        Args:
            query: Search term
            limit: Maximum number of results
            
        Returns:
            List of matching interactions
        """
        try:
            cursor = self.conn.execute(
                """
                SELECT timestamp, user_input, response, action, command
                FROM interactions
                WHERE user_input LIKE ? OR response LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (f"%{query}%", f"%{query}%", limit)
            )
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Failed to search interactions: {e}")
            return []
    
    def get_interaction_count(self) -> int:
        """Get total number of interactions"""
        try:
            cursor = self.conn.execute("SELECT COUNT(*) FROM interactions")
            return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Failed to get interaction count: {e}")
            return 0
    
    def clear_old_interactions(self, days: int = 30):
        """
        Clear interactions older than specified days
        
        Args:
            days: Number of days to keep
        """
        try:
            self.conn.execute(
                """
                DELETE FROM interactions
                WHERE timestamp < datetime('now', '-' || ? || ' days')
                """,
                (days,)
            )
            self.conn.commit()
            logger.info(f"Cleared interactions older than {days} days")
        except Exception as e:
            logger.error(f"Failed to clear old interactions: {e}")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Memory database connection closed")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()
