const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');

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
        // API 호출 (추후 실제 API로 교체)
        const response = await mockApiCall(message);

        // 타이핑 인디케이터 제거
        hideTypingIndicator();

        // AI 응답 추가
        addMessageToDOM(response.content, 'ai', response.actions);
    } catch (error) {
        hideTypingIndicator();
        addMessageToDOM('죄송합니다. 오류가 발생했습니다. 다시 시도해주세요.', 'ai');
    }

    // 버튼 활성화
    sendBtn.disabled = false;
}

// DOM에 메시지 추가
function addMessageToDOM(content, type, actions = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;

    let html = `<div class="message-content">${formatMessage(content)}</div>`;

    // 액션 버튼 추가
    if (actions && actions.length > 0) {
        html = `
            <div class="message-content">
                ${formatMessage(content)}
                <div class="action-buttons">
                    ${actions.map(a => `<button class="action-btn" onclick="${a.onclick}">${a.label}</button>`).join('')}
                </div>
            </div>
        `;
    }

    messageDiv.innerHTML = html;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
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

// Mock API 호출 (추후 실제 API로 교체)
async function mockApiCall(message) {
    // 1~2초 딜레이
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000));

    // 간단한 응답 로직
    if (message.includes('삼겹살')) {
        return {
            content: '삼겹살로 만들 수 있는 요리를 추천해드릴게요!\n\n1. 삼겹살 김치찌개\n2. 대패삼겹 숙주볶음\n3. 삼겹살 된장찌개\n4. 삼겹살 볶음밥\n\n지금 마트에서 삼겹살이 30% 할인 중이에요!',
            actions: [
                { label: '레시피 보기', onclick: 'showRecipe()' },
                { label: '장바구니 담기', onclick: 'addToCart()' }
            ]
        };
    } else if (message.includes('저녁') || message.includes('추천')) {
        return {
            content: '간단한 저녁 메뉴 추천이요!\n\n1. 제육볶음 - 30분\n2. 계란말이 - 15분\n3. 김치볶음밥 - 20분\n4. 된장찌개 - 25분\n\n어떤 요리가 끌리세요?',
            actions: [
                { label: '레시피 보기', onclick: 'showRecipe()' },
                { label: '재료 확인', onclick: 'showIngredients()' }
            ]
        };
    } else {
        return {
            content: `"${message}"에 대해 알아볼게요!\n\n관련 요리를 찾아보고 있어요. 조금만 기다려주세요...`,
            actions: null
        };
    }
}

// 액션 함수들 (추후 구현)
function showRecipe() {
    alert('레시피 상세 페이지로 이동합니다!');
}

function addToCart() {
    alert('장바구니에 담았습니다!');
}

function showIngredients() {
    alert('필요한 재료 목록을 보여드립니다!');
}
