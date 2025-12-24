// 채팅 페이지 JS - API 연동

const API_BASE = '/api';

const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');

let currentRecipes = [];

// 텍스트 영역 자동 높이 조절
userInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

// 엔터키로 전송 (Shift+Enter는 줄바꿈)
userInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// 메시지 전송
async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    // 사용자 메시지 추가
    addMessageToDOM(message, 'user');
    userInput.value = '';
    userInput.style.height = 'auto';

    // 버튼 비활성화
    sendBtn.disabled = true;

    // 타이핑 인디케이터 표시
    showTypingIndicator();

    try {
        // API 호출
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });

        if (!response.ok) {
            throw new Error('API 호출 실패');
        }

        const data = await response.json();

        // 타이핑 인디케이터 제거
        hideTypingIndicator();

        // 레시피가 있으면 저장
        if (data.recipes && data.recipes.length > 0) {
            currentRecipes = [...currentRecipes, ...data.recipes];
        }

        // AI 응답 추가
        addMessageToDOM(data.content, 'ai', data.recipes);
    } catch (error) {
        console.error('채팅 API 오류:', error);
        hideTypingIndicator();
        addMessageToDOM('죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.', 'ai');
    }

    // 버튼 활성화
    sendBtn.disabled = false;
}

// DOM에 메시지 추가
function addMessageToDOM(content, type, recipes = null) {
    // 텍스트 메시지 추가
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.innerHTML = `<div class="message-content">${formatMessage(content)}</div>`;
    chatMessages.appendChild(messageDiv);

    // 레시피 카드가 있으면 별도 영역으로 추가
    if (recipes && recipes.length > 0) {
        const recipeListDiv = document.createElement('div');
        recipeListDiv.className = 'chat-recipe-list';
        recipeListDiv.innerHTML = recipes.map(recipe => renderRecipeCard(recipe)).join('');
        chatMessages.appendChild(recipeListDiv);
    }

    scrollToBottom();
}

// 레시피 카드 렌더링 (다른 페이지와 동일한 구조)
function renderRecipeCard(recipe) {
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
            ${recipe.discountInfo && recipe.discountInfo.length > 0
                ? `<span class="recipe-card-discount">${recipe.discountInfo.map(d => `${d.item} ${d.rate} 할인`).join(', ')}</span>`
                : ''}
        </div>
    `;
}

// 메시지 포맷팅 (줄바꿈 처리)
function formatMessage(text) {
    return text.replace(/\n/g, '<br>');
}

// 스크롤 맨 아래로
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 타이핑 인디케이터 표시
function showTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'message ai';
    indicator.id = 'typingIndicator';
    indicator.innerHTML = `
        <div class="message-content typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    chatMessages.appendChild(indicator);
    scrollToBottom();
}

// 타이핑 인디케이터 제거
function hideTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

// 레시피 모달 표시
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

// 모달 닫기
function closeModal() {
    document.getElementById('recipeModal').classList.remove('show');
    document.body.style.overflow = '';
}

// 장바구니에 추가
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
