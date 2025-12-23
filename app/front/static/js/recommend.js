// 요리 추천 페이지 JS

// Mock 데이터 (추후 API로 교체)
const mockRecipes = {
    '한식': [
        {
            id: '1',
            name: '김치찌개',
            cookTime: '30분',
            difficulty: '쉬움',
            ingredients: ['김치', '돼지고기', '두부', '대파', '고춧가루'],
            discountInfo: [{ item: '돼지고기', rate: '30%' }],
            steps: ['김치를 먹기 좋은 크기로 썬다', '냄비에 참기름을 두르고 김치를 볶는다', '물을 붓고 돼지고기를 넣어 끓인다', '두부와 대파를 넣고 마무리한다']
        },
        {
            id: '2',
            name: '된장찌개',
            cookTime: '25분',
            difficulty: '쉬움',
            ingredients: ['된장', '두부', '애호박', '감자', '대파'],
            discountInfo: [{ item: '두부', rate: '1+1' }],
            steps: ['감자와 애호박을 깍둑썰기한다', '냄비에 물을 붓고 된장을 푼다', '감자를 먼저 넣고 끓인다', '애호박, 두부, 대파를 넣고 마무리한다']
        }
    ],
    '중식': [
        {
            id: '3',
            name: '짜장면',
            cookTime: '40분',
            difficulty: '보통',
            ingredients: ['춘장', '돼지고기', '양파', '감자', '면'],
            discountInfo: [{ item: '춘장', rate: '20%' }],
            steps: ['양파와 감자를 깍둑썰기한다', '돼지고기를 볶다가 춘장을 넣는다', '물을 붓고 끓인다', '삶은 면 위에 소스를 올린다']
        }
    ],
    '일식': [
        {
            id: '4',
            name: '돈카츠',
            cookTime: '35분',
            difficulty: '보통',
            ingredients: ['돼지등심', '빵가루', '계란', '밀가루', '양배추'],
            discountInfo: [{ item: '돼지등심', rate: '25%' }],
            steps: ['돼지등심을 두드려 편다', '밀가루, 계란, 빵가루 순으로 튀김옷을 입힌다', '170도 기름에 바삭하게 튀긴다', '양배추와 함께 플레이팅한다']
        }
    ],
    '양식': [
        {
            id: '5',
            name: '파스타',
            cookTime: '25분',
            difficulty: '쉬움',
            ingredients: ['파스타면', '올리브오일', '마늘', '베이컨', '파마산치즈'],
            discountInfo: [{ item: '파스타면', rate: '15%' }],
            steps: ['파스타를 삶는다', '팬에 올리브오일과 마늘을 볶는다', '베이컨을 넣고 볶는다', '삶은 파스타를 넣고 섞어 완성한다']
        }
    ]
};

let currentRecipes = [];

function getRecommendation() {
    const categories = Array.from(document.querySelectorAll('input[name="category"]:checked'))
        .map(cb => cb.value);
    const condition = document.getElementById('conditionInput').value.trim();

    if (categories.length === 0 && !condition) {
        alert('카테고리를 선택하거나 조건을 입력해주세요!');
        return;
    }

    // Mock 데이터에서 레시피 가져오기
    currentRecipes = [];
    if (categories.length > 0) {
        categories.forEach(cat => {
            if (mockRecipes[cat]) {
                currentRecipes.push(...mockRecipes[cat]);
            }
        });
    } else {
        // 조건만 있을 경우 기본 추천
        currentRecipes = mockRecipes['한식'];
    }

    renderRecipeCards(currentRecipes);

    document.getElementById('resultSection').hidden = false;
    document.getElementById('resultSection').scrollIntoView({ behavior: 'smooth' });
}

function renderRecipeCards(recipes) {
    const container = document.getElementById('recipeList');

    container.innerHTML = recipes.map(recipe => `
        <div class="recipe-card" data-id="${recipe.id}">
            <div class="recipe-card-header">
                <h3>${recipe.name}</h3>
                <div class="recipe-card-actions">
                    <button class="btn-recipe" onclick="showRecipeModal('${recipe.id}')">레시피</button>
                    <button class="btn-cart" onclick="addToCart('${recipe.id}')">담기</button>
                </div>
            </div>
            <p class="recipe-card-ingredients">재료: ${recipe.ingredients.join(', ')}</p>
            ${recipe.discountInfo && recipe.discountInfo.length > 0
                ? `<span class="recipe-card-discount">${recipe.discountInfo.map(d => `${d.item} ${d.rate} 할인`).join(', ')}</span>`
                : ''}
        </div>
    `).join('');
}

function showRecipeModal(recipeId) {
    const recipe = currentRecipes.find(r => r.id === recipeId);
    if (!recipe) return;

    document.getElementById('modalTitle').textContent = recipe.name;
    document.getElementById('modalTime').textContent = `조리시간: ${recipe.cookTime}`;
    document.getElementById('modalDifficulty').textContent = `난이도: ${recipe.difficulty}`;
    document.getElementById('modalIngredients').innerHTML = recipe.ingredients.map(i => `<li>${i}</li>`).join('');
    document.getElementById('modalSteps').innerHTML = recipe.steps.map(s => `<li>${s}</li>`).join('');

    document.getElementById('recipeModal').classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    document.getElementById('recipeModal').classList.remove('show');
    document.body.style.overflow = '';
}

function addToCart(recipeId) {
    const recipe = currentRecipes.find(r => r.id === recipeId);
    if (!recipe) return;

    alert(`${recipe.name}의 재료를 장바구니에 담았습니다!`);
}

// 모달 바깥 클릭 시 닫기
document.getElementById('recipeModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeModal();
    }
});

// ESC 키로 모달 닫기
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeModal();
    }
});
