// 할인상품 추천 페이지 JS

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

    document.getElementById('resultCard').innerHTML = `
        <p class="result-intro">${all.join(', ')}을(를) 선택하셨네요!</p>
        <div class="result-list">
            <h3>비빔밥 어때요?</h3>
            <p>선택하신 재료로 맛있게 만들 수 있어요!</p>
        </div>
        <div class="discount-info">
            <p>들기름 50% - 4,500원</p>
            <p>삼겹살 30% - 12,600원</p>
        </div>
        <div class="result-actions">
            <button class="action-btn" onclick="showRecipe()">레시피 보기</button>
            <button class="action-btn secondary" onclick="addToCart()">장바구니 담기</button>
        </div>
    `;

    document.getElementById('resultSection').hidden = false;
    document.getElementById('resultSection').scrollIntoView({ behavior: 'smooth' });
}

function showRecipe() {
    alert('1. 밥 준비\n2. 나물 볶기\n3. 고추장 넣고 비비기\n4. 완성!');
}

function addToCart() {
    alert('장바구니에 담았습니다!');
}

// 엔터키로 추가
document.getElementById('addInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') addItem();
});
