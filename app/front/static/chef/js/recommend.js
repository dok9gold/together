// 요리 추천 페이지 JS - API 연동

const API_BASE = '/api/chef';

let currentRecipes = [];

async function getRecommendation() {
    const categories = Array.from(document.querySelectorAll('input[name="category"]:checked'))
        .map(cb => cb.value);
    const condition = document.getElementById('conditionInput').value.trim();

    if (categories.length === 0 && !condition) {
        alert('카테고리를 선택하거나 조건을 입력해주세요!');
        return;
    }

    try {
        // API 호출
        const response = await fetch(`${API_BASE}/recommend`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                categories: categories.length > 0 ? categories : ['한식'],
                condition: condition || null
            })
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
