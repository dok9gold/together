from fastapi import APIRouter, Request
from app.service.chef.model.chat import ChatRequest, ChatResponse
from app.service.chef.chat import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def send_message(request: Request, chat_request: ChatRequest):
    """
    채팅 메시지 전송

    AI와 대화하며 요리 관련 질문을 할 수 있습니다.
    """
    # app.state.llm에서 LLMProvider 가져오기
    llm = request.app.state.llm

    # ChatService 인스턴스 생성 (요청마다 생성)
    chat_service = ChatService(llm)

    return await chat_service.send_message(chat_request)
