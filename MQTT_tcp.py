import paho.mqtt.client as mqtt
import socket
import threading
import time

# MQTT Broker details
mqtt_server = ""
mqtt_port = 0
client_id = ""
mqtt_username = ""
mqtt_password = ""
call_topic = ""
response_topic = ""

# TCP Server details
tcp_ip = "127.0.0.1"
tcp_port = 0

# Global list to keep track of all connected TCP clients
connected_tcp_clients = []
tcp_clients_lock = threading.Lock()

# Callback when the client connects to the broker
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected to MQTT broker with result code {reason_code}")
    # Subscribe to the call topic
    client.subscribe(call_topic)

# Callback when a message is received from the broker
def on_message(client, userdata, msg):
    print(f"Received message on topic {msg.topic}: {len(msg.payload)} bytes")
    
    # Forward the raw payload directly to all connected TCP clients
    with tcp_clients_lock:
        disconnected_clients = []
        for tcp_client in connected_tcp_clients:
            try:
                tcp_client.sendall(msg.payload)
                print(f"Forwarded {len(msg.payload)} bytes to TCP client {tcp_client.getpeername()}")
            except Exception as e:
                print(f"Error sending to TCP client: {e}")
                disconnected_clients.append(tcp_client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            connected_tcp_clients.remove(client)

# Function to handle TCP client connections
def handle_tcp_client(client_socket):
    try:
        client_addr = client_socket.getpeername()
        print(f"TCP client connected: {client_addr}")
        
        # Add the client to our list of connected clients
        with tcp_clients_lock:
            connected_tcp_clients.append(client_socket)
        
        while True:
            # Receive data from the TCP client
            data = client_socket.recv(1024)
            if not data:
                break  # No more data, close the connection

            # Publish the raw binary data directly to the MQTT response topic
            client.publish(response_topic, data)
            print(f"Published {len(data)} bytes to MQTT topic {response_topic}")

    except Exception as e:
        print(f"Error handling TCP client: {e}")
    finally:
        # Remove the client from our list
        with tcp_clients_lock:
            if client_socket in connected_tcp_clients:
                connected_tcp_clients.remove(client_socket)
        
        # Close the TCP client socket
        client_socket.close()
        print(f"TCP client {client_addr} disconnected")

# Function to start the TCP server
def start_tcp_server():
    try:
        # Create a TCP socket
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allow reuse of the address
        tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind the socket to the IP and port
        tcp_socket.bind((tcp_ip, tcp_port))
        # Listen for incoming connections
        tcp_socket.listen(5)
        print(f"TCP server started on {tcp_ip}:{tcp_port}")
        print("Waiting for TCP client connections...")

        while True:
            # Accept a new connection
            client_socket, client_address = tcp_socket.accept()
            print(f"New TCP client connected: {client_address}")
            # Handle the client in a new thread
            client_thread = threading.Thread(target=handle_tcp_client, args=(client_socket,))
            client_thread.daemon = True
            client_thread.start()

    except Exception as e:
        print(f"TCP server error: {e}")

# Create an MQTT client instance with callback API version
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)

# Set username and password if provided
if mqtt_username:
    client.username_pw_set(mqtt_username, mqtt_password)

# Configure TLS/SSL
client.tls_set()

# Assign the callbacks
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT broker
try:
    client.connect(mqtt_server, mqtt_port, 60)
    print("Connected to MQTT broker")
except Exception as e:
    print(f"Failed to connect to MQTT broker: {e}")

# Start the MQTT loop in a non-blocking manner
client.loop_start()

# Start the TCP server in a separate thread
tcp_server_thread = threading.Thread(target=start_tcp_server)
tcp_server_thread.daemon = True
tcp_server_thread.start()

# Keep the main thread alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Program interrupted. Exiting...")
finally:
    # Disconnect the MQTT client
    client.loop_stop()
    client.disconnect()
    print("MQTT client disconnected")