// 레시피 검색 페이지 JS - API 연동

const API_BASE = '/api/chef';

let currentRecipes = [];

// 페이지 로드 시 인기 검색어 가져오기
document.addEventListener('DOMContentLoaded', loadPopularKeywords);

async function loadPopularKeywords() {
    try {
        const response = await fetch(`${API_BASE}/recipe/popular`);
        if (response.ok) {
            const keywords = await response.json();
            renderPopularKeywords(keywords);
        }
    } catch (error) {
        console.error('인기 검색어 로드 실패:', error);
    }
}

function renderPopularKeywords(keywords) {
    const container = document.querySelector('.popular-tags');
    if (!container) return;

    container.innerHTML = keywords.map(keyword =>
        `<button class="popular-tag" onclick="quickSearch('${keyword}')">${keyword}</button>`
    ).join('');
}

function quickSearch(keyword) {
    document.getElementById('searchInput').value = keyword;
    searchRecipe();
}

async function searchRecipe() {
    const keyword = document.getElementById('searchInput').value.trim();

    if (!keyword) {
        alert('요리명을 입력해주세요!');
        return;
    }

    try {
        // API 호출
        const response = await fetch(`${API_BASE}/recipe/search?keyword=${encodeURIComponent(keyword)}`);

        if (!response.ok) {
            throw new Error('API 호출 실패');
        }

        const data = await response.json();
        currentRecipes = data.recipes;

        if (currentRecipes.length === 0) {
            alert('검색 결과가 없습니다.');
            return;
        }

        renderRecipeCards(currentRecipes);

        document.getElementById('resultSection').hidden = false;
        document.getElementById('resultSection').scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('검색 API 오류:', error);
        alert('검색에 실패했습니다. 다시 시도해주세요.');
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
