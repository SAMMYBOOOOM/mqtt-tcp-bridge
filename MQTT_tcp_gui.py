import paho.mqtt.client as mqtt
import socket
import threading
from PIL import Image, ImageTk
import time
import tkinter as tk
from tkinter import messagebox
import json
import os
import sys

# Path to the JSON configuration file
CONFIG_FILE = "config.json"

# Global variables to store MQTT and TCP details
mqtt_server = ""
mqtt_port = 0
client_id = ""
mqtt_username = ""
mqtt_password = ""
call_topic = ""
response_topic = ""
tcp_ip = ""
tcp_port = 0
use_tls = True  # Default to using TLS

# Global list to keep track of all connected TCP clients
connected_tcp_clients = []
tcp_clients_lock = threading.Lock()

# Global variables for MQTT client and TCP server
client = None
tcp_server_thread = None
input_window = None
tcp_socket = None  # Global TCP socket for proper cleanup

# Function to load configuration from JSON file
def load_config():
    global mqtt_server, mqtt_port, client_id, mqtt_username, mqtt_password, call_topic, response_topic, tcp_ip, tcp_port, use_tls
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            config = json.load(file)
            mqtt_server = config.get("mqtt_server", "")
            mqtt_port = config.get("mqtt_port", 8883)
            client_id = config.get("client_id", "")
            mqtt_username = config.get("mqtt_username", "")
            mqtt_password = config.get("mqtt_password", "")
            call_topic = config.get("call_topic", "")
            response_topic = config.get("response_topic", "")
            tcp_ip = config.get("tcp_ip", "")
            tcp_port = config.get("tcp_port", 8080)
            use_tls = config.get("use_tls", True)

# Function to save configuration to JSON file
def save_config():
    config = {
        "mqtt_server": mqtt_server,
        "mqtt_port": mqtt_port,
        "client_id": client_id,
        "mqtt_username": mqtt_username,
        "mqtt_password": mqtt_password,
        "call_topic": call_topic,
        "response_topic": response_topic,
        "tcp_ip": tcp_ip,
        "tcp_port": tcp_port,
        "use_tls": use_tls
    }
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)

# Callback when the client connects to the broker
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected to MQTT broker with result code {reason_code}")
    # Subscribe to the call topic
    client.subscribe(call_topic)
    client.publish(response_topic, "Connected to MQTT broker")

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
    global tcp_socket
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

# Function to start the MQTT client
def start_mqtt_client():
    global client
    if client is not None:
        # Disconnect and clean up the existing MQTT client
        client.loop_stop()
        client.disconnect()
        print("Disconnected existing MQTT client")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)

    # Set username and password if provided
    if mqtt_username:
        client.username_pw_set(mqtt_username, mqtt_password)

    # Configure TLS/SSL if enabled
    if use_tls:
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
        # Show error message
        messagebox.showerror("Connection Error", f"Failed to connect to MQTT broker: {e}")

    # Start the MQTT loop in a non-blocking manner
    client.loop_start()

# Function to handle the submit button click
def on_submit():
    global mqtt_server, mqtt_port, client_id, mqtt_username, mqtt_password, call_topic, response_topic, tcp_ip, tcp_port, use_tls

    # Get the values from the entry fields
    mqtt_server = mqtt_server_entry.get()
    mqtt_port = int(mqtt_port_entry.get())
    client_id = client_id_entry.get()
    mqtt_username = mqtt_username_entry.get()
    mqtt_password = mqtt_password_entry.get()
    call_topic = call_topic_entry.get()
    response_topic = response_topic_entry.get()
    tcp_ip = tcp_ip_entry.get()
    tcp_port = int(tcp_port_entry.get())
    use_tls = use_tls_var.get()

    # Save the new configuration to the JSON file
    save_config()

    # Start the MQTT client and TCP server
    start_mqtt_client()
    if tcp_server_thread is not None and tcp_server_thread.is_alive():
        # Stop the existing TCP server thread
        print("Stopping existing TCP server")
        # Close the TCP socket to stop the server
        if tcp_socket:
            tcp_socket.close()
    start_tcp_server_thread()

# Function to start the TCP server in a separate thread
def start_tcp_server_thread():
    global tcp_server_thread
    tcp_server_thread = threading.Thread(target=start_tcp_server)
    tcp_server_thread.daemon = True
    tcp_server_thread.start()

# Function to show the input window
def show_input_window():
    global input_window, mqtt_server_entry, mqtt_port_entry, client_id_entry, mqtt_username_entry, mqtt_password_entry, call_topic_entry, response_topic_entry, tcp_ip_entry, tcp_port_entry, use_tls_var

    # Create the main input window
    input_window = tk.Tk()
    input_window.title("MQTT and TCP Configuration")

    # Configure grid resizing behavior
    for i in range(10):
        input_window.grid_rowconfigure(i, weight=1)
    input_window.grid_columnconfigure(1, weight=1)

    # Load the developer icon
    try:
        dev_image = Image.open("dev.png")
        dev_image = dev_image.resize((50, 50), Image.Resampling.LANCZOS)  # Resize the image if needed
        dev_icon = ImageTk.PhotoImage(dev_image)
    except Exception as e:
        print(f"Error loading developer icon: {e}")
        dev_icon = None

    # Create a frame for the developer label and icon
    dev_frame = tk.Frame(input_window)
    dev_frame.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=5)

    if dev_icon:
        dev_label_icon = tk.Label(dev_frame, image=dev_icon)
        dev_label_icon.image = dev_icon  # Keep a reference to avoid garbage collection
        dev_label_icon.pack(side="left", padx=(0, 5))

    dev_label_text = tk.Label(dev_frame, text="Developed by Sam", font=("Arial", 10))
    dev_label_text.pack(side="left")

    # Create and place the labels and entry fields
    tk.Label(input_window, text="MQTT Server:").grid(row=1, column=0, sticky="w")
    mqtt_server_entry = tk.Entry(input_window)
    mqtt_server_entry.insert(0, mqtt_server)
    mqtt_server_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

    tk.Label(input_window, text="MQTT Port:").grid(row=2, column=0, sticky="w")
    mqtt_port_entry = tk.Entry(input_window)
    mqtt_port_entry.insert(0, str(mqtt_port))
    mqtt_port_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

    tk.Label(input_window, text="Client ID:").grid(row=3, column=0, sticky="w")
    client_id_entry = tk.Entry(input_window)
    client_id_entry.insert(0, client_id)
    client_id_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

    tk.Label(input_window, text="MQTT Username:").grid(row=4, column=0, sticky="w")
    mqtt_username_entry = tk.Entry(input_window)
    mqtt_username_entry.insert(0, mqtt_username)
    mqtt_username_entry.grid(row=4, column=1, sticky="ew", padx=5, pady=5)

    tk.Label(input_window, text="MQTT Password:").grid(row=5, column=0, sticky="w")
    mqtt_password_entry = tk.Entry(input_window, show="*")
    mqtt_password_entry.insert(0, mqtt_password)
    mqtt_password_entry.grid(row=5, column=1, sticky="ew", padx=5, pady=5)

    tk.Label(input_window, text="Call Topic:").grid(row=6, column=0, sticky="w")
    call_topic_entry = tk.Entry(input_window)
    call_topic_entry.insert(0, call_topic)
    call_topic_entry.grid(row=6, column=1, sticky="ew", padx=5, pady=5)

    tk.Label(input_window, text="Response Topic:").grid(row=7, column=0, sticky="w")
    response_topic_entry = tk.Entry(input_window)
    response_topic_entry.insert(0, response_topic)
    response_topic_entry.grid(row=7, column=1, sticky="ew", padx=5, pady=5)

    tk.Label(input_window, text="TCP IP:").grid(row=8, column=0, sticky="w")
    tcp_ip_entry = tk.Entry(input_window)
    tcp_ip_entry.insert(0, tcp_ip)
    tcp_ip_entry.grid(row=8, column=1, sticky="ew", padx=5, pady=5)

    tk.Label(input_window, text="TCP Port:").grid(row=9, column=0, sticky="w")
    tcp_port_entry = tk.Entry(input_window)
    tcp_port_entry.insert(0, str(tcp_port))
    tcp_port_entry.grid(row=9, column=1, sticky="ew", padx=5, pady=5)

    # Add a checkbox for enabling/disabling TLS
    use_tls_var = tk.BooleanVar(value=use_tls)
    tls_checkbox = tk.Checkbutton(input_window, text="Use TLS/SSL", variable=use_tls_var)
    tls_checkbox.grid(row=10, column=0, columnspan=2, sticky="w", padx=5, pady=5)

    # Create and place the submit button
    submit_button = tk.Button(input_window, text="Submit", command=on_submit)
    submit_button.grid(row=11, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

    # Handle window close event
    def on_closing():
        if client is not None:
            client.loop_stop()
            client.disconnect()
            print("MQTT client disconnected")
        if tcp_socket:
            tcp_socket.close()
            print("TCP server socket closed")
        input_window.destroy()
        sys.exit(0)  # Gracefully exit the program

    input_window.protocol("WM_DELETE_WINDOW", on_closing)

    # Start the main loop for the input window
    input_window.mainloop()

# Load the configuration from the JSON file
load_config()

# Show the input window
show_input_window()