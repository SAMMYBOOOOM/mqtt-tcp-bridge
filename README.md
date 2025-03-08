# MQTT-TCP Bridge with GUI

This project provides a bridge between MQTT (Message Queuing Telemetry Transport) and TCP (Transmission Control Protocol) communication. It allows you to forward messages between MQTT topics and TCP clients seamlessly. The project includes a graphical user interface (GUI) for easy configuration and management.

## Features

- **MQTT to TCP Forwarding**: Forward messages received on an MQTT topic to connected TCP clients.
    
- **TCP to MQTT Forwarding**: Forward data received from TCP clients to an MQTT topic.
    
- **GUI Configuration**: Configure MQTT broker details, TCP server settings, and topics through a user-friendly GUI.
    
- **TLS/SSL Support**: Secure your MQTT connections with TLS/SSL encryption.
    
- **Multi-Client Support**: Handle multiple TCP client connections simultaneously.
    
- **Configuration Persistence**: Save and load configuration settings from a JSON file.
    

## Requirements

- Python 3.x
    
- `paho-mqtt` library
    
- `Pillow` library (for GUI image handling)
    
- `tkinter` (for GUI)
    
- `pyinstaller` (for compiling to .exe)
    

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/SAMMYBOOOOM/mqtt-tcp-bridge.git
   cd mqtt-tcp-bridge
   ```

2. **Install the required Python packages**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   - To run the Python script directly:
     ```bash
     python MQTT_tcp_gui.py
     ```
   - To use the compiled `.exe` file, navigate to the `build` directory and run:
     ```bash
     ./MQTT_tcp_gui.exe
     ```

## Usage

1. **Launch the Application**:
    
    - Run the `MQTT_tcp_gui.exe` from the `build` directory.
        
2. **Configure Settings**:
    
    - Enter the MQTT broker details (server, port, username, password).
        
    - Specify the MQTT topics for call and response.
        
    - Set the TCP server IP and port.
        
    - Enable or disable TLS/SSL as needed.
        
3. **Submit Configuration**:
    
    - Click the "Submit" button to save the configuration and start the MQTT client and TCP server.
        
4. **Monitor Connections**:
    
    - The application will print connection and message forwarding details to the console.
        

## License

This project is licensed under the **GNU General Public License Version 2 (GPL-2.0)**. See the [LICENSE](https://license/) file for more details.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## Issues

If you encounter any issues, please open an issue on the [GitHub repository](https://github.com/SAMMYBOOOOM/mqtt-tcp-bridge/issues).

## Acknowledgments

- Developed by Sam.
    

---

With this setup, you can seamlessly transfer MQTT messages to Mission Planner via TCP, enabling integration with MAVLink-based systems. 🚀