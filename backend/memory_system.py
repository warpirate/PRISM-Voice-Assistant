"""
Memory and Learning System
Stores interactions, learns patterns, and provides personalization
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import sqlite3
from loguru import logger

from backend.config import config


class MemorySystem:
    """
    Manages conversation history, user preferences, and learning
    """

    def __init__(self):
        self.db_path = config.data_dir / "memory.db"
        self.conn: Optional[sqlite3.Connection] = None
        self.initialized = False

    async def initialize(self):
        """Initialize memory database"""
        if self.initialized:
            return
        
        logger.info("Initializing memory system...")
        
        try:
            # Create database connection
            self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            
            # Create tables
            await self._create_tables()
            
            # Clean old data if needed
            await self._cleanup_old_data()
            
            self.initialized = True
            logger.success("Memory system initialized")
            
        except Exception as e:
            logger.error(f"Error initializing memory system: {e}")
            raise

    async def _create_tables(self):
        """Create database tables"""
        cursor = self.conn.cursor()
        
        # Interactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                input_method TEXT,
                requires_action BOOLEAN,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Patterns table (learned behaviors)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_data TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                last_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_interactions_timestamp 
            ON interactions(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_patterns_type 
            ON patterns(pattern_type)
        """)
        
        self.conn.commit()

    async def store_interaction(self, interaction: Dict[str, Any]):
        """Store a user or assistant interaction"""
        if not config.privacy.store_conversations:
            return
        
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT INTO interactions 
                (timestamp, role, content, input_method, requires_action, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                interaction.get("timestamp", datetime.now().isoformat()),
                interaction.get("role"),
                interaction.get("content"),
                interaction.get("input_method"),
                interaction.get("requires_action", False),
                json.dumps(interaction.get("metadata", {}))
            ))
            
            self.conn.commit()
            
            # Update patterns
            await self._update_patterns(interaction)
            
        except Exception as e:
            logger.error(f"Error storing interaction: {e}")

    async def get_recent_interactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent interactions"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT * FROM interactions 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            
            return [
                {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "role": row["role"],
                    "content": row["content"],
                    "input_method": row["input_method"],
                    "requires_action": bool(row["requires_action"]),
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Error getting recent interactions: {e}")
            return []

    async def search_interactions(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search interactions by content"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT * FROM interactions 
                WHERE content LIKE ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (f"%{query}%", limit))
            
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error searching interactions: {e}")
            return []

    async def _update_patterns(self, interaction: Dict[str, Any]):
        """Update learned patterns based on interaction"""
        try:
            # Extract patterns from user input
            if interaction.get("role") == "user":
                content = interaction.get("content", "").lower()
                
                # Command patterns
                command_keywords = ["open", "launch", "start", "search", "find", "create"]
                for keyword in command_keywords:
                    if keyword in content:
                        await self._record_pattern(
                            "command",
                            {"keyword": keyword, "content": content}
                        )
                
                # Application patterns
                for app_name in ["chrome", "vscode", "notepad", "calculator"]:
                    if app_name in content:
                        await self._record_pattern(
                            "application",
                            {"app": app_name}
                        )
            
        except Exception as e:
            logger.error(f"Error updating patterns: {e}")

    async def _record_pattern(self, pattern_type: str, pattern_data: Dict[str, Any]):
        """Record or update a pattern"""
        try:
            cursor = self.conn.cursor()
            
            pattern_json = json.dumps(pattern_data)
            
            # Check if pattern exists
            cursor.execute("""
                SELECT id, frequency FROM patterns 
                WHERE pattern_type = ? AND pattern_data = ?
            """, (pattern_type, pattern_json))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update frequency
                cursor.execute("""
                    UPDATE patterns 
                    SET frequency = frequency + 1, last_seen = ? 
                    WHERE id = ?
                """, (datetime.now().isoformat(), existing["id"]))
            else:
                # Insert new pattern
                cursor.execute("""
                    INSERT INTO patterns (pattern_type, pattern_data, frequency)
                    VALUES (?, ?, 1)
                """, (pattern_type, pattern_json))
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Error recording pattern: {e}")

    async def get_patterns(self, pattern_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get learned patterns"""
        try:
            cursor = self.conn.cursor()
            
            if pattern_type:
                cursor.execute("""
                    SELECT * FROM patterns 
                    WHERE pattern_type = ? 
                    ORDER BY frequency DESC, last_seen DESC 
                    LIMIT ?
                """, (pattern_type, limit))
            else:
                cursor.execute("""
                    SELECT * FROM patterns 
                    ORDER BY frequency DESC, last_seen DESC 
                    LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            
            return [
                {
                    "id": row["id"],
                    "pattern_type": row["pattern_type"],
                    "pattern_data": json.loads(row["pattern_data"]),
                    "frequency": row["frequency"],
                    "last_seen": row["last_seen"]
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Error getting patterns: {e}")
            return []

    async def set_preference(self, key: str, value: Any):
        """Set a user preference"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO preferences (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, json.dumps(value), datetime.now().isoformat()))
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Error setting preference: {e}")

    async def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT value FROM preferences WHERE key = ?
            """, (key,))
            
            row = cursor.fetchone()
            
            if row:
                return json.loads(row["value"])
            return default
            
        except Exception as e:
            logger.error(f"Error getting preference: {e}")
            return default

    async def _cleanup_old_data(self):
        """Clean up old interaction data based on retention policy"""
        if not config.privacy.retention_days:
            return
        
        try:
            cutoff_date = (datetime.now() - timedelta(days=config.privacy.retention_days)).isoformat()
            
            cursor = self.conn.cursor()
            
            cursor.execute("""
                DELETE FROM interactions WHERE timestamp < ?
            """, (cutoff_date,))
            
            deleted = cursor.rowcount
            
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} old interactions")
            
            self.conn.commit()
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")

    async def export_data(self, output_path: Path):
        """Export all data to JSON file"""
        try:
            data = {
                "interactions": await self.get_recent_interactions(limit=1000),
                "patterns": await self.get_patterns(limit=100),
                "exported_at": datetime.now().isoformat()
            }
            
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.success(f"Data exported to {output_path}")
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")

    async def clear_all_data(self):
        """Clear all stored data (for privacy)"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("DELETE FROM interactions")
            cursor.execute("DELETE FROM patterns")
            
            self.conn.commit()
            
            logger.info("All data cleared")
            
        except Exception as e:
            logger.error(f"Error clearing data: {e}")

    async def shutdown(self):
        """Shutdown memory system"""
        logger.info("Shutting down memory system...")
        
        if self.conn:
            self.conn.close()
        
        self.initialized = False
        logger.success("Memory system shutdown complete")
