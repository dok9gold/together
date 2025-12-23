// 냉장고 털기 페이지 JS

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

    document.getElementById('resultCard').innerHTML = `
        <p class="result-intro">${all.join(', ')}이(가) 있으시네요!</p>
        <div class="result-list">
            <h3>제육볶음 어때요?</h3>
            <p>지금 고추장이 20% 할인이에요!</p>
        </div>
        <div class="discount-info">
            <p>고추장 20% - 2,400원</p>
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
    alert('1. 고기 양념하기\n2. 야채 썰기\n3. 센 불에 볶기\n4. 완성!');
}

function addToCart() {
    alert('장바구니에 담았습니다!');
}

// 엔터키로 추가
document.getElementById('addInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') addItem();
});
