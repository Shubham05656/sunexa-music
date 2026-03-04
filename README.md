# 🎵 Sunexa Music

A full-stack music streaming web application built with Flask + MySQL.

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.10+
- MySQL 8.0+ running locally
- pip

---

### 2. Create & Activate Virtual Environment

```bash
cd sunexa-music

# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `flask-mysqldb` requires `libmysqlclient-dev` on Ubuntu/Debian:
> ```bash
> sudo apt install libmysqlclient-dev python3-dev
> ```
> On macOS with Homebrew:
> ```bash
> brew install mysql-client pkg-config
> export PKG_CONFIG_PATH="/opt/homebrew/opt/mysql-client/lib/pkgconfig"
> ```

---

### 4. Create the Database

```bash
mysql -u root -p < sunexa_db.sql
```

Or run these manually in MySQL:

```sql
CREATE DATABASE sunexa_music CHARACTER SET utf8mb4;
USE sunexa_music;
-- ... (see sunexa_db.sql)
```

---

### 5. Configure Database Credentials

Open `app.py` and update if needed:

```python
app.config['MYSQL_HOST']     = 'localhost'
app.config['MYSQL_USER']     = 'root'
app.config['MYSQL_PASSWORD'] = ''        # ← set your MySQL password
app.config['MYSQL_DB']       = 'sunexa_music'
```

---

### 6. Run the App

```bash
python app.py
```

Open your browser: **http://127.0.0.1:5000**

---

## 🔑 Credentials

| Role  | URL                        | Username | Password          |
|-------|----------------------------|----------|-------------------|
| User  | http://127.0.0.1:5000      | (signup) | (your choice)     |
| Admin | http://127.0.0.1:5000/admin| admin    | sunexa@admin123   |

---

## 📁 Project Structure

```
sunexa-music/
├── app.py                    # Flask application
├── requirements.txt
├── sunexa_db.sql             # Database schema
├── README.md
├── static/
│   ├── css/style.css         # All styles
│   ├── js/script.js          # Player, AJAX, playlists
│   ├── uploads/
│   │   ├── images/           # Song cover art (uploaded)
│   │   └── songs/            # Audio files (uploaded)
└── templates/
    ├── base.html             # Base layout with flash toasts
    ├── index.html            # Main dashboard
    ├── login.html
    ├── signup.html
    ├── admin_login.html
    └── admin_dashboard.html
```

---

## 🎵 Adding Songs (via Admin Panel)

1. Go to http://127.0.0.1:5000/admin
2. Login with `admin` / `sunexa@admin123`
3. Use the "Upload New Song" form
4. Fill in Title, Artist, select a cover image + audio file
5. Click **Upload Song**

Songs will appear on the main page immediately.

---

## 🔌 API Reference

| Method | Endpoint              | Description              |
|--------|-----------------------|--------------------------|
| GET    | /api/songs            | All songs (JSON)         |
| GET    | /api/search?q=query   | Search songs             |
| POST   | /api/recently-played  | Log a play               |
| POST   | /api/like-song        | Toggle like/unlike       |
| POST   | /api/create-playlist  | Create new playlist      |
| POST   | /api/delete-playlist  | Delete a playlist        |

---

## 🎨 Features

- 🌙 **Dark themed UI** with gradient accents and glassmorphism  
- 🎵 **Full audio player** — play/pause, seek, volume, shuffle, repeat  
- 🔍 **Live AJAX search** — no page reloads  
- ❤️ **Like system** — toggle hearts on any song  
- 📂 **Playlists** — create and delete from sidebar  
- 🕐 **Recently played** — tracks your listening history  
- 📊 **Feature charts** — top songs ranked  
- 🛡️ **Admin panel** — upload/delete songs with file management  
- 📱 **Fully responsive** — works on mobile  
