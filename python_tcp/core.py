"""A step-by-step explanation of TCP and implementation using Python's socket module"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_core.ipynb.

# %% auto 0
__all__ = ['LOCALHOST', 'DEFAULT_BUFFER_SIZE', 'DEFAULT_BACKLOG', 'get_free_port', 'SocketState', 'TCPConnection']

# %% ../nbs/00_core.ipynb 6
import socket
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any, Union
import threading
import time

# %% ../nbs/00_core.ipynb 8
def get_free_port() -> int:
    """Get an available port number by creating and closing a temporary socket."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

# %% ../nbs/00_core.ipynb 10
LOCALHOST = '127.0.0.1'
DEFAULT_BUFFER_SIZE = 1024
DEFAULT_BACKLOG = 5  # Maximum number of queued connections

# %% ../nbs/00_core.ipynb 12
# Socket states
class SocketState:
    """Constants for socket states."""
    CLOSED = "CLOSED"
    LISTEN = "LISTEN"
    SYN_SENT = "SYN_SENT"
    SYN_RECEIVED = "SYN_RECEIVED"
    ESTABLISHED = "ESTABLISHED"
    FIN_WAIT_1 = "FIN_WAIT_1"
    FIN_WAIT_2 = "FIN_WAIT_2"
    CLOSE_WAIT = "CLOSE_WAIT"
    CLOSING = "CLOSING"
    LAST_ACK = "LAST_ACK"
    TIME_WAIT = "TIME_WAIT"

# %% ../nbs/00_core.ipynb 14
@dataclass
class TCPConnection:
    """Represents a TCP connection with state information."""
    socket: Optional[object] = None
    state: str = SocketState.CLOSED
    remote_address: Optional[Tuple[str, int]] = None
    connection_id: Optional[str] = None
    
    def __str__(self) -> str:
        addr = f"{self.remote_address[0]}:{self.remote_address[1]}" if self.remote_address else "None"
        return f"Connection[{self.connection_id or 'unknown'}] to {addr} (state: {self.state})"
    
    def update_state(self, new_state: str) -> None:
        """Update connection state with logging."""
        prev_state = self.state
        self.state = new_state
        # Normally we'd log this state transition
        print(f"Connection {self.connection_id}: {prev_state} -> {self.state}")
