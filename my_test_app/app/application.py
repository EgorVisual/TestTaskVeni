import json
import os
import asyncio

from loguru import logger

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import Set

from .serial_arduino import background_receive_serial
from .states_file import init_states, read_states, write_states
from .websockethandler import WebSocketHandler

app = FastAPI()

logger.add("my_test_app/data/logs.log", rotation="50 MB")

WS_CLIENTS: Set[WebSocket] = set()
RESPONSE_QUEUE = asyncio.Queue()
REQUEST_QUEUE = asyncio.Queue()

PREFIX = "CLIENT: "

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>My controller</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <button onclick="sendCommand(event, id)" id="open_button">Open</button>
        <button onclick="sendCommand(event, id)" id="close_button">Close</button>
        <input id = "command_first_output" value = "Command 1"/>
        <input id = "command_second_output" value = "Command 2"/>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
                const actuatorStates = JSON.parse(event.data);
                console.log(actuatorStates)
                if (actuatorStates["actuatorId"] == 0){
                    document.getElementById("command_first_output").value = actuatorStates["state"]
                }
                if (actuatorStates["actuatorId"] == 1){
                    document.getElementById("command_second_output").value = actuatorStates["state"]
                }
                }
            function sendCommand(event, button_command) {
                command = button_command.split("_")[0]
                const request = JSON.stringify({actuatorId: '0', state: command});
                ws.send(request)
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.on_event("startup")
async def start_background_tasks():
    init_states()
    asyncio.create_task(background_receive_serial(RESPONSE_QUEUE))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    ws_handler = WebSocketHandler(websocket, REQUEST_QUEUE, RESPONSE_QUEUE, WS_CLIENTS)
    await ws_handler.greet_new_client()
    WS_CLIENTS.add(websocket)
    try:
        await asyncio.gather(
            ws_handler.receive_request(),
            ws_handler.process_request(),
            ws_handler.process_response(),
        )
    except WebSocketDisconnect:
        WS_CLIENTS.remove(websocket)
        logger.info(f'WebSocket: client ({websocket}) disconnected.')

