// 레시피 검색 페이지 JS

const recipes = {
    '김치찌개': { time: '30분', difficulty: '쉬움', ingredients: '김치, 돼지고기, 두부, 대파, 고춧가루' },
    '된장찌개': { time: '25분', difficulty: '쉬움', ingredients: '된장, 두부, 애호박, 감자, 대파' },
    '제육볶음': { time: '20분', difficulty: '보통', ingredients: '돼지고기, 고추장, 양파, 대파, 마늘' },
    '불고기': { time: '40분', difficulty: '보통', ingredients: '소고기, 간장, 배, 양파, 마늘' },
    '파스타': { time: '25분', difficulty: '쉬움', ingredients: '파스타면, 올리브오일, 마늘, 베이컨' }
};

function quickSearch(keyword) {
    document.getElementById('searchInput').value = keyword;
    searchRecipe();
}

function searchRecipe() {
    const keyword = document.getElementById('searchInput').value.trim();

    if (!keyword) {
        alert('요리명을 입력해주세요!');
        return;
    }

    const recipe = recipes[keyword] || { time: '30분', difficulty: '보통', ingredients: '돼지고기, 양파, 마늘, 간장, 설탕' };

    document.getElementById('resultCard').innerHTML = `
        <div class="recipe-header">
            <h3>${keyword}</h3>
            <div class="recipe-meta">
                <span>조리시간: ${recipe.time}</span>
                <span>난이도: ${recipe.difficulty}</span>
            </div>
        </div>
        <div class="recipe-ingredients">
            <h4>필요한 재료</h4>
            <p>${recipe.ingredients}</p>
        </div>
        <div class="result-actions">
            <button class="action-btn" onclick="showRecipeDetail()">레시피 보기</button>
            <button class="action-btn secondary" onclick="addToCart()">장바구니 담기</button>
        </div>
    `;

    document.getElementById('resultSection').hidden = false;
    document.getElementById('resultSection').scrollIntoView({ behavior: 'smooth' });
}

function showRecipeDetail() {
    alert('1. 재료 손질\n2. 조리하기\n3. 간 맞추기\n4. 완성!');
}

function addToCart() {
    alert('장바구니에 담았습니다!');
}

// 엔터키 검색
document.getElementById('searchInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') searchRecipe();
});
