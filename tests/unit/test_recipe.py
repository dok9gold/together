"""Recipe Entity 단위 테스트

Recipe 엔티티의 비즈니스 로직과 검증 규칙을 테스트합니다.
"""
import pytest
from app.domain.entities.recipe import Recipe
from app.domain.exceptions import RecipeValidationError


class TestRecipeCreation:
    """Recipe 생성 테스트"""

    def test_create_valid_recipe(self):
        """유효한 레시피 생성"""
        # Given
        title = "김치찌개"
        ingredients = ["김치 300g", "돼지고기 200g", "두부 1/2모"]
        steps = ["1. 김치를 썬다", "2. 고기를 볶는다", "3. 물을 넣고 끓인다"]
        cooking_time = "30분"
        difficulty = "쉬움"

        # When
        recipe = Recipe(
            title=title,
            ingredients=ingredients,
            steps=steps,
            cooking_time=cooking_time,
            difficulty=difficulty
        )

        # Then
        assert recipe.title == title
        assert recipe.ingredients == ingredients
        assert recipe.steps == steps
        assert recipe.cooking_time == cooking_time
        assert recipe.difficulty == difficulty

    def test_recipe_validation_success(self):
        """정상 레시피 검증 성공"""
        # Given
        recipe = Recipe(
            title="파스타",
            ingredients=["면 100g", "올리브 오일"],
            steps=["1. 면을 삶는다"],
            cooking_time="15분",
            difficulty="중간"
        )

        # When / Then (예외 발생하지 않아야 함)
        recipe.validate()


class TestRecipeValidation:
    """Recipe 검증 테스트"""

    def test_validate_empty_title(self):
        """빈 제목 검증 실패"""
        # Given
        recipe = Recipe(
            title="",
            ingredients=["김치"],
            steps=["1. 끓인다"],
            cooking_time="30분",
            difficulty="쉬움"
        )

        # When / Then
        with pytest.raises(RecipeValidationError) as exc_info:
            recipe.validate()

        assert exc_info.value.code == "INVALID_TITLE"
        assert "2글자 이상" in exc_info.value.message
        assert exc_info.value.details["title"] == ""

    def test_validate_short_title(self):
        """짧은 제목 검증 실패"""
        # Given
        recipe = Recipe(
            title="김",
            ingredients=["김치"],
            steps=["1. 끓인다"],
            cooking_time="30분",
            difficulty="쉬움"
        )

        # When / Then
        with pytest.raises(RecipeValidationError) as exc_info:
            recipe.validate()

        assert exc_info.value.code == "INVALID_TITLE"

    def test_validate_empty_ingredients(self):
        """빈 재료 목록 검증 실패"""
        # Given
        recipe = Recipe(
            title="김치찌개",
            ingredients=[],
            steps=["1. 끓인다"],
            cooking_time="30분",
            difficulty="쉬움"
        )

        # When / Then
        with pytest.raises(RecipeValidationError) as exc_info:
            recipe.validate()

        assert exc_info.value.code == "EMPTY_INGREDIENTS"
        assert "최소 1개 이상" in exc_info.value.message
        assert exc_info.value.details["ingredients_count"] == 0

    def test_validate_empty_steps(self):
        """빈 조리 단계 검증 실패"""
        # Given
        recipe = Recipe(
            title="김치찌개",
            ingredients=["김치"],
            steps=[],
            cooking_time="30분",
            difficulty="쉬움"
        )

        # When / Then
        with pytest.raises(RecipeValidationError) as exc_info:
            recipe.validate()

        assert exc_info.value.code == "EMPTY_STEPS"
        assert exc_info.value.details["steps_count"] == 0

    def test_validate_invalid_difficulty(self):
        """잘못된 난이도 검증 실패"""
        # Given
        recipe = Recipe(
            title="김치찌개",
            ingredients=["김치"],
            steps=["1. 끓인다"],
            cooking_time="30분",
            difficulty="매우어려움"  # 잘못된 난이도
        )

        # When / Then
        with pytest.raises(RecipeValidationError) as exc_info:
            recipe.validate()

        assert exc_info.value.code == "INVALID_DIFFICULTY"
        assert "매우어려움" in str(exc_info.value.details["difficulty"])
        assert "쉬움" in exc_info.value.message
        assert "중간" in exc_info.value.message
        assert "어려움" in exc_info.value.message

    @pytest.mark.parametrize(
        "difficulty",
        ["쉬움", "중간", "어려움"]
    )
    def test_validate_valid_difficulties(self, difficulty):
        """유효한 난이도들 검증 성공"""
        # Given
        recipe = Recipe(
            title="테스트 레시피",
            ingredients=["재료1"],
            steps=["1. 조리"],
            cooking_time="10분",
            difficulty=difficulty
        )

        # When / Then (예외 발생하지 않아야 함)
        recipe.validate()


class TestRecipeMethods:
    """Recipe 메서드 테스트"""

    def test_get_total_steps(self):
        """조리 단계 개수 반환"""
        # Given
        recipe = Recipe(
            title="파스타",
            ingredients=["면"],
            steps=["1. 끓이기", "2. 볶기", "3. 플레이팅"],
            cooking_time="20분",
            difficulty="중간"
        )

        # When
        total_steps = recipe.get_total_steps()

        # Then
        assert total_steps == 3

    def test_get_ingredient_count(self):
        """재료 개수 반환"""
        # Given
        recipe = Recipe(
            title="파스타",
            ingredients=["면 100g", "올리브오일", "마늘", "페퍼론치노"],
            steps=["1. 조리"],
            cooking_time="20분",
            difficulty="중간"
        )

        # When
        ingredient_count = recipe.get_ingredient_count()

        # Then
        assert ingredient_count == 4

    def test_get_total_steps_empty(self):
        """빈 조리 단계 개수"""
        # Given
        recipe = Recipe(
            title="파스타",
            ingredients=["면"],
            steps=[],
            cooking_time="20분",
            difficulty="중간"
        )

        # When
        total_steps = recipe.get_total_steps()

        # Then
        assert total_steps == 0


class TestRecipeExceptionDetails:
    """Recipe 예외 상세 정보 테스트"""

    def test_exception_to_dict(self):
        """예외의 딕셔너리 변환"""
        # Given
        recipe = Recipe(
            title="",
            ingredients=["김치"],
            steps=["1. 조리"],
            cooking_time="30분",
            difficulty="쉬움"
        )

        # When
        try:
            recipe.validate()
            pytest.fail("RecipeValidationError가 발생해야 합니다")
        except RecipeValidationError as e:
            error_dict = e.to_dict()

        # Then
        assert error_dict["error_type"] == "RecipeValidationError"
        assert error_dict["code"] == "INVALID_TITLE"
        assert "message" in error_dict
        assert "details" in error_dict
        assert error_dict["details"]["title"] == ""

    def test_exception_str_representation(self):
        """예외의 문자열 표현"""
        # Given
        recipe = Recipe(
            title="김치찌개",
            ingredients=[],
            steps=["1. 조리"],
            cooking_time="30분",
            difficulty="쉬움"
        )

        # When
        try:
            recipe.validate()
            pytest.fail("RecipeValidationError가 발생해야 합니다")
        except RecipeValidationError as e:
            error_str = str(e)

        # Then
        assert "EMPTY_INGREDIENTS" in error_str
        assert "최소 1개 이상" in error_str
        assert "ingredients_count" in error_str


class TestRecipeEdgeCases:
    """Recipe 엣지 케이스 테스트"""

    def test_recipe_with_minimum_valid_data(self):
        """최소한의 유효한 데이터로 레시피 생성"""
        # Given
        recipe = Recipe(
            title="최소",  # 2글자 (최소)
            ingredients=["재료"],  # 1개
            steps=["조리"],  # 1개
            cooking_time="1분",
            difficulty="쉬움"
        )

        # When / Then
        recipe.validate()  # 성공해야 함

    def test_recipe_with_very_long_title(self):
        """매우 긴 제목"""
        # Given
        long_title = "김" * 100
        recipe = Recipe(
            title=long_title,
            ingredients=["재료"],
            steps=["조리"],
            cooking_time="10분",
            difficulty="쉬움"
        )

        # When / Then
        recipe.validate()  # 성공해야 함 (최대 길이 제한 없음)
        assert len(recipe.title) == 100

    def test_recipe_with_many_ingredients(self):
        """많은 재료"""
        # Given
        many_ingredients = [f"재료{i}" for i in range(50)]
        recipe = Recipe(
            title="복잡한 요리",
            ingredients=many_ingredients,
            steps=["조리"],
            cooking_time="120분",
            difficulty="어려움"
        )

        # When / Then
        recipe.validate()
        assert recipe.get_ingredient_count() == 50
