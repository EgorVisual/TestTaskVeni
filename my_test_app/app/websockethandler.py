import asyncio
from asyncio import Queue

import json
from json import JSONDecodeError

from fastapi import WebSocket

from loguru import logger

from typing import Dict, Set

from pydantic import ValidationError

from .domain import ActuatorRequest, ActuatorResponse, GenericResponse, SerialRequest
from .serial_arduino import send_command_serial
from .states_file import read_states, write_states

_STATES_NAME: Dict[str, str] = {
    "0": "ACTUATOR_1",
    "1": "ACTUATOR_2",
}

PREFIX = "WebSocket:"


class WebSocketHandler:
    def __init__(self, ws_client: WebSocket, request_queue: Queue, response_queue: Queue, clients: Set[WebSocket]):
        self.request_queue = request_queue
        self.response_queue = response_queue
        self.ws_client = ws_client
        self.clients = clients

    async def receive_request(self) -> None:
        while True:
            request = await self.ws_client.receive_text()
            logger.info(f"{PREFIX} We get from client: {request}")
            try:
                parsed_json = json.loads(request)
                request = ActuatorRequest(**parsed_json)
                if request.actuator_id in _STATES_NAME:
                    self.request_queue.put_nowait(request)
                else:
                    await self.ws_client.send_text((GenericResponse(
                        status="error", detail=f"Number of actuator "
                                               f"is unknown: {request.actuator_id}").json(by_alias=True)))
            except (JSONDecodeError, ValidationError) as e:
                await self.ws_client.send_text((GenericResponse(status="error", detail=str(e)).json(by_alias=True)))
            await asyncio.sleep(.2)

    async def process_request(self) -> None:
        while True:
            if not self.request_queue.empty():
                request = self.request_queue.get_nowait()
                if request.state == "toggle":
                    current_state = self._restore_states(request.actuator_id)
                    if current_state == "close": request.state = "open"
                    if current_state == "open": request.state = "close"
                serial_request = SerialRequest(actuator_id=request.actuator_id, state=request.state)
                send_command_serial(serial_request)
                self.request_queue.task_done()
            await asyncio.sleep(.2)

    async def process_response(self):
        while True:
            if not (self.response_queue.empty()):
                response = self.response_queue.get_nowait()
                if response.actuator_id in _STATES_NAME:
                    self._update_states(response.actuator_id, response.state)
                    self.response_queue.task_done()
                    await self._update_clients_pages(response, self.clients)
            await asyncio.sleep(.2)

    async def greet_new_client(self) -> None:
        await self.ws_client.accept()
        logger.info(f'{PREFIX} new client ({self.ws_client}) connected.')
        for actuator_id in _STATES_NAME:
            state = self._restore_states(actuator_id)
            response = ActuatorResponse(actuator_id=actuator_id, state=state)
            await self.ws_client.send_text(response.json(by_alias=True))

    @staticmethod
    async def _update_clients_pages(response: ActuatorResponse, clients: Set[WebSocket]):
        logger.info(f'{PREFIX} send updated data to clients: {response.json(by_alias=True)}')
        for client in clients:
            await client.send_text(response.json(by_alias=True))

    @staticmethod
    def _restore_states(actuator_id: str) -> str:
        states = read_states()
        state = states.get(actuator_id)
        if state is None:
            WebSocketHandler._update_states(actuator_id, 'close')
            serial_request = SerialRequest(actuator_id=actuator_id, state='close')
            send_command_serial(serial_request)
        return states.get(actuator_id)

    @staticmethod
    def _update_states(actuator_id: str, state: str) -> None:
        states = read_states()
        states[actuator_id] = state
        write_states(states)
