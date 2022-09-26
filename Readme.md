# Test task for Veni

# Project description:

The project is a backend part of the Web app. 

The task:
1) Transmit commands from the frontend to the Serial port.
2) Receive responses from the Serial.
3) Send responses to the frontend.

The project was built using FastAPI with websocket, like interface. 

To start the project is necessary to create a **.env** file containing definitions of environment variables:
1. SERIAL_PORT - serial port (required)
2. SERIAL_BAUDRATE - serial port speed (optional, default value is 9600)
3. SERIAL_TIMEOUT - timeout for reading from the serial port (optional, default value is 0)

Example:
```shell
SERIAL_PORT=/dev/serial/by-id/id-of_required_serial_port
SERIAL_BAUDRATE=9600
SERIAL_TIMEOUT=0
```

