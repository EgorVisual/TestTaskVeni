import json

from loguru import logger
from typing import Dict

DEFAULT_STATES: Dict[str, str] = {
    "0": "CLOSE",
    "1": "CLOSE",
}

STATES_FILE = "./my_test_app/data/states.json"
PREFIX = "JSON: "


def init_states():
    try:
        with open(STATES_FILE, 'r') as file:
            json.load(file)
        logger.info(f'{PREFIX} Successfully read init states: {STATES_FILE}')
    except:
        with open(STATES_FILE, 'w') as file:
            json.dump(DEFAULT_STATES, file, indent=4)
            logger.info(f'{PREFIX} Empty json file were created: {STATES_FILE}')


def read_states() -> Dict[str, str]:
    with open(STATES_FILE, 'r') as file:
        try:
            states = json.load(file)
            logger.info(f'{PREFIX} Successfully read states: {states} from {STATES_FILE}')
            return states
        except Exception as e:
            logger.error(f"{PREFIX} Some wrong with states file: {e}")
        return {}


def write_states(states: Dict[str, str]) -> None:
    with open(STATES_FILE, 'w') as file:
        json.dump(states, file, indent=4)
