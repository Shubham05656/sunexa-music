-- ============================================================
--  Sunexa Music — Complete Database Setup v4
-- ============================================================
CREATE DATABASE IF NOT EXISTS sunexa_music CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE sunexa_music;

CREATE TABLE IF NOT EXISTS users (
    id         INT          PRIMARY KEY AUTO_INCREMENT,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(150) NOT NULL UNIQUE,
    password   VARCHAR(255) NOT NULL,
    is_premium TINYINT(1)   DEFAULT 0,
    created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS songs (
    id         INT          PRIMARY KEY AUTO_INCREMENT,
    title      VARCHAR(200) NOT NULL,
    artist     VARCHAR(150) NOT NULL,
    image      VARCHAR(300) NOT NULL,
    file_path  VARCHAR(300) NOT NULL,
    genre      VARCHAR(50)  DEFAULT 'trending',
    created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS playlists (
    id      INT          PRIMARY KEY AUTO_INCREMENT,
    user_id INT          NOT NULL,
    name    VARCHAR(200) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS playlist_songs (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    playlist_id INT NOT NULL,
    song_id     INT NOT NULL,
    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
    FOREIGN KEY (song_id)     REFERENCES songs(id)     ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS recently_played (
    id        INT       PRIMARY KEY AUTO_INCREMENT,
    user_id   INT       NOT NULL,
    song_id   INT       NOT NULL,
    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS liked_songs (
    id      INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    song_id INT NOT NULL,
    UNIQUE KEY uq_like (user_id, song_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
);

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
