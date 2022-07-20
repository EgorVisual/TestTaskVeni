import asyncio

from loguru import logger

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from typing import Set

from .serial_arduino import background_receive_serial
from .states_file import init_states
from .websockethandler import WebSocketHandler

app = FastAPI()

logger.add("./data/logs.log", rotation="50 MB")

WS_CLIENTS: Set[WebSocket] = set()
RESPONSE_QUEUE = asyncio.Queue()
REQUEST_QUEUE = asyncio.Queue()

PREFIX = "CLIENT: "

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Control panel</title>
    </head>
    <body>
        <h1>Control panel</h1>
        You can use this panel to control 2 actuators by buttons (open/close). The first pair of buttons is used for 
        first actuator, the second pair - for the second actuator!
        <div>
        <input id = "command_first_output" value = "Command 1"/>
        <input id = "command_second_output" value = "Command 2"/>
        </div>
        <div> 
        Actuator id - 0   
        <button onclick="sendCommand(event, 'open', 0)" id="open_button_zero">Open</button>
        <button onclick="sendCommand(event, 'close', 0)" id="close_button_zero">Close</button>
        </div>
        <div>  
        Actuator id - 1     
        <button onclick="sendCommand(event, 'open', 1)" id="open_button_first">Open</button>
        <button onclick="sendCommand(event, 'close', 1)" id="close_button_first">Close</button>
        </div>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8080/ws");
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
            function sendCommand(event, button_command, actuator_id) {
                const request = JSON.stringify({actuatorId: actuator_id, state: button_command});
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

