// 채팅 페이지 JS - API 연동

const API_BASE = '/api';

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

        // AI 응답 추가
        addMessageToDOM(data.content, 'ai', data.actions);
    } catch (error) {
        console.error('채팅 API 오류:', error);
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
                    ${actions.map(a => `<button class="action-btn" onclick="handleAction('${a.type}', ${JSON.stringify(a.data).replace(/"/g, '&quot;')})">${a.label}</button>`).join('')}
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

// 액션 버튼 핸들러
async function handleAction(type, data) {
    switch (type) {
        case 'recipe':
            if (data && data.id) {
                // 레시피 상세 페이지로 이동 또는 모달 표시
                window.location.href = `recipe.html?id=${data.id}`;
            }
            break;
        case 'cart':
            if (data && data.items) {
                await addToCart(data.items);
            }
            break;
        case 'ingredients':
            if (data && data.items) {
                alert(`필요한 재료: ${data.items.join(', ')}`);
            }
            break;
        default:
            console.log('Unknown action:', type, data);
    }
}

// 장바구니에 추가
async function addToCart(items) {
    try {
        const cartItems = items.map(name => ({ name, quantity: 1 }));
        const response = await fetch(`${API_BASE}/cart/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ items: cartItems })
        });

        if (response.ok) {
            alert('장바구니에 담았습니다!');
        } else {
            throw new Error('장바구니 추가 실패');
        }
    } catch (error) {
        console.error('장바구니 API 오류:', error);
        alert('장바구니 추가에 실패했습니다.');
    }
}
