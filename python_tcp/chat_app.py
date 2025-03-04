"""A step-by-step tutorial showing how to build a chat application using our TCP implementation"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/04_chat_app.ipynb.

# %% auto 0
__all__ = ['ChatServer', 'ChatClient', 'run_chat_client', 'run_chat_server', 'start_server', 'start_client']

# %% ../nbs/04_chat_app.ipynb 5
class ChatServer:
    """A simple chat server using our TCP implementation."""
    
    def __init__(self, host=LOCALHOST, port=0):
        """Initialize the chat server."""
        self.host = host
        self.port = port
        self.server = EventDrivenTCPServer(host, port)
        
        # Track connected users: {connection_id: username}
        self.users = {}
        
        # Set up event handlers
        self.server.on_connect = self._on_client_connect
        self.server.on_disconnect = self._on_client_disconnect
        self.server.on_data = self._on_data_received
        
        # Set up message handler
        self.server.set_message_handler(self._handle_message)
    
    def start(self):
        """Start the chat server."""
        self.server.start()
        print(f"Chat server running at {self.host}:{self.port}")
        return self.port
    
    def stop(self):
        """Stop the chat server."""
        self.server.stop()
        print("Chat server stopped")
    
    def _on_client_connect(self, conn_id, addr):
        """Handle a new client connection."""
        print(f"New connection from {addr[0]}:{addr[1]} (ID: {conn_id})")
        # We'll assign the username when we receive the join message
    
    def _on_client_disconnect(self, conn_id):
        """Handle a client disconnection."""
        if conn_id in self.users:
            username = self.users[conn_id]
            del self.users[conn_id]
            print(f"User {username} disconnected")
            
            # Notify other users about the departure
            self._broadcast_user_leave(username)
            
            # Send updated user list
            self._broadcast_user_list()
    
    def _on_data_received(self, conn_id, data):
        """Handle received data."""
        try:
            message = json.loads(data.decode('utf-8'))
            print(f"Received: {message}")
        except json.JSONDecodeError:
            print(f"Received invalid JSON: {data.decode('utf-8')}")
    
    def _handle_message(self, conn_id, data):
        """Process a message and return a response."""
        try:
            message = json.loads(data.decode('utf-8'))
            message_type = message.get('type')
            
            if message_type == 'join':
                return self._handle_join(conn_id, message)
            elif message_type == 'message':
                return self._handle_chat_message(conn_id, message)
            elif message_type == 'leave':
                return self._handle_leave(conn_id, message)
            else:
                return self._create_error_response("Unknown message type")
                
        except json.JSONDecodeError:
            return self._create_error_response("Invalid JSON format")
        except Exception as e:
            return self._create_error_response(str(e))
    
    def _handle_join(self, conn_id, message):
        """Handle a join message."""
        username = message.get('username')
        
        if not username:
            return self._create_error_response("Username is required")
        
        # Check if username is already taken
        if username in self.users.values():
            return self._create_error_response("Username already taken")
        
        # Register the user
        self.users[conn_id] = username
        print(f"User {username} joined")
        
        # Broadcast join message to all users
        self._broadcast_user_join(username)
        
        # Send updated user list to all
        self._broadcast_user_list()
        
        # Send welcome message to the new user
        return json.dumps({
            'type': 'welcome',
            'content': f"Welcome to the chat, {username}!",
            'timestamp': time.time()
        }).encode('utf-8')
    
    def _handle_chat_message(self, conn_id, message):
        """Handle a chat message."""
        if conn_id not in self.users:
            return self._create_error_response("You are not registered in the chat")
        
        username = self.users[conn_id]
        content = message.get('content', '')
        
        if not content:
            return self._create_error_response("Message content is required")
        
        # Broadcast the message to all users
        self._broadcast_message(username, content)
        
        # No need to send a response to the sender
        return None
    
    def _handle_leave(self, conn_id, message):
        """Handle a leave message."""
        if conn_id not in self.users:
            return self._create_error_response("You are not registered in the chat")
        
        username = self.users[conn_id]
        
        # Broadcast leave message
        self._broadcast_user_leave(username)
        
        # Remove the user
        del self.users[conn_id]
        
        # Send updated user list
        self._broadcast_user_list()
        
        # Send goodbye message
        return json.dumps({
            'type': 'goodbye',
            'content': f"Goodbye, {username}!",
            'timestamp': time.time()
        }).encode('utf-8')
    
    def _broadcast_message(self, username, content):
        """Broadcast a chat message to all users."""
        message = {
            'type': 'message',
            'username': username,
            'content': content,
            'timestamp': time.time()
        }
        
        self._broadcast(json.dumps(message).encode('utf-8'))
    
    def _broadcast_user_join(self, username):
        """Broadcast a user join notification."""
        message = {
            'type': 'join',
            'username': username,
            'timestamp': time.time()
        }
        
        self._broadcast(json.dumps(message).encode('utf-8'))
    
    def _broadcast_user_leave(self, username):
        """Broadcast a user leave notification."""
        message = {
            'type': 'leave',
            'username': username,
            'timestamp': time.time()
        }
        
        self._broadcast(json.dumps(message).encode('utf-8'))
    
    def _broadcast_user_list(self):
        """Broadcast the current user list."""
        message = {
            'type': 'users',
            'users': list(self.users.values()),
            'timestamp': time.time()
        }
        
        self._broadcast(json.dumps(message).encode('utf-8'))
    
    def _broadcast(self, data):
        """Send data to all connected clients."""
        for conn_id in list(self.users.keys()):
            try:
                self.server.send(conn_id, data)
            except Exception as e:
                print(f"Error broadcasting to {conn_id}: {e}")
    
    def _create_error_response(self, error_message):
        """Create an error response."""
        return json.dumps({
            'type': 'error',
            'content': error_message,
            'timestamp': time.time()
        }).encode('utf-8')

# %% ../nbs/04_chat_app.ipynb 7
class ChatClient:
    """A simple chat client using our TCP implementation."""
    
    def __init__(self, username):
        """Initialize the chat client."""
        self.username = username
        self.client = EventDrivenTCPClient()
        self.connected = False
        
        # Set up event handlers
        self.client.on_connect = self._on_connected
        self.client.on_disconnect = self._on_disconnected
        self.client.on_data = self._on_data_received
        self.client.on_error = self._on_error
        
        # Callback for message display
        self.message_callback = None
        
        # Current user list
        self.users = []
    
    def connect(self, host, port):
        """Connect to the chat server."""
        return self.client.connect(host, port)
    
    def join(self):
        """Join the chat with the provided username."""
        if not self.connected:
            print("Not connected to a server")
            return False
        
        # Send join message
        message = {
            'type': 'join',
            'username': self.username,
            'timestamp': time.time()
        }
        
        return self.client.send(json.dumps(message).encode('utf-8'))
    
    def send_message(self, content):
        """Send a chat message."""
        if not self.connected:
            print("Not connected to a server")
            return False
        
        # Send chat message
        message = {
            'type': 'message',
            'content': content,
            'timestamp': time.time()
        }
        
        return self.client.send(json.dumps(message).encode('utf-8'))
    
    def leave(self):
        """Leave the chat."""
        if not self.connected:
            print("Not connected to a server")
            return False
        
        # Send leave message
        message = {
            'type': 'leave',
            'timestamp': time.time()
        }
        
        result = self.client.send(json.dumps(message).encode('utf-8'))
        
        # Give a moment for the message to be sent
        time.sleep(0.5)
        
        # Disconnect
        self.client.close()
        return result
    
    def set_message_callback(self, callback):
        """Set the callback for displaying messages."""
        self.message_callback = callback
    
    def _on_connected(self, host, port):
        """Handle successful connection."""
        self.connected = True
        if self.message_callback:
            self.message_callback(f"Connected to {host}:{port}")
    
    def _on_disconnected(self):
        """Handle disconnection."""
        self.connected = False
        if self.message_callback:
            self.message_callback("Disconnected from server")
    
    def _on_error(self, error):
        """Handle errors."""
        if self.message_callback:
            self.message_callback(f"Error: {error}")
    
    def _on_data_received(self, data):
        """Handle received data."""
        try:
            message = json.loads(data.decode('utf-8'))
            message_type = message.get('type')
            
            if message_type == 'message':
                self._handle_chat_message(message)
            elif message_type == 'join':
                self._handle_join(message)
            elif message_type == 'leave':
                self._handle_leave(message)
            elif message_type == 'users':
                self._handle_users(message)
            elif message_type == 'welcome':
                self._handle_welcome(message)
            elif message_type == 'goodbye':
                self._handle_goodbye(message)
            elif message_type == 'error':
                self._handle_error(message)
            else:
                if self.message_callback:
                    self.message_callback(f"Received unknown message type: {message_type}")
        
        except json.JSONDecodeError:
            if self.message_callback:
                self.message_callback(f"Received invalid JSON: {data.decode('utf-8')}")
        except Exception as e:
            if self.message_callback:
                self.message_callback(f"Error processing message: {e}")
    
    def _handle_chat_message(self, message):
        """Handle a chat message."""
        username = message.get('username')
        content = message.get('content')
        timestamp = message.get('timestamp')
        
        if self.message_callback:
            time_str = datetime.datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
            self.message_callback(f"[{time_str}] {username} left the chat")
    
    def _handle_users(self, message):
        """Handle a users list update."""
        self.users = message.get('users', [])
        
        if self.message_callback:
            users_str = ", ".join(self.users)
            self.message_callback(f"Users in chat: {users_str}")
    
    def _handle_welcome(self, message):
        """Handle a welcome message."""
        content = message.get('content')
        timestamp = message.get('timestamp')
        
        if self.message_callback:
            time_str = datetime.datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
            self.message_callback(f"[{time_str}] Server: {content}")
    
    def _handle_goodbye(self, message):
        """Handle a goodbye message."""
        content = message.get('content')
        timestamp = message.get('timestamp')
        
        if self.message_callback:
            time_str = datetime.datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
            self.message_callback(f"[{time_str}] Server: {content}")
    
    def _handle_error(self, message):
        """Handle an error message."""
        content = message.get('content')
        timestamp = message.get('timestamp')
        
        if self.message_callback:
            time_str = datetime.datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
            self.message_callback(f"[{time_str}] Error: {content}")

# %% ../nbs/04_chat_app.ipynb 11
def run_chat_client():
    """Run a command-line chat client."""
    print("=== Chat Client ===")
    username = input("Enter your username: ")
    
    host = input("Enter server host (default: localhost): ") or LOCALHOST
    port_str = input("Enter server port (default: 8000): ") or "8000"
    port = int(port_str)
    
    # Create the chat client
    client = ChatClient(username)
    
    # Define the message callback
    def display_message(msg):
        print(msg)
    
    client.set_message_callback(display_message)
    
    # Connect to the server
    print(f"Connecting to {host}:{port}...")
    if not client.connect(host, port):
        print("Failed to connect to the server")
        return
    
    # Join the chat
    client.join()
    
    print("\nChat commands:")
    print("/users - Show current users")
    print("/exit or /quit - Leave the chat")
    print("Any other text will be sent as a message")
    print("Start typing your messages:\n")
    
    try:
        while True:
            message = input("")
            
            if message.lower() in ["/exit", "/quit"]:
                break
            elif message.lower() == "/users":
                users_str = ", ".join(client.users)
                print(f"Users in chat: {users_str}")
            else:
                client.send_message(message)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        print("Leaving chat...")
        client.leave()

# %% ../nbs/04_chat_app.ipynb 12
def run_chat_server():
    """Run a chat server."""
    print("=== Chat Server ===")
    port_str = input("Enter server port (default: 8000): ") or "8000"
    port = int(port_str)
    
    # Create and start the chat server
    server = ChatServer(port=port)
    server.start()
    
    print("\nServer is running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server.stop()

# %% ../nbs/04_chat_app.ipynb 14
def start_server():
    """Entry point for starting a chat server."""
    run_chat_server()

# %% ../nbs/04_chat_app.ipynb 15
def start_client():
    """Entry point for starting a chat client."""
    run_chat_client()
