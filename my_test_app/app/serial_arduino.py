import json
import os
import re

import asyncio
from asyncio import Queue

from typing import Dict

from loguru import logger

from serial import Serial, SerialException
from serial.tools import list_ports

from my_test_app.app.domain import SerialRequest, ActuatorResponse

ARDUINO_1: str = "8543930323335111D1A2"
ARDUINO_2: str = "755333530383511130C0"

PREFIX = "Serial:"

ser = Serial(
    port=os.environ.get("SERIAL_PORT", 'COM8'),
    baudrate=int(os.environ.get('SERIAL_BAUDRATE', 9600)),
    timeout=int(os.environ.get('SERIAL_TIMEOUT', 0)),
)


def send_command_serial(serial_request: SerialRequest) -> None:
    try:
        msg = f'{serial_request.actuator_id}:{serial_request.state}'
        logger.info(f"{PREFIX} To Arduino: {msg.encode('ascii')}")
        ser.write(msg.encode('ascii'))
    except SerialException as e:
        logger.error(f"{PREFIX} Error: {e}")


async def background_receive_serial(response_queue: Queue) -> None:
    while True:
        serial_message: str = None
        message: str = None
        if ser.is_open and ser.in_waiting > 0:
            try:
                serial_message = ser.readline().decode("ascii")
                message = parse_serial(serial_message)
            except SerialException as e:
                logger.error(f"{PREFIX} serial error: {e}")
            except UnicodeDecodeError as e:
                logger.error(f'{PREFIX} unable to decode message ({repr(e.object)}); error:\"{e}\", ({ser.port}).')
            except IOError:
                logger.error(f'{PREFIX} unable to establish connection to serial port ({ser.port}).')
                ser.close()
        if message is not None:
            response = ActuatorResponse(**message)
            response_queue.put_nowait(response)
        await asyncio.sleep(.2)


def parse_serial(serial_message: str) -> Dict[str, str] or None:
    logger.info(f"{PREFIX} port: {ser.port} | get serial raw message: {serial_message}")
    if re.match(r'^(\d+):(open|close|busy|closing|opening)\r\n$', serial_message):
        delimiter_position = serial_message.find(':')
        new_line_position = serial_message.find('\r\n')
        actuator_id = serial_message[:delimiter_position]
        actuator_status = serial_message[delimiter_position + 1:new_line_position]
        return {'actuator_id': actuator_id, 'state': actuator_status}
    return None
