-- ============================================
-- 시퀀스 네이밍 규칙
-- ============================================
-- {feature}_{column}_seq
-- ex) chef_session_id_seq, chef_message_id_seq
-- ============================================

-- Chef 시퀀스
CREATE SEQUENCE chef_session_id_seq;
CREATE SEQUENCE chef_message_id_seq;

-- ============================================
-- 범용 State 테이블
-- ============================================
-- 다양한 AI 기능의 세션/메시지 상태를 저장하는 범용 테이블
--
-- PK: (session_id, message_id)
-- - feature: 기능명 (ex: 'chef', 'other_ai', ...)
-- - session_id: 세션 ID (feature별 시퀀스로 채번)
-- - message_id: 메시지 ID (세션 내 순번)
-- ============================================

CREATE TABLE state (
    feature VARCHAR(50) NOT NULL,
    session_id INT NOT NULL,
    message_id INT NOT NULL,
    state JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (session_id, message_id)
);

CREATE INDEX idx_state_feature ON state (feature);
CREATE INDEX idx_state_feature_session ON state (feature, session_id);

-- ============================================
-- 범용 Message 테이블
-- ============================================
-- 다양한 AI 기능의 채팅 메시지를 저장하는 범용 테이블
--
-- PK: (session_id, message_id, role)
-- - feature: 기능명 (ex: 'chef', 'other_ai', ...)
-- - session_id: 세션 ID (feature별 시퀀스로 채번)
-- - message_id: 메시지 ID (세션 내 순번)
-- - role: 'user' | 'ai'
-- ============================================

CREATE TABLE message (
    feature VARCHAR(50) NOT NULL,
    session_id INT NOT NULL,
    message_id INT NOT NULL,
    role VARCHAR(10) NOT NULL,
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (session_id, message_id, role)
);

CREATE INDEX idx_message_feature ON message (feature);
CREATE INDEX idx_message_feature_session ON message (feature, session_id);

-- ============================================
-- 상품 카테고리 테이블
-- ============================================

CREATE TABLE product_category (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

-- ============================================
-- 상품 테이블
-- ============================================

CREATE TABLE product (
    barcode VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    detail_name VARCHAR(200),
    category_id INT REFERENCES product_category(category_id),
    price INT
);

CREATE INDEX idx_product_category ON product (category_id);

-- ============================================
-- 할인 상품 테이블
-- ============================================
-- discount_type: '할인', '1+1', '2+1' 등
-- discount_rate: 할인일 때만 사용 (%, ex: 30)

CREATE TABLE discount_product (
    barcode VARCHAR(50) PRIMARY KEY REFERENCES product(barcode),
    discount_type VARCHAR(20) NOT NULL,
    discount_rate INT,
    start_date DATE,
    end_date DATE
);

-- ============================================
-- 레시피 캐시 테이블
-- ============================================
-- AI 생성 레시피를 캐싱하는 테이블
--
-- dish_name 정규화 규칙:
-- - 공백 제거
-- - 영어는 소문자로 변환
-- ex) "김치 찌개" → "김치찌개", "Kimchi Jjigae" → "kimchijjigae"

CREATE TABLE recipe (
    dish_name VARCHAR(100) PRIMARY KEY,
    display_name VARCHAR(100) NOT NULL,
    content JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- 레시피 조회 로그 테이블
-- ============================================
-- 인기 레시피 순위 산출용

CREATE TABLE recipe_log (
    log_id SERIAL PRIMARY KEY,
    dish_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_recipe_log_dish ON recipe_log (dish_name);
