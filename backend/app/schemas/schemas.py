from pydantic import BaseModel, Field

class AuthIn(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=128)
class WatchlistCreate(BaseModel): name: str = Field(min_length=1,max_length=100); is_default: bool=False
class GroupCreate(BaseModel): name: str=Field(min_length=1,max_length=100); type: str="CUSTOM"
class GroupMove(BaseModel): group_id: int
class StockAdd(BaseModel): symbol: str; group_id: int|None=None
class NoteUpdate(BaseModel): note: str|None=None
class PreferenceUpdate(BaseModel): styles: list[str]
class AlertCreate(BaseModel): symbol: str; alert_type: str; threshold: float
