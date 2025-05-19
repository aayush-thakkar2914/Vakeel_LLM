from pydantic import BaseModel

class UserQuery(BaseModel):
    user_input: str
