// 할인상품 추천 페이지 JS - API 연동

const API_BASE = '/api/chef';

let currentRecipes = [];

// 페이지 로드 시 오늘의 할인상품 가져오기
document.addEventListener('DOMContentLoaded', loadTodayDiscounts);

async function loadTodayDiscounts() {
    try {
        const response = await fetch(`${API_BASE}/discount/today`);
        if (response.ok) {
            const discounts = await response.json();
            renderDiscountItems(discounts);
        }
    } catch (error) {
        console.error('할인상품 로드 실패:', error);
    }
}

function renderDiscountItems(discounts) {
    // 할인상품 그리드 업데이트
    const grid = document.querySelector('.discount-grid');
    if (grid) {
        grid.innerHTML = discounts.map(item => `
            <div class="discount-item">
                <span class="discount-badge">${item.discountRate}</span>
                <span class="discount-name">${item.name}</span>
            </div>
        `).join('');
    }

    // 체크박스 그룹 업데이트
    const checkboxGroup = document.querySelector('.checkbox-group');
    if (checkboxGroup) {
        checkboxGroup.innerHTML = discounts.map(item => `
            <label class="checkbox-item">
                <input type="checkbox" name="discount" value="${item.name}">
                <span class="checkbox-label">${item.name}</span>
            </label>
        `).join('');
    }
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
}

function removeItem(btn) {
    btn.parentElement.remove();
}

async function getRecommendation() {
    const selected = Array.from(document.querySelectorAll('input[name="discount"]:checked'))
        .map(cb => cb.value);
    const added = Array.from(document.querySelectorAll('.added-tag'))
        .map(tag => tag.textContent.replace(' x', ''));

    const all = [...selected, ...added];

    if (all.length === 0) {
        alert('상품을 선택하거나 입력해주세요!');
        return;
    }

    try {
        // API 호출
        const response = await fetch(`${API_BASE}/discount/recommend`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ items: all })
        });

        if (!response.ok) {
            throw new Error('API 호출 실패');
        }

        const data = await response.json();
        currentRecipes = data.recipes;

        renderRecipeCards(currentRecipes);

        document.getElementById('resultSection').hidden = false;
        document.getElementById('resultSection').scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('추천 API 오류:', error);
        alert('추천을 가져오는데 실패했습니다. 다시 시도해주세요.');
    }
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

async function addToCart(recipeId) {
    const recipe = currentRecipes.find(r => r.id === recipeId);
    if (!recipe) return;

    try {
        const cartItems = recipe.ingredients.map(name => ({ name, quantity: 1 }));
        const response = await fetch(`${API_BASE}/cart/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ items: cartItems })
        });

        if (response.ok) {
            alert(`${recipe.name}의 재료를 장바구니에 담았습니다!`);
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
