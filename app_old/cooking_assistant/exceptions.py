"""Domain Exceptions - 도메인 계층 예외 정의

비즈니스 규칙 위반 및 도메인 오류를 나타내는 예외들입니다.
"""
from typing import Optional, Dict, Any


class DomainException(Exception):
    """도메인 예외 베이스 클래스

    모든 도메인 예외의 부모 클래스입니다.

    Attributes:
        message: 에러 메시지
        code: 에러 코드 (선택)
        details: 추가 상세 정보 (선택)
    """

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """문자열 표현"""
        if self.details:
            return f"{self.code}: {self.message} (details: {self.details})"
        return f"{self.code}: {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환 (API 응답용)"""
        return {
            "error_type": self.__class__.__name__,
            "code": self.code,
            "message": self.message,
            "details": self.details
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 비즈니스 로직 예외
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ValidationError(DomainException):
    """검증 실패 예외

    도메인 엔티티나 값 객체의 유효성 검증 실패 시 발생합니다.

    Example:
        >>> raise ValidationError(
        ...     "레시피 재료가 비어있습니다",
        ...     code="EMPTY_INGREDIENTS",
        ...     details={"field": "ingredients"}
        ... )
    """
    pass


class RecipeValidationError(ValidationError):
    """레시피 검증 실패 예외

    레시피의 비즈니스 규칙 위반 시 발생합니다.

    Example:
        >>> raise RecipeValidationError(
        ...     "난이도는 '쉬움', '중간', '어려움' 중 하나여야 합니다",
        ...     code="INVALID_DIFFICULTY",
        ...     details={"difficulty": "매우 어려움"}
        ... )
    """
    pass


class IntentClassificationError(DomainException):
    """의도 분류 실패 예외

    사용자 쿼리의 의도 분류에 실패했을 때 발생합니다.

    Example:
        >>> raise IntentClassificationError(
        ...     "의도 분류 신뢰도가 너무 낮습니다",
        ...     code="LOW_CONFIDENCE",
        ...     details={"confidence": 0.3, "threshold": 0.5}
        ... )
    """
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 외부 시스템 연동 예외
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ExternalServiceError(DomainException):
    """외부 서비스 오류 베이스 클래스

    LLM, 이미지 생성 등 외부 서비스 호출 실패 시 발생합니다.
    """
    pass


class LLMServiceError(ExternalServiceError):
    """LLM 서비스 오류

    Anthropic, OpenAI 등 LLM API 호출 실패 시 발생합니다.

    Example:
        >>> raise LLMServiceError(
        ...     "LLM API 타임아웃",
        ...     code="LLM_TIMEOUT",
        ...     details={"provider": "anthropic", "timeout": 90}
        ... )
    """
    pass


class ImageGenerationError(ExternalServiceError):
    """이미지 생성 오류

    Replicate, DALLE 등 이미지 생성 API 호출 실패 시 발생합니다.

    Example:
        >>> raise ImageGenerationError(
        ...     "이미지 생성 실패",
        ...     code="IMAGE_GEN_FAILED",
        ...     details={"provider": "replicate", "model": "flux-schnell"}
        ... )
    """
    pass


class VectorStoreError(ExternalServiceError):
    """벡터 DB 오류 (향후 RAG용)

    ChromaDB, Pinecone 등 벡터 DB 연동 실패 시 발생합니다.

    Example:
        >>> raise VectorStoreError(
        ...     "벡터 검색 실패",
        ...     code="VECTOR_SEARCH_FAILED",
        ...     details={"collection": "recipes", "query": "김치찌개"}
        ... )
    """
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 워크플로우 예외
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class WorkflowError(DomainException):
    """워크플로우 실행 오류

    LangGraph 워크플로우 실행 중 오류 발생 시 사용합니다.

    Example:
        >>> raise WorkflowError(
        ...     "노드 실행 실패",
        ...     code="NODE_EXECUTION_FAILED",
        ...     details={"node": "recipe_generator", "state": {...}}
        ... )
    """
    pass


class NodeExecutionError(WorkflowError):
    """노드 실행 오류

    특정 워크플로우 노드 실행 실패 시 발생합니다.

    Example:
        >>> raise NodeExecutionError(
        ...     "레시피 생성 노드 실패",
        ...     code="RECIPE_NODE_FAILED",
        ...     details={"node": "recipe_generator", "reason": "LLM timeout"}
        ... )
    """
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 데이터 파싱 예외
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ParsingError(DomainException):
    """데이터 파싱 오류

    JSON 파싱, LLM 응답 파싱 실패 시 발생합니다.

    Example:
        >>> raise ParsingError(
        ...     "JSON 파싱 실패",
        ...     code="JSON_PARSE_ERROR",
        ...     details={"raw_content": "invalid json..."}
        ... )
    """
    pass


class LLMResponseParsingError(ParsingError):
    """LLM 응답 파싱 오류

    LLM 응답을 JSON으로 파싱하는 데 실패했을 때 발생합니다.

    Example:
        >>> raise LLMResponseParsingError(
        ...     "LLM 응답이 유효한 JSON이 아닙니다",
        ...     code="INVALID_JSON_RESPONSE",
        ...     details={"response": "...", "error": "Expecting value"}
        ... )
    """
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 설정 오류
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ConfigurationError(DomainException):
    """설정 오류

    환경 변수, 설정 파일 등의 오류 발생 시 사용합니다.

    Example:
        >>> raise ConfigurationError(
        ...     "API 키가 설정되지 않았습니다",
        ...     code="MISSING_API_KEY",
        ...     details={"env_var": "ANTHROPIC_API_KEY"}
        ... )
    """
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 리소스 예외
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ResourceNotFoundError(DomainException):
    """리소스 미발견 오류

    요청한 리소스를 찾을 수 없을 때 발생합니다.

    Example:
        >>> raise ResourceNotFoundError(
        ...     "레시피를 찾을 수 없습니다",
        ...     code="RECIPE_NOT_FOUND",
        ...     details={"recipe_id": 123}
        ... )
    """
    pass


class RateLimitExceededError(DomainException):
    """속도 제한 초과 오류

    API 호출 제한을 초과했을 때 발생합니다.

    Example:
        >>> raise RateLimitExceededError(
        ...     "API 호출 제한 초과",
        ...     code="RATE_LIMIT_EXCEEDED",
        ...     details={"limit": 100, "window": "1m"}
        ... )
    """
    pass
