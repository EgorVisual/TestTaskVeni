from typing import Literal, Optional

from pydantic import BaseModel, Field


class GenericResponse(BaseModel):
    status: str = Literal['ok', 'error']
    detail: Optional[str] = None


class ActuatorRequest(BaseModel):
    actuator_id: str = Field(alias='actuatorId')
    state: Literal['open', 'close', 'toggle']

    class Config:
        allow_population_by_field_name = True


class ActuatorResponse(BaseModel):
    actuator_id: str = Field(alias='actuatorId')
    state: Literal['open', 'close', 'closing', 'opening', 'busy']

    class Config:
        allow_population_by_field_name = True


class SerialRequest(BaseModel):
    actuator_id: str = Field(alias='actuatorId')
    state: Literal['open', 'close']

    class Config:
        allow_population_by_field_name = True
