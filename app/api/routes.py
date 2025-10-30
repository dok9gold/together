import json
from fastapi import APIRouter, HTTPException
from app.models.schemas import CookingRequest, CookingResponse
from app.services.cooking_assistant import CookingAssistant

router = APIRouter()
cooking_assistant = CookingAssistant()


@router.post("/cooking", response_model=CookingResponse)
async def handle_cooking_query(request: CookingRequest):
    """
    요리 AI 어시스턴트 API

    사용자 쿼리의 의도를 파악하여 적절한 응답을 생성합니다:
    - 레시피 생성: 상세한 조리법과 이미지
    - 음식 추천: 맞춤형 메뉴 제안
    - 질문 답변: 요리 관련 정보 제공

    - **query**: 요리 관련 쿼리
        - 예: "파스타 카르보나라 만드는 법" (레시피 생성)
        - 예: "매운 음식 추천해줘" (음식 추천)
        - 예: "김치찌개 칼로리는?" (질문 답변)
    """
    try:
        # 요리 AI 어시스턴트 워크플로우 실행
        result = await cooking_assistant.run(request.query)

        # 에러 처리
        if result.get("error"):
            return CookingResponse(
                status="error",
                intent=result.get("primary_intent", "recipe_create"),
                message=result["error"],
                data=None
            )

        # 복합 의도 응답 구성 (primary + secondary 결과 모두 포함)
        intent = result.get("primary_intent", "recipe_create")
        response_data = {}

        # 엔티티 및 메타데이터 추가 (디버깅 및 투명성)
        response_data["metadata"] = {
            "entities": result.get("entities", {}),
            "confidence": result.get("confidence", 0.0),
            "secondary_intents_processed": result.get("secondary_intents", [])
        }

        # 각 의도의 결과를 순서대로 response_data에 추가
        # 1. 추천 결과 (있으면 추가)
        if result.get("recommendation"):
            try:
                recommendation_data = json.loads(result["recommendation"])
                recommendations = recommendation_data.get("recommendations", [])

                # LLM이 추가한 불필요한 필드 제거 (name, description, reason만 유지)
                cleaned_recommendations = []
                for rec in recommendations:
                    cleaned_rec = {
                        "name": rec.get("name", ""),
                        "description": rec.get("description", ""),
                        "reason": rec.get("reason", "")
                    }
                    cleaned_recommendations.append(cleaned_rec)

                response_data["recommendations"] = cleaned_recommendations
            except json.JSONDecodeError as e:
                print(f"[DEBUG] 추천 파싱 실패: {e}")
                print(f"[DEBUG] result['recommendation'][:500]: {result['recommendation'][:500]}")
                # 추천 파싱 실패해도 다른 결과는 반환
                response_data["recommendations_error"] = f"추천 파싱 실패: {str(e)}"

        # 2. 레시피 결과 (있으면 추가)
        if result.get("recipe_text"):
            try:
                recipe_data = json.loads(result["recipe_text"])

                # 단일 레시피 vs 복수 레시피 분기
                if isinstance(recipe_data, list):
                    # 복수 레시피 (배열 형식)
                    response_data["recipes"] = recipe_data
                elif isinstance(recipe_data, dict):
                    # 단일 레시피 (딕셔너리 형식)
                    response_data["recipe"] = recipe_data

                response_data["image_url"] = result.get("image_url")
            except json.JSONDecodeError as e:
                print(f"[DEBUG] 레시피 파싱 실패: {e}")
                # 레시피 파싱 실패해도 다른 결과는 반환
                response_data["recipe_error"] = f"레시피 파싱 실패: {str(e)}"

        # 3. 질문 답변 (있으면 추가)
        if result.get("answer"):
            try:
                answer_data = json.loads(result["answer"])
                response_data["answer"] = answer_data.get("answer", "")
                response_data["additional_tips"] = answer_data.get("additional_tips", [])
            except json.JSONDecodeError as e:
                print(f"[DEBUG] 답변 파싱 실패: {e}")
                # 답변 파싱 실패해도 다른 결과는 반환
                response_data["answer_error"] = f"답변 파싱 실패: {str(e)}"

        # response_data가 비어있거나 metadata만 있으면 에러
        # metadata 제외하고 실제 결과 데이터가 있는지 확인
        result_keys = [k for k in response_data.keys() if k != "metadata"]
        if not result_keys or all(k.endswith("_error") for k in result_keys):
            return CookingResponse(
                status="error",
                intent=intent,
                message="모든 결과 파싱 실패",
                data=None
            )

        return CookingResponse(
            status="success",
            intent=intent,
            data=response_data,
            message="이미지 생성 실패" if intent == "recipe_create" and not result.get("image_url") else None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")


@router.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "service": "cooking-assistant"}