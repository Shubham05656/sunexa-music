USE sunexa_music;

SET SQL_SAFE_UPDATES = 0;

UPDATE songs SET genre = 'trending' WHERE genre IS NULL OR genre = '';

SET SQL_SAFE_UPDATES = 1;

CREATE TABLE IF NOT EXISTS premium_subscriptions (
    id           INT          PRIMARY KEY AUTO_INCREMENT,
    user_id      INT          NOT NULL,
    plan_name    VARCHAR(50)  NOT NULL,
    plan_price   DECIMAL(8,2) NOT NULL,
    duration_days INT         NOT NULL DEFAULT 30,
    payment_method VARCHAR(30) NOT NULL DEFAULT 'card',
    status       ENUM('active','expired','cancelled') DEFAULT 'active',
    started_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    expires_at   TIMESTAMP    NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS admin_logs (
    id         INT           PRIMARY KEY AUTO_INCREMENT,
    action     VARCHAR(100)  NOT NULL,
    details    TEXT,
    ip_address VARCHAR(50),
    created_at TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_activity (
    id         INT           PRIMARY KEY AUTO_INCREMENT,
    user_id    INT           NOT NULL,
    action     VARCHAR(100)  NOT NULL,
    details    TEXT,
    created_at TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

SELECT id, title, artist, genre FROM songs;