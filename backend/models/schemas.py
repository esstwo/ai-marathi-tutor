from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ChildCreateRequest(BaseModel):
    name: str
    age: int
    avatar: str = "🐘"


# --- Conversation schemas ---


class ConversationMessage(BaseModel):
    role: str  # "child" or "mitra"
    content: str


class ChatRequest(BaseModel):
    child_id: str
    message: str
    conversation_history: list[ConversationMessage] = []


class ChatResponse(BaseModel):
    marathi_text: str
    english_hint: str | None = None


class StartConversationRequest(BaseModel):
    child_id: str


class StartConversationResponse(BaseModel):
    conversation_id: str
    marathi_text: str
    english_hint: str | None = None


class SendMessageRequest(BaseModel):
    message: str


class SendMessageResponse(BaseModel):
    marathi_text: str
    english_hint: str | None = None
