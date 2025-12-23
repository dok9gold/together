// 레시피 검색 페이지 JS

// Mock 데이터 (추후 API로 교체)
const mockRecipes = {
    '김치찌개': {
        id: '1',
        name: '김치찌개',
        cookTime: '30분',
        difficulty: '쉬움',
        ingredients: ['김치', '돼지고기', '두부', '대파', '고춧가루'],
        discountInfo: [{ item: '돼지고기', rate: '30%' }],
        steps: ['김치를 먹기 좋은 크기로 썬다', '냄비에 참기름을 두르고 김치를 볶는다', '물을 붓고 돼지고기를 넣어 끓인다', '두부와 대파를 넣고 마무리한다']
    },
    '된장찌개': {
        id: '2',
        name: '된장찌개',
        cookTime: '25분',
        difficulty: '쉬움',
        ingredients: ['된장', '두부', '애호박', '감자', '대파'],
        discountInfo: [{ item: '두부', rate: '1+1' }],
        steps: ['감자와 애호박을 깍둑썰기한다', '냄비에 물을 붓고 된장을 푼다', '감자를 먼저 넣고 끓인다', '애호박, 두부, 대파를 넣고 마무리한다']
    },
    '제육볶음': {
        id: '3',
        name: '제육볶음',
        cookTime: '20분',
        difficulty: '보통',
        ingredients: ['돼지고기', '고추장', '양파', '대파', '마늘'],
        discountInfo: [{ item: '돼지고기', rate: '30%' }],
        steps: ['돼지고기에 고추장 양념을 버무린다', '양파와 대파를 썬다', '팬에 기름을 두르고 고기를 볶는다', '야채를 넣고 함께 볶아 완성한다']
    },
    '불고기': {
        id: '4',
        name: '불고기',
        cookTime: '40분',
        difficulty: '보통',
        ingredients: ['소고기', '간장', '배', '양파', '마늘'],
        discountInfo: [{ item: '소고기', rate: '20%' }],
        steps: ['소고기를 얇게 썬다', '간장, 배즙, 마늘로 양념을 만든다', '고기에 양념을 버무려 30분 재운다', '팬에 구워 완성한다']
    },
    '파스타': {
        id: '5',
        name: '파스타',
        cookTime: '25분',
        difficulty: '쉬움',
        ingredients: ['파스타면', '올리브오일', '마늘', '베이컨', '파마산치즈'],
        discountInfo: [{ item: '파스타면', rate: '15%' }],
        steps: ['파스타를 삶는다', '팬에 올리브오일과 마늘을 볶는다', '베이컨을 넣고 볶는다', '삶은 파스타를 넣고 섞어 완성한다']
    }
};

let currentRecipes = [];

function quickSearch(keyword) {
    document.getElementById('searchInput').value = keyword;
    searchRecipe();
}

function searchRecipe() {
    const keyword = document.getElementById('searchInput').value.trim();

    if (!keyword) {
        alert('요리명을 입력해주세요!');
        return;
    }

    // Mock 데이터에서 검색
    currentRecipes = [];

    // 정확히 일치하는 레시피 찾기
    if (mockRecipes[keyword]) {
        currentRecipes.push(mockRecipes[keyword]);
    } else {
        // 부분 일치 검색
        Object.values(mockRecipes).forEach(recipe => {
            if (recipe.name.includes(keyword)) {
                currentRecipes.push(recipe);
            }
        });
    }

    // 검색 결과가 없으면 기본 레시피 생성
    if (currentRecipes.length === 0) {
        currentRecipes.push({
            id: 'default',
            name: keyword,
            cookTime: '30분',
            difficulty: '보통',
            ingredients: ['재료1', '재료2', '재료3'],
            discountInfo: [],
            steps: ['재료를 준비한다', '조리한다', '완성한다']
        });
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

// 엔터키 검색
document.getElementById('searchInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') searchRecipe();
});

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
