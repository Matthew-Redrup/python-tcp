"""
Simple TCP Echo Example

This script demonstrates a working implementation of our TCP library
with a basic echo server and client.
"""

from python_tcp.core import *
from python_tcp.server import TCPServer
from python_tcp.client import TCPClient
import threading
import time

def run_server(port=8000):
    """Run a simple echo server on the given port."""
    server = TCPServer(port=port)
    server.start()
    return server

def run_client(port=8000, message="Hello, TCP world!"):
    """Connect to the server, send a message, and receive a response."""
    client = TCPClient()
    if client.connect(LOCALHOST, port):
        print(f"Client: Sending message: {message}")
        client.send(message.encode('utf-8'))
        
        # Receive response
        response = client.receive()
        if response:
            print(f"Client: Received: {response.decode('utf-8')}")
        
        # Close the connection
        client.close()
    else:
        print("Client: Connection failed")

def main():
    # Start the server
    server = run_server()
    print(f"Server started on {LOCALHOST}:{server.port}")
    
    # Give the server a moment to start
    time.sleep(0.5)
    
    try:
        # Run the client in a separate thread
        client_thread = threading.Thread(target=run_client, args=(server.port,))
        client_thread.start()
        client_thread.join()
        
        # Run another client with a different message
        client_thread = threading.Thread(
            target=run_client, 
            args=(server.port, "Another test message!")
        )
        client_thread.start()
        client_thread.join()
        
    finally:
        # Stop the server
        print("Stopping server...")
        server.stop()

if __name__ == "__main__":
    main()