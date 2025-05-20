from pydantic import BaseModel
from typing import List, Dict, Optional

class UserQuery(BaseModel):
    user_input: str

class ConversationRequest(UserQuery):
    conversation_history: Optional[List[Dict[str, str]]] = []