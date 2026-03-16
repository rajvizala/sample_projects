from pydantic import BaseModel, Field


class SignalCreate(BaseModel):
    channel: str = Field(min_length=3, max_length=40)
    sender: str = Field(min_length=2, max_length=120)
    content: str = Field(min_length=4, max_length=600)
    country: str = Field(min_length=2, max_length=40)
    hour: int = Field(ge=0, le=23)
    amount: float = Field(default=0.0, ge=0)
    new_device: bool = False
    new_ip: bool = False
    ai_voice_flag: bool = False
