"""
WebSocket Bridge
Connects backend with Electron UI
"""

import asyncio
import json
from typing import Optional, Callable
import websockets
from loguru import logger

from backend.config import config


class WebSocketBridge:
    """
    WebSocket client that connects Python backend to Electron UI server
    """

    def __init__(self, port: int = 9876, host: str = "localhost"):
        self.port = port
        self.host = host
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False
        self.reconnect_task = None
        
        # Callback for messages from UI
        self.message_callback: Optional[Callable] = None
        
        # Connection retry settings
        self.max_retries = 10
        self.base_delay = 0.5
        self.max_delay = 5.0

    async def start(self):
        """Start WebSocket client and connect to UI server"""
        logger.info(f"Connecting to WebSocket server at ws://{self.host}:{self.port}...")
        
        self.running = True
        
        # Start connection with retry logic
        await self._connect_with_retry()
        
        # Start message receiver
        if self.websocket:
            asyncio.create_task(self._receive_messages())

    async def _connect_with_retry(self):
        """Connect to WebSocket server with exponential backoff"""
        retry_count = 0
        
        while self.running and retry_count < self.max_retries:
            try:
                self.websocket = await websockets.connect(
                    f"ws://{self.host}:{self.port}",
                    ping_interval=20,
                    ping_timeout=10
                )
                
                logger.success(f"Connected to WebSocket server at ws://{self.host}:{self.port}")
                return
                
            except (ConnectionRefusedError, OSError) as e:
                retry_count += 1
                delay = min(self.base_delay * (2 ** retry_count), self.max_delay)
                
                if retry_count < self.max_retries:
                    logger.warning(f"Connection attempt {retry_count}/{self.max_retries} failed, retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Failed to connect after {self.max_retries} attempts: {e}")
                    raise
                    
            except Exception as e:
                logger.error(f"Unexpected error connecting to WebSocket: {e}")
                raise

    async def _receive_messages(self):
        """Continuously receive messages from UI"""
        try:
            async for message in self.websocket:
                await self._handle_message(message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.websocket = None
            
            # Attempt reconnection if still running
            if self.running:
                logger.info("Attempting to reconnect...")
                await self._connect_with_retry()
                if self.websocket:
                    asyncio.create_task(self._receive_messages())
                    
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")
            self.websocket = None

    async def _handle_message(self, message: str):
        """Handle incoming message from UI"""
        try:
            data = json.loads(message)
            logger.info(f"Received from UI: {data.get('type', 'unknown')} - {data}")
            
            if self.message_callback:
                await self.message_callback(data)
            else:
                logger.warning("No message callback registered!")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from UI: {message}")
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)

    async def send_to_ui(self, data: dict):
        """Send message to UI"""
        if not self.websocket:
            logger.debug("No WebSocket connection, message not sent")
            return
        
        try:
            message = json.dumps(data)
            await self.websocket.send(message)
            logger.debug(f"Sent to UI: {data.get('type', 'unknown')}")
            
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Cannot send to UI - connection closed")
            self.websocket = None
        except Exception as e:
            logger.error(f"Error sending to UI: {e}")

    def register_callback(self, callback: Callable):
        """Register callback for messages from UI"""
        self.message_callback = callback

    async def shutdown(self):
        """Shutdown WebSocket client"""
        logger.info("Shutting down WebSocket bridge...")
        
        self.running = False
        
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception:
                pass
        
        logger.success("WebSocket bridge shutdown complete")
