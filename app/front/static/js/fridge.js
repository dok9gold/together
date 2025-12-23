// 냉장고 털기 페이지 JS - API 연동

const API_BASE = '/api';

let currentRecipes = [];
let userIngredients = [];

function updateSelected() {
    const selected = Array.from(document.querySelectorAll('input[name="ingredient"]:checked'))
        .map(cb => cb.value);
    const added = Array.from(document.querySelectorAll('.added-tag'))
        .map(tag => tag.textContent.replace(' x', ''));

    userIngredients = [...selected, ...added];
    document.getElementById('selectedDisplay').textContent = userIngredients.length > 0 ? userIngredients.join(', ') : '없음';
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

async function getRecommendation() {
    const selected = Array.from(document.querySelectorAll('input[name="ingredient"]:checked'))
        .map(cb => cb.value);
    const added = Array.from(document.querySelectorAll('.added-tag'))
        .map(tag => tag.textContent.replace(' x', ''));

    userIngredients = [...selected, ...added];

    if (userIngredients.length === 0) {
        alert('재료를 선택하거나 입력해주세요!');
        return;
    }

    try {
        // API 호출
        const response = await fetch(`${API_BASE}/fridge/recommend`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ingredients: userIngredients })
        });

        if (!response.ok) {
            throw new Error('API 호출 실패');
        }

        const data = await response.json();
        currentRecipes = data.recipes;

        renderRecipeCards(currentRecipes, userIngredients);

        document.getElementById('resultSection').hidden = false;
        document.getElementById('resultSection').scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('추천 API 오류:', error);
        alert('추천을 가져오는데 실패했습니다. 다시 시도해주세요.');
    }
}

function renderRecipeCards(recipes, ingredients) {
    const container = document.getElementById('recipeList');

    container.innerHTML = recipes.map(recipe => {
        // 부족한 재료 계산
        const missing = recipe.ingredients.filter(ing => !ingredients.includes(ing));

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

async function addToCart(recipeId) {
    const recipe = currentRecipes.find(r => r.id === recipeId);
    if (!recipe) return;

    // 부족한 재료만 장바구니에 추가
    const missing = recipe.ingredients.filter(ing => !userIngredients.includes(ing));
    const itemsToAdd = missing.length > 0 ? missing : recipe.ingredients;

    try {
        const cartItems = itemsToAdd.map(name => ({ name, quantity: 1 }));
        const response = await fetch(`${API_BASE}/cart/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ items: cartItems })
        });

        if (response.ok) {
            if (missing.length > 0) {
                alert(`부족한 재료(${missing.join(', ')})를 장바구니에 담았습니다!`);
            } else {
                alert(`${recipe.name}의 재료를 장바구니에 담았습니다!`);
            }
        } else {
            throw new Error('장바구니 추가 실패');
        }
    } catch (error) {
        console.error('장바구니 API 오류:', error);
        alert('장바구니 추가에 실패했습니다.');
    }
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
