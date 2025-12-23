// 요리 추천 페이지 JS

function getRecommendation() {
    const categories = Array.from(document.querySelectorAll('input[name="category"]:checked'))
        .map(cb => cb.value);
    const condition = document.getElementById('conditionInput').value.trim();

    if (categories.length === 0 && !condition) {
        alert('카테고리를 선택하거나 조건을 입력해주세요!');
        return;
    }

    const categoryText = categories.length > 0 ? categories.join(', ') : '맞춤';

    const recommendations = {
        '한식': ['김치찌개', '된장찌개', '불고기', '비빔밥'],
        '중식': ['짜장면', '탕수육', '마파두부', '볶음밥'],
        '일식': ['돈카츠', '우동', '연어덮밥', '라멘'],
        '양식': ['파스타', '스테이크', '리조또', '피자']
    };

    let result = categories.length > 0 ? recommendations[categories[0]] : ['제육볶음', '계란말이', '김치볶음밥', '된장찌개'];

    document.getElementById('resultCard').innerHTML = `
        <p class="result-intro">${categoryText} 요리를 원하시는군요!</p>
        <div class="result-list">
            <h3>오늘의 추천 요리</h3>
            <ul>
                ${result.map(r => `<li>${r}</li>`).join('')}
            </ul>
        </div>
        <p class="result-tip">관련 재료가 할인 중이에요!</p>
        <div class="result-actions">
            <button class="action-btn" onclick="showRecipe()">레시피 보기</button>
            <button class="action-btn secondary" onclick="addToCart()">장바구니 담기</button>
        </div>
    `;

    document.getElementById('resultSection').hidden = false;
    document.getElementById('resultSection').scrollIntoView({ behavior: 'smooth' });
}

function showRecipe() {
    alert('레시피 상세 페이지로 이동합니다!');
}

function addToCart() {
    alert('장바구니에 담았습니다!');
}
