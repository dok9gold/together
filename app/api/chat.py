from fastapi import APIRouter
from app.service.model.chat import ChatRequest, ChatResponse
from app.service.chat import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])

# Service 인스턴스
chat_service = ChatService()


@router.post("", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    채팅 메시지 전송

    AI와 대화하며 요리 관련 질문을 할 수 있습니다.
    """
    return await chat_service.send_message(request)
