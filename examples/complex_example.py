"""
Comprehensive TCP Example

This script demonstrates the full capabilities of our TCP implementation
including the event-driven server and client, custom message handling,
and multiple simultaneous connections.
"""

from python_tcp.core import *
from python_tcp.server import EventDrivenTCPServer
from python_tcp.client import EventDrivenTCPClient
import threading
import time
import json
import random

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def colored(text, color):
    """Return colored text for terminal display."""
    return f"{color}{text}{Colors.ENDC}"

def run_server(port=8000):
    """Run an event-driven server with custom message handling."""
    server = EventDrivenTCPServer(port=port)
    
    # Set up event handlers
    server.on_connect = lambda conn_id, addr: print(colored(
        f"Server: Client connected from {addr[0]}:{addr[1]} (ID: {conn_id})",
        Colors.GREEN
    ))
    
    server.on_disconnect = lambda conn_id: print(colored(
        f"Server: Client disconnected (ID: {conn_id})",
        Colors.YELLOW
    ))
    
    server.on_data = lambda conn_id, data: print(colored(
        f"Server: Received from {conn_id}: {data.decode('utf-8')}",
        Colors.BLUE
    ))
    
    # Set up a custom message handler that processes JSON
    def message_handler(conn_id, data):
        try:
            # Try to parse as JSON
            message = json.loads(data.decode('utf-8'))
            
            if isinstance(message, dict) and 'command' in message:
                command = message['command']
                
                if command == 'echo':
                    # Simple echo response
                    return json.dumps({
                        'status': 'success',
                        'command': 'echo',
                        'data': message.get('data', ''),
                        'timestamp': time.time()
                    }).encode('utf-8')
                
                elif command == 'random':
                    # Generate a random number within the given range
                    try:
                        min_val = message.get('min', 1)
                        max_val = message.get('max', 100)
                        random_num = random.randint(min_val, max_val)
                        
                        return json.dumps({
                            'status': 'success',
                            'command': 'random',
                            'result': random_num,
                            'timestamp': time.time()
                        }).encode('utf-8')
                    except Exception as e:
                        return json.dumps({
                            'status': 'error',
                            'command': 'random',
                            'message': str(e),
                            'timestamp': time.time()
                        }).encode('utf-8')
                
                elif command == 'time':
                    # Return the current server time
                    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
                    return json.dumps({
                        'status': 'success',
                        'command': 'time',
                        'result': current_time,
                        'timestamp': time.time()
                    }).encode('utf-8')
                
                else:
                    # Unknown command
                    return json.dumps({
                        'status': 'error',
                        'message': f"Unknown command: {command}",
                        'timestamp': time.time()
                    }).encode('utf-8')
            else:
                # Not a valid command format
                return json.dumps({
                    'status': 'error',
                    'message': "Invalid message format. Expected JSON with 'command' field.",
                    'timestamp': time.time()
                }).encode('utf-8')
                
        except json.JSONDecodeError:
            # Not JSON, just echo it back
            return data
    
    server.set_message_handler(message_handler)
    server.start()
    return server

def run_client(name, port, commands):
    """Run a client that sends a series of commands to the server."""
    client = EventDrivenTCPClient()
    
    # Set up event handlers
    client.on_connect = lambda host, port: print(colored(
        f"Client {name}: Connected to {host}:{port}",
        Colors.GREEN
    ))
    
    client.on_disconnect = lambda: print(colored(
        f"Client {name}: Disconnected from server",
        Colors.YELLOW
    ))
    
    def on_data(data):
        try:
            # Try to parse as JSON
            response = json.loads(data.decode('utf-8'))
            print(colored(
                f"Client {name} received: {json.dumps(response, indent=2)}",
                Colors.BLUE
            ))
        except json.JSONDecodeError:
            # Not JSON, just print it
            print(colored(
                f"Client {name} received: {data.decode('utf-8')}",
                Colors.BLUE
            ))
    
    client.on_data = on_data
    
    client.on_error = lambda error: print(colored(
        f"Client {name} error: {error}",
        Colors.RED
    ))
    
    # Connect to the server
    if client.connect(LOCALHOST, port):
        try:
            # Send each command with a delay between them
            for command in commands:
                print(colored(
                    f"Client {name} sending: {json.dumps(command, indent=2)}",
                    Colors.BOLD
                ))
                client.send(json.dumps(command).encode('utf-8'))
                time.sleep(1)
            
            # Wait a moment for responses
            time.sleep(1)
            
        finally:
            # Close the connection
            client.close()
    
    return client

def main():
    # Start the server
    server = run_server()
    print(colored(f"Server started on {LOCALHOST}:{server.port}", Colors.HEADER))
    
    # Give the server a moment to start
    time.sleep(0.5)
    
    try:
        # Create multiple client threads with different commands
        client_threads = []
        
        # Client 1 - Echo commands
        client1_commands = [
            {'command': 'echo', 'data': 'Hello, server!'},
            {'command': 'echo', 'data': 'This is an echo test.'}
        ]
        client1_thread = threading.Thread(
            target=run_client, 
            args=('Echo', server.port, client1_commands)
        )
        client_threads.append(client1_thread)
        
        # Client 2 - Random number commands
        client2_commands = [
            {'command': 'random', 'min': 1, 'max': 10},
            {'command': 'random', 'min': 100, 'max': 200}
        ]
        client2_thread = threading.Thread(
            target=run_client, 
            args=('Random', server.port, client2_commands)
        )
        client_threads.append(client2_thread)
        
        # Client 3 - Time commands and an invalid command
        client3_commands = [
            {'command': 'time'},
            {'command': 'invalid_command'},
            "This is not a JSON message"  # This will be handled as raw data
        ]
        client3_thread = threading.Thread(
            target=run_client, 
            args=('Time', server.port, client3_commands)
        )
        client_threads.append(client3_thread)
        
        # Start all client threads
        for thread in client_threads:
            thread.start()
        
        # Wait for all client threads to finish
        for thread in client_threads:
            thread.join()
        
    finally:
        # Stop the server
        print(colored("Stopping server...", Colors.HEADER))
        server.stop()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(colored("\nProgram interrupted by user", Colors.RED))