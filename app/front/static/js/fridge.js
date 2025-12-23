// 냉장고 털기 페이지 JS

// Mock 데이터 (추후 API로 교체)
const mockRecipes = [
    {
        id: '1',
        name: '김치찌개',
        cookTime: '30분',
        difficulty: '쉬움',
        ingredients: ['삼겹살', '김치', '두부', '대파', '고춧가루'],
        discountInfo: [{ item: '삼겹살', rate: '30%' }],
        steps: ['삼겹살을 먹기 좋은 크기로 썬다', '냄비에 삼겹살과 김치를 볶는다', '물을 붓고 끓인다', '두부와 대파를 넣고 마무리한다'],
        requiredIngredients: ['김치', '삼겹살']
    },
    {
        id: '2',
        name: '계란말이',
        cookTime: '15분',
        difficulty: '쉬움',
        ingredients: ['계란', '대파', '당근', '소금'],
        discountInfo: [],
        steps: ['계란을 풀어 소금 간을 한다', '대파와 당근을 잘게 썬다', '팬에 기름을 두르고 계란물을 붓는다', '돌돌 말아가며 익힌다'],
        requiredIngredients: ['계란']
    },
    {
        id: '3',
        name: '제육볶음',
        cookTime: '25분',
        difficulty: '쉬움',
        ingredients: ['삼겹살', '고추장', '양파', '대파', '마늘'],
        discountInfo: [{ item: '고추장', rate: '20%' }],
        steps: ['삼겹살에 고추장 양념을 버무린다', '양파와 대파를 썬다', '팬에 고기를 볶는다', '야채를 넣고 함께 볶아 완성한다'],
        requiredIngredients: ['삼겹살', '양파']
    },
    {
        id: '4',
        name: '두부조림',
        cookTime: '20분',
        difficulty: '쉬움',
        ingredients: ['두부', '간장', '고춧가루', '대파', '마늘'],
        discountInfo: [{ item: '두부', rate: '1+1' }],
        steps: ['두부를 도톰하게 썬다', '팬에 두부를 노릇하게 굽는다', '양념장을 만들어 끼얹는다', '대파를 올려 마무리한다'],
        requiredIngredients: ['두부']
    },
    {
        id: '5',
        name: '김치볶음밥',
        cookTime: '15분',
        difficulty: '쉬움',
        ingredients: ['밥', '김치', '계란', '대파', '참기름'],
        discountInfo: [],
        steps: ['김치를 잘게 썬다', '팬에 김치를 볶는다', '밥을 넣고 함께 볶는다', '계란 프라이를 올려 완성한다'],
        requiredIngredients: ['김치', '계란']
    }
];

let currentRecipes = [];

function updateSelected() {
    const selected = Array.from(document.querySelectorAll('input[name="ingredient"]:checked'))
        .map(cb => cb.value);
    const added = Array.from(document.querySelectorAll('.added-tag'))
        .map(tag => tag.textContent.replace(' x', ''));

    const all = [...selected, ...added];
    document.getElementById('selectedDisplay').textContent = all.length > 0 ? all.join(', ') : '없음';
}

function addItem() {
    const input = document.getElementById('addInput');
    const value = input.value.trim();
    if (!value) return;

    const container = document.getElementById('addedItems');
    const tag = document.createElement('span');
    tag.className = 'added-tag';
    tag.innerHTML = `${value} <button onclick="removeItem(this)">x</button>`;
    container.appendChild(tag);
    input.value = '';
    updateSelected();
}

function removeItem(btn) {
    btn.parentElement.remove();
    updateSelected();
}

function getRecommendation() {
    const selected = Array.from(document.querySelectorAll('input[name="ingredient"]:checked'))
        .map(cb => cb.value);
    const added = Array.from(document.querySelectorAll('.added-tag'))
        .map(tag => tag.textContent.replace(' x', ''));

    const all = [...selected, ...added];

    if (all.length === 0) {
        alert('재료를 선택하거나 입력해주세요!');
        return;
    }

    // 선택한 재료로 만들 수 있는 레시피 필터링
    currentRecipes = mockRecipes.filter(recipe =>
        recipe.requiredIngredients.some(req => all.includes(req))
    );

    // 결과가 없으면 전체 레시피 중 일부 표시
    if (currentRecipes.length === 0) {
        currentRecipes = mockRecipes.slice(0, 2);
    }

    renderRecipeCards(currentRecipes, all);

    document.getElementById('resultSection').hidden = false;
    document.getElementById('resultSection').scrollIntoView({ behavior: 'smooth' });
}

function renderRecipeCards(recipes, userIngredients) {
    const container = document.getElementById('recipeList');

    container.innerHTML = recipes.map(recipe => {
        // 부족한 재료 계산
        const missing = recipe.ingredients.filter(ing => !userIngredients.includes(ing));

        return `
            <div class="recipe-card" data-id="${recipe.id}">
                <div class="recipe-card-header">
                    <h3>${recipe.name}</h3>
                    <div class="recipe-card-actions">
                        <button class="btn-recipe" onclick="showRecipeModal('${recipe.id}')">레시피</button>
                        <button class="btn-cart" onclick="addToCart('${recipe.id}')">담기</button>
                    </div>
                </div>
                <p class="recipe-card-ingredients">재료: ${recipe.ingredients.join(', ')}</p>
                ${missing.length > 0
                    ? `<p class="recipe-card-missing">부족한 재료: ${missing.join(', ')}</p>`
                    : '<p class="recipe-card-complete">모든 재료가 있어요!</p>'}
                ${recipe.discountInfo && recipe.discountInfo.length > 0
                    ? `<span class="recipe-card-discount">${recipe.discountInfo.map(d => `${d.item} ${d.rate} 할인`).join(', ')}</span>`
                    : ''}
            </div>
        `;
    }).join('');
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

// 엔터키로 추가
document.getElementById('addInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') addItem();
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
