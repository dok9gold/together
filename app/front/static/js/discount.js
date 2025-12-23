// 할인상품 추천 페이지 JS

// Mock 데이터 (추후 API로 교체)
const mockRecipes = [
    {
        id: '1',
        name: '삼겹살 김치찌개',
        cookTime: '30분',
        difficulty: '쉬움',
        ingredients: ['삼겹살', '김치', '두부', '대파', '고춧가루'],
        discountInfo: [{ item: '삼겹살', rate: '30%' }, { item: '두부', rate: '1+1' }],
        steps: ['삼겹살을 먹기 좋은 크기로 썬다', '냄비에 삼겹살과 김치를 볶는다', '물을 붓고 끓인다', '두부와 대파를 넣고 마무리한다'],
        relatedItems: ['삼겹살', '두부']
    },
    {
        id: '2',
        name: '비빔밥',
        cookTime: '35분',
        difficulty: '보통',
        ingredients: ['밥', '고추장', '들기름', '나물', '계란'],
        discountInfo: [{ item: '들기름', rate: '50%' }, { item: '고추장', rate: '20%' }],
        steps: ['나물을 각각 볶아 준비한다', '밥 위에 나물을 올린다', '계란 프라이를 올린다', '고추장과 들기름을 넣고 비빈다'],
        relatedItems: ['들기름', '고추장']
    },
    {
        id: '3',
        name: '제육볶음',
        cookTime: '25분',
        difficulty: '쉬움',
        ingredients: ['삼겹살', '고추장', '양파', '대파', '마늘'],
        discountInfo: [{ item: '삼겹살', rate: '30%' }, { item: '고추장', rate: '20%' }],
        steps: ['삼겹살에 고추장 양념을 버무린다', '양파와 대파를 썬다', '팬에 고기를 볶는다', '야채를 넣고 함께 볶아 완성한다'],
        relatedItems: ['삼겹살', '고추장']
    },
    {
        id: '4',
        name: '두부조림',
        cookTime: '20분',
        difficulty: '쉬움',
        ingredients: ['두부', '간장', '고춧가루', '대파', '마늘'],
        discountInfo: [{ item: '두부', rate: '1+1' }],
        steps: ['두부를 도톰하게 썬다', '팬에 두부를 노릇하게 굽는다', '양념장을 만들어 끼얹는다', '대파를 올려 마무리한다'],
        relatedItems: ['두부']
    }
];

let currentRecipes = [];

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
}

function removeItem(btn) {
    btn.parentElement.remove();
}

function getRecommendation() {
    const selected = Array.from(document.querySelectorAll('input[name="discount"]:checked'))
        .map(cb => cb.value);
    const added = Array.from(document.querySelectorAll('.added-tag'))
        .map(tag => tag.textContent.replace(' x', ''));

    const all = [...selected, ...added];

    if (all.length === 0) {
        alert('상품을 선택하거나 입력해주세요!');
        return;
    }

    // 선택한 할인상품과 관련된 레시피 필터링
    currentRecipes = mockRecipes.filter(recipe =>
        recipe.relatedItems.some(item => all.includes(item))
    );

    // 결과가 없으면 전체 레시피 표시
    if (currentRecipes.length === 0) {
        currentRecipes = mockRecipes.slice(0, 2);
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
