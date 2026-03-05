"""
Sunexa Music v4 — Full Stack Music Streaming App
"""
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import (Flask, render_template, request, redirect,
                   url_for, session, jsonify, flash)
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# ── Load .env file (local development ke liye) ───────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'sunexa_super_secret_key_2024')

# ── MySQL Config ──────────────────────────────────────────────
app.config['MYSQL_HOST']        = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER']        = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD']    = os.environ.get('MYSQL_PASSWORD', '')
app.config['MYSQL_DB']          = os.environ.get('MYSQL_DB', 'sunexa_music')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['MYSQL_SSL'] = {"ssl": {"ca": "ca.pem"}}

mysql_port = os.environ.get('MYSQL_PORT')
if mysql_port:
    app.config['MYSQL_PORT'] = int(mysql_port)

UPLOAD_FOLDER_IMAGES = os.path.join('static', 'uploads', 'images')
UPLOAD_FOLDER_SONGS  = os.path.join('static', 'uploads', 'songs')
ALLOWED_IMAGE_EXT = {'png','jpg','jpeg','gif','webp'}
ALLOWED_AUDIO_EXT = {'mp3','ogg','wav','flac'}
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

mysql = MySQL(app)

# ── Helpers ───────────────────────────────────────────────────
def allowed_image(f): return '.' in f and f.rsplit('.',1)[1].lower() in ALLOWED_IMAGE_EXT
def allowed_audio(f): return '.' in f and f.rsplit('.',1)[1].lower() in ALLOWED_AUDIO_EXT

def login_required(f):
    @wraps(f)
    def dec(*a,**k):
        if 'user_id' not in session:
            flash('Please log in.','warning'); return redirect(url_for('login'))
        return f(*a,**k)
    return dec

def admin_required(f):
    @wraps(f)
    def dec(*a,**k):
        if not session.get('admin_logged_in'):
            flash('Admin access required.','warning'); return redirect(url_for('admin_login'))
        return f(*a,**k)
    return dec

def log_admin(action, details=''):
    try:
        cur = mysql.connection.cursor()
        ip  = request.remote_addr
        cur.execute("INSERT INTO admin_logs (action,details,ip_address) VALUES (%s,%s,%s)",
                    (action, details, ip))
        mysql.connection.commit(); cur.close()
    except: pass

def log_user(user_id, action, details=''):
    try:
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO user_activity (user_id,action,details) VALUES (%s,%s,%s)",
                    (user_id, action, details))
        mysql.connection.commit(); cur.close()
    except: pass

# ── Index ─────────────────────────────────────────────────────
@app.route('/')
def index():
    if 'user_id' not in session: return redirect(url_for('login'))
    uid = session['user_id']
    cur = mysql.connection.cursor()

    genres = ['trending','romantic','sad','remix','hot','devotional','hiphop','party']
    genre_songs = {}
    for g in genres:
        cur.execute("SELECT * FROM songs WHERE genre=%s ORDER BY created_at DESC LIMIT 12", (g,))
        rows = cur.fetchall()
        if rows:
            genre_songs[g] = rows

    cur.execute("""
        SELECT s.*, rp.played_at FROM recently_played rp
        JOIN songs s ON rp.song_id=s.id
        WHERE rp.user_id=%s ORDER BY rp.played_at DESC LIMIT 6
    """, (uid,))
    recently_played = cur.fetchall()

    cur.execute("SELECT * FROM playlists WHERE user_id=%s ORDER BY id DESC", (uid,))
    playlists = cur.fetchall()

    cur.execute("SELECT song_id FROM liked_songs WHERE user_id=%s", (uid,))
    liked_ids = {r['song_id'] for r in cur.fetchall()}

    cur.execute("""
        SELECT * FROM premium_subscriptions
        WHERE user_id=%s AND status='active' AND expires_at > NOW()
        ORDER BY id DESC LIMIT 1
    """, (uid,))
    premium_sub = cur.fetchone()
    session['is_premium'] = bool(premium_sub)

    cur.close()
    return render_template('index.html',
                           genre_songs=genre_songs,
                           recently_played=recently_played,
                           playlists=playlists, liked_ids=liked_ids,
                           premium_sub=premium_sub)

# ── Auth ──────────────────────────────────────────────────────
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        name=request.form.get('name','').strip()
        email=request.form.get('email','').strip()
        password=request.form.get('password','')
        if not all([name,email,password]):
            flash('All fields required.','danger'); return redirect(url_for('signup'))
        try:
            cur=mysql.connection.cursor()
            cur.execute("INSERT INTO users (name,email,password) VALUES (%s,%s,%s)",
                        (name,email,generate_password_hash(password)))
            mysql.connection.commit()
            uid=cur.lastrowid; cur.close()
            log_user(uid,'signup',f'New account: {email}')
            flash('Account created! Please log in.','success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Signup Error: {str(e)}','danger')
            return redirect(url_for('signup'))
    return render_template('signup.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        identifier=request.form.get('email','').strip()
        password=request.form.get('password','')

        admin_pass = os.environ.get('ADMIN_PASSWORD', 'sunexa@admin123')
        if identifier == 'admin' and password == admin_pass:
            session['admin_logged_in'] = True
            log_admin('admin_login', f'Login from {request.remote_addr}')
            flash('Welcome, Admin!', 'success')
            return redirect(url_for('admin_dashboard'))

        try:
            cur=mysql.connection.cursor()
            cur.execute("SELECT * FROM users WHERE email=%s",(identifier,))
            user=cur.fetchone(); cur.close()
            if user and check_password_hash(user['password'],password):
                session['user_id']=user['id']
                session['user_name']=user['name']
                session['user_email']=user['email']
                cur2=mysql.connection.cursor()
                cur2.execute("SELECT * FROM premium_subscriptions WHERE user_id=%s AND status='active' AND expires_at>NOW() LIMIT 1",(user['id'],))
                sub=cur2.fetchone(); cur2.close()
                session['is_premium']=bool(sub)
                log_user(user['id'],'login',f'Login from {request.remote_addr}')
                flash(f"Welcome back, {user['name']}!",'success')
                return redirect(url_for('index'))
            flash('Invalid email or password.','danger')
        except Exception as e:
            flash(f'Login Error: {str(e)}','danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    if 'user_id' in session:
        log_user(session['user_id'],'logout','')
    session.clear()
    flash('Logged out.','info')
    return redirect(url_for('login'))

# ── Premium ───────────────────────────────────────────────────
@app.route('/premium')
@login_required
def premium():
    uid=session['user_id']
    cur=mysql.connection.cursor()
    cur.execute("""
        SELECT * FROM premium_subscriptions
        WHERE user_id=%s AND status='active' AND expires_at>NOW()
        ORDER BY id DESC LIMIT 1
    """,(uid,))
    sub=cur.fetchone(); cur.close()
    if sub:
        return redirect(url_for('premium_dashboard'))
    return render_template('premium.html')

@app.route('/premium/dashboard')
@login_required
def premium_dashboard():
    uid=session['user_id']
    cur=mysql.connection.cursor()
    cur.execute("""
        SELECT * FROM premium_subscriptions
        WHERE user_id=%s AND status='active' AND expires_at>NOW()
        ORDER BY id DESC LIMIT 1
    """,(uid,))
    sub=cur.fetchone()
    if not sub:
        flash('You do not have an active Premium plan.','warning')
        return redirect(url_for('premium'))
    cur.execute("SELECT COUNT(*) AS cnt FROM liked_songs WHERE user_id=%s",(uid,))
    liked_count=cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(DISTINCT song_id) AS cnt FROM recently_played WHERE user_id=%s",(uid,))
    played_count=cur.fetchone()['cnt']
    cur.execute("SELECT COUNT(*) AS cnt FROM playlists WHERE user_id=%s",(uid,))
    pl_count=cur.fetchone()['cnt']
    cur.execute("SELECT s.* FROM liked_songs ls JOIN songs s ON ls.song_id=s.id WHERE ls.user_id=%s ORDER BY ls.id DESC LIMIT 5",(uid,))
    fav_songs=cur.fetchall()
    cur.close()
    return render_template('premium_dashboard.html', sub=sub,
                           liked_count=liked_count, played_count=played_count,
                           pl_count=pl_count, fav_songs=fav_songs)

@app.route('/api/activate-premium', methods=['POST'])
@login_required
def api_activate_premium():
    data = request.get_json()
    plan   = data.get('plan','Individual')
    method = data.get('method','card')
    price  = 119 if plan=='Individual' else 179
    days   = 30
    uid    = session['user_id']
    try:
        cur=mysql.connection.cursor()
        cur.execute("UPDATE premium_subscriptions SET status='cancelled' WHERE user_id=%s AND status='active'",(uid,))
        expires = datetime.now() + timedelta(days=days)
        cur.execute("""
            INSERT INTO premium_subscriptions
            (user_id,plan_name,plan_price,duration_days,payment_method,status,expires_at)
            VALUES (%s,%s,%s,%s,%s,'active',%s)
        """,(uid,plan,price,days,method,expires))
        cur.execute("UPDATE users SET is_premium=1 WHERE id=%s",(uid,))
        mysql.connection.commit()
        session['is_premium']=True
        log_user(uid,'premium_activated',f'{plan} plan ₹{price} via {method}')
        log_admin('premium_activated',f'User {uid} activated {plan} ₹{price}')
        cur.close()
        return jsonify({'status':'ok','expires':expires.strftime('%d %b %Y')})
    except Exception as e:
        return jsonify({'error':str(e)}),500

# ── Song APIs ─────────────────────────────────────────────────
@app.route('/api/songs')
@login_required
def api_songs():
    cur=mysql.connection.cursor()
    cur.execute("SELECT * FROM songs ORDER BY created_at DESC")
    songs=cur.fetchall(); cur.close()
    for s in songs:
        if s.get('created_at'): s['created_at']=str(s['created_at'])
    return jsonify(songs)

@app.route('/api/search')
@login_required
def api_search():
    q=request.args.get('q','').strip()
    if not q: return jsonify([])
    cur=mysql.connection.cursor()
    cur.execute("SELECT * FROM songs WHERE title LIKE %s OR artist LIKE %s LIMIT 20",
                (f'%{q}%',f'%{q}%'))
    songs=cur.fetchall(); cur.close()
    for s in songs:
        if s.get('created_at'): s['created_at']=str(s['created_at'])
    return jsonify(songs)

@app.route('/api/recently-played', methods=['POST'])
@login_required
def api_recently_played():
    data=request.get_json(); song_id=data.get('song_id')
    if not song_id: return jsonify({'error':'song_id required'}),400
    cur=mysql.connection.cursor()
    cur.execute("DELETE FROM recently_played WHERE user_id=%s AND song_id=%s",(session['user_id'],song_id))
    cur.execute("INSERT INTO recently_played (user_id,song_id) VALUES (%s,%s)",(session['user_id'],song_id))
    mysql.connection.commit(); cur.close()
    return jsonify({'status':'ok'})

@app.route('/api/like-song', methods=['POST'])
@login_required
def api_like_song():
    data=request.get_json(); song_id=data.get('song_id')
    if not song_id: return jsonify({'error':'song_id required'}),400
    cur=mysql.connection.cursor()
    cur.execute("SELECT id FROM liked_songs WHERE user_id=%s AND song_id=%s",(session['user_id'],song_id))
    if cur.fetchone():
        cur.execute("DELETE FROM liked_songs WHERE user_id=%s AND song_id=%s",(session['user_id'],song_id))
        liked=False
    else:
        cur.execute("INSERT INTO liked_songs (user_id,song_id) VALUES (%s,%s)",(session['user_id'],song_id))
        liked=True
    mysql.connection.commit(); cur.close()
    return jsonify({'liked':liked})

# ── Playlist APIs ─────────────────────────────────────────────
@app.route('/api/create-playlist', methods=['POST'])
@login_required
def api_create_playlist():
    data=request.get_json(); name=(data.get('name') or '').strip()
    if not name: return jsonify({'error':'Name required'}),400
    cur=mysql.connection.cursor()
    cur.execute("INSERT INTO playlists (user_id,name) VALUES (%s,%s)",(session['user_id'],name))
    mysql.connection.commit(); pid=cur.lastrowid; cur.close()
    return jsonify({'id':pid,'name':name})

@app.route('/api/delete-playlist', methods=['POST'])
@login_required
def api_delete_playlist():
    data=request.get_json(); pid=data.get('playlist_id')
    cur=mysql.connection.cursor()
    cur.execute("DELETE FROM playlists WHERE id=%s AND user_id=%s",(pid,session['user_id']))
    mysql.connection.commit(); cur.close()
    return jsonify({'status':'deleted'})

# ── Admin ─────────────────────────────────────────────────────
@app.route('/admin')
def admin(): return redirect(url_for('admin_login'))

@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method=='POST':
        admin_pass = os.environ.get('ADMIN_PASSWORD', 'sunexa@admin123')
        if request.form.get('username')=='admin' and request.form.get('password')==admin_pass:
            session['admin_logged_in']=True
            log_admin('admin_login',f'Login from {request.remote_addr}')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials.','danger')
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    cur=mysql.connection.cursor()
    cur.execute("SELECT * FROM songs ORDER BY created_at DESC")
    songs=cur.fetchall()
    cur.execute("""
        SELECT u.id, u.name, u.email, u.created_at, u.is_premium,
               COUNT(DISTINCT ls.song_id)  AS liked_count,
               COUNT(DISTINCT rp.song_id)  AS played_count,
               COUNT(DISTINCT p.id)        AS playlist_count,
               ps.plan_name, ps.plan_price, ps.payment_method,
               ps.started_at, ps.expires_at, ps.status AS sub_status
        FROM users u
        LEFT JOIN liked_songs        ls ON ls.user_id = u.id
        LEFT JOIN recently_played    rp ON rp.user_id = u.id
        LEFT JOIN playlists           p ON p.user_id  = u.id
        LEFT JOIN premium_subscriptions ps ON ps.user_id=u.id AND ps.status='active' AND ps.expires_at>NOW()
        GROUP BY u.id, u.name, u.email, u.created_at, u.is_premium,
                 ps.plan_name, ps.plan_price, ps.payment_method,
                 ps.started_at, ps.expires_at, ps.status
        ORDER BY u.created_at DESC
    """)
    users=cur.fetchall()
    cur.execute("SELECT SUM(plan_price) AS total, COUNT(*) AS cnt FROM premium_subscriptions WHERE status='active'")
    revenue=cur.fetchone()
    cur.execute("SELECT * FROM admin_logs ORDER BY created_at DESC LIMIT 20")
    admin_logs=cur.fetchall()
    cur.execute("""
        SELECT ua.*, u.name AS user_name
        FROM user_activity ua
        JOIN users u ON ua.user_id=u.id
        ORDER BY ua.created_at DESC LIMIT 30
    """)
    user_activity=cur.fetchall()
    cur.close()
    return render_template('admin_dashboard.html',
                           songs=songs, users=users,
                           revenue=revenue, admin_logs=admin_logs,
                           user_activity=user_activity)

@app.route('/admin/upload-song', methods=['POST'])
@admin_required
def admin_upload_song():
    title=request.form.get('title','').strip()
    artist=request.form.get('artist','').strip()
    genre=request.form.get('genre','trending')
    image_file=request.files.get('image')
    song_file=request.files.get('song')
    if not all([title,artist,image_file,song_file]):
        flash('All fields required.','danger'); return redirect(url_for('admin_dashboard'))
    if not allowed_image(image_file.filename):
        flash('Invalid image format.','danger'); return redirect(url_for('admin_dashboard'))
    if not allowed_audio(song_file.filename):
        flash('Invalid audio format.','danger'); return redirect(url_for('admin_dashboard'))
    try:
        img_name=secure_filename(image_file.filename)
        sng_name=secure_filename(song_file.filename)
        image_file.save(os.path.join(UPLOAD_FOLDER_IMAGES,img_name))
        song_file.save(os.path.join(UPLOAD_FOLDER_SONGS,sng_name))
        cur=mysql.connection.cursor()
        cur.execute("INSERT INTO songs (title,artist,image,file_path,genre) VALUES (%s,%s,%s,%s,%s)",
                    (title,artist,f'uploads/images/{img_name}',f'uploads/songs/{sng_name}',genre))
        mysql.connection.commit(); cur.close()
        log_admin('song_uploaded',f'{title} by {artist} [{genre}]')
        flash('Song uploaded!','success')
    except Exception as e:
        flash(f'Error: {e}','danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-song', methods=['POST'])
@admin_required
def admin_delete_song():
    sid=request.form.get('song_id')
    try:
        cur=mysql.connection.cursor()
        cur.execute("SELECT title,image,file_path FROM songs WHERE id=%s",(sid,))
        song=cur.fetchone()
        if song:
            for key in ('image','file_path'):
                path=os.path.join('static',song[key])
                if os.path.exists(path): os.remove(path)
            cur.execute("DELETE FROM songs WHERE id=%s",(sid,))
            mysql.connection.commit()
            log_admin('song_deleted',f'{song["title"]}')
        cur.close(); flash('Song deleted.','success')
    except Exception as e:
        flash(f'Error: {e}','danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-user', methods=['POST'])
@admin_required
def admin_delete_user():
    uid=request.form.get('user_id')
    try:
        cur=mysql.connection.cursor()
        cur.execute("SELECT name,email FROM users WHERE id=%s",(uid,))
        user=cur.fetchone()
        if user:
            cur.execute("DELETE FROM users WHERE id=%s",(uid,))
            mysql.connection.commit()
            log_admin('user_deleted',f'{user["name"]} ({user["email"]})')
            flash(f'User {user["name"]} deleted.','success')
        cur.close()
    except Exception as e:
        flash(f'Error: {e}','danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/revoke-premium', methods=['POST'])
@admin_required
def admin_revoke_premium():
    uid=request.form.get('user_id')
    try:
        cur=mysql.connection.cursor()
        cur.execute("UPDATE premium_subscriptions SET status='cancelled' WHERE user_id=%s AND status='active'",(uid,))
        cur.execute("UPDATE users SET is_premium=0 WHERE id=%s",(uid,))
        mysql.connection.commit(); cur.close()
        log_admin('premium_revoked',f'User {uid} premium revoked')
        flash('Premium revoked.','success')
    except Exception as e:
        flash(f'Error: {e}','danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    log_admin('admin_logout','')
    session.pop('admin_logged_in',None)
    return redirect(url_for('admin_login'))

@app.route('/genre/<genre_name>')
@login_required
def genre_page(genre_name):
    VALID = ['trending','romantic','sad','remix','hot','devotional','hiphop','party']
    if genre_name not in VALID:
        return redirect(url_for('index'))
    uid = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM songs WHERE genre=%s ORDER BY created_at DESC", (genre_name,))
    songs = cur.fetchall()
    cur.execute("SELECT song_id FROM liked_songs WHERE user_id=%s", (uid,))
    liked_ids = {r['song_id'] for r in cur.fetchall()}
    cur.execute("SELECT * FROM playlists WHERE user_id=%s ORDER BY id DESC", (uid,))
    playlists = cur.fetchall()
    cur.close()
    return render_template('genre.html', genre=genre_name, songs=songs,
                           liked_ids=liked_ids, playlists=playlists)

@app.route('/api/cancel-premium', methods=['POST'])
@login_required
def api_cancel_premium():
    uid = session['user_id']
    try:
        cur = mysql.connection.cursor()
        cur.execute("UPDATE premium_subscriptions SET status='cancelled' WHERE user_id=%s AND status='active'", (uid,))
        cur.execute("UPDATE users SET is_premium=0 WHERE id=%s", (uid,))
        mysql.connection.commit(); cur.close()
        session['is_premium'] = False
        log_user(uid, 'premium_cancelled', 'Self-cancelled premium')
        return jsonify({'status':'ok'})
    except Exception as e:
        return jsonify({'error':str(e)}), 500

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

if __name__=='__main__':
    app.run(debug=True)