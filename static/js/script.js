/* ================================================================
   Sunexa Music — script.js  (Main Player + UI)
   Works on both index.html and genre.html
   ================================================================ */

'use strict';

/* ── Audio & State ─────────────────────────────────────────── */
const audio       = document.getElementById('audioPlayer');
let queue         = [];   // [{id,title,artist,image,src}]
let currentIdx    = -1;
let isShuffle     = false;
let isRepeat      = false;
let currentSongId = null;

/* Build queue from all song cards on page load */
document.addEventListener('DOMContentLoaded', () => {
  buildQueue();
  initSeekBar();
  initVolume();
});

function buildQueue() {
  // genre.html exposes genreSongs global; index.html doesn't
  if (typeof genreSongs !== 'undefined' && genreSongs.length) {
    queue = genreSongs;
  }
  // Otherwise queue is built dynamically as songs play
}

/* ── Play a Song ───────────────────────────────────────────── */
function playSong(id, title, artist, imgSrc, fileSrc) {
  // Add to queue if not present
  if (!queue.find(s => s.id === id)) {
    queue.push({ id, title, artist, image: imgSrc, src: fileSrc });
  }
  currentIdx    = queue.findIndex(s => s.id === id);
  currentSongId = id;

  audio.src = fileSrc;
  audio.load();
  audio.play().then(() => setPlayIcon(true)).catch(() => {});

  // Update player bar
  document.getElementById('playerTitle').textContent  = title;
  document.getElementById('playerArtist').textContent = artist;
  document.getElementById('playerImg').src            = imgSrc;

  // Highlight row on genre page
  document.querySelectorAll('.genre-list-row').forEach(r => r.classList.remove('playing'));
  const row = document.getElementById('song-row-' + id);
  if (row) row.classList.add('playing');

  // Track recently played
  fetch('/api/recently-played', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ song_id: id })
  }).catch(() => {});
}

/* alias used by genre.html */
function playGenreSong(id, title, artist, imgSrc, fileSrc) {
  playSong(id, title, artist, imgSrc, fileSrc);
}

/* ── Controls ──────────────────────────────────────────────── */
function togglePlay() {
  if (!audio.src) return;
  if (audio.paused) audio.play().then(() => setPlayIcon(true)).catch(() => {});
  else              { audio.pause(); setPlayIcon(false); }
}

function nextSong() {
  if (!queue.length) return;
  if (isShuffle) currentIdx = Math.floor(Math.random() * queue.length);
  else           currentIdx = (currentIdx + 1) % queue.length;
  const s = queue[currentIdx];
  playSong(s.id, s.title, s.artist, s.image, s.src);
}

function prevSong() {
  if (!queue.length) return;
  if (audio.currentTime > 3) { audio.currentTime = 0; return; }
  currentIdx = (currentIdx - 1 + queue.length) % queue.length;
  const s = queue[currentIdx];
  playSong(s.id, s.title, s.artist, s.image, s.src);
}

function playAll() {
  if (queue.length) {
    const s = queue[0];
    playSong(s.id, s.title, s.artist, s.image, s.src);
  }
}

function shuffleAll() {
  if (!queue.length) return;
  isShuffle = true;
  document.getElementById('shuffleBtn')?.classList.add('active');
  const idx = Math.floor(Math.random() * queue.length);
  const s   = queue[idx];
  playSong(s.id, s.title, s.artist, s.image, s.src);
}

function toggleShuffle() {
  isShuffle = !isShuffle;
  document.getElementById('shuffleBtn')?.classList.toggle('active', isShuffle);
}

function toggleRepeat() {
  isRepeat = !isRepeat;
  document.getElementById('repeatBtn')?.classList.toggle('active', isRepeat);
}

/* ── Audio Events ──────────────────────────────────────────── */
if (audio) {
  audio.volume = 0.8;

  audio.addEventListener('timeupdate', () => {
    if (!audio.duration) return;
    const pct = (audio.currentTime / audio.duration) * 100;
    const bar = document.getElementById('seekBar');
    if (bar) {
      bar.value = pct;
      bar.style.setProperty('--seek-pct', pct + '%');
    }
    document.getElementById('currentTime').textContent = fmtTime(audio.currentTime);
  });

  audio.addEventListener('loadedmetadata', () => {
    document.getElementById('totalTime').textContent = fmtTime(audio.duration);
    if (currentSongId) {
      const el = document.getElementById('dur-' + currentSongId);
      if (el) el.textContent = fmtTime(audio.duration);
    }
  });

  audio.addEventListener('ended', () => {
    if (isRepeat) { audio.currentTime = 0; audio.play(); }
    else nextSong();
  });

  audio.addEventListener('play',  () => setPlayIcon(true));
  audio.addEventListener('pause', () => setPlayIcon(false));
}

/* ── Seek & Volume ─────────────────────────────────────────── */
function initSeekBar() {
  const bar = document.getElementById('seekBar');
  if (bar) bar.style.setProperty('--seek-pct', '0%');
}

function initVolume() {
  const bar = document.getElementById('volumeBar');
  if (bar) {
    bar.value = 80;
    bar.style.setProperty('--vol-pct', '80%');
  }
}

function seekTo(v) {
  if (!audio || !audio.duration) return;
  audio.currentTime = (v / 100) * audio.duration;
  document.getElementById('seekBar')?.style.setProperty('--seek-pct', v + '%');
}

let isMuted = false;
function setVolume(v) {
  if (audio) audio.volume = v / 100;
  document.getElementById('volumeBar')?.style.setProperty('--vol-pct', v + '%');
  updateVolIcon(v);
}

function toggleMute() {
  if (!audio) return;
  isMuted = !isMuted;
  audio.muted = isMuted;
  const v   = isMuted ? 0 : Math.round(audio.volume * 100);
  const bar = document.getElementById('volumeBar');
  if (bar) { bar.value = v; bar.style.setProperty('--vol-pct', v + '%'); }
  updateVolIcon(v);
}

function updateVolIcon(v) {
  const i = document.getElementById('volIcon');
  if (!i) return;
  if (v == 0)     i.className = 'bi bi-volume-mute';
  else if (v < 50) i.className = 'bi bi-volume-down';
  else             i.className = 'bi bi-volume-up';
}

/* ── Helpers ───────────────────────────────────────────────── */
function setPlayIcon(playing) {
  const i = document.getElementById('playPauseIcon');
  if (i) i.className = playing ? 'bi bi-pause-fill' : 'bi bi-play-fill';
}

function fmtTime(s) {
  if (!s || isNaN(s)) return '0:00';
  return Math.floor(s / 60) + ':' + String(Math.floor(s % 60)).padStart(2, '0');
}

/* ── Like ──────────────────────────────────────────────────── */
function toggleLike(songId, btn) {
  fetch('/api/like-song', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ song_id: songId })
  })
  .then(r => r.json())
  .then(data => {
    // Update every like button for this song on the page
    document.querySelectorAll(`.like-btn, .like-btn-row`).forEach(b => {
      if (b.getAttribute('onclick') && b.getAttribute('onclick').includes(`toggleLike(${songId}`)) {
        b.classList.toggle('liked', data.liked);
        const ico = b.querySelector('i');
        if (ico) ico.className = data.liked ? 'bi bi-heart-fill' : 'bi bi-heart';
      }
    });
    // Player bar heart
    if (songId === currentSongId) {
      const pi = document.getElementById('playerLikeIcon');
      const pb = document.getElementById('playerLikeBtn');
      if (pi) pi.className = data.liked ? 'bi bi-heart-fill' : 'bi bi-heart';
      if (pb) pb.classList.toggle('liked', data.liked);
    }
  })
  .catch(() => {});
}

function toggleLikePlayer() {
  if (currentSongId) toggleLike(currentSongId, document.getElementById('playerLikeBtn'));
}

/* ── Search ────────────────────────────────────────────────── */
let searchTimer = null;

function toggleSearch() {
  const wrap = document.getElementById('searchBarWrap');
  if (!wrap) return;
  const isHidden = wrap.style.display === 'none' || !wrap.style.display;
  wrap.style.display = isHidden ? 'flex' : 'none';
  if (isHidden) document.getElementById('searchInput')?.focus();
}

function closeSearch() {
  const wrap = document.getElementById('searchBarWrap');
  if (wrap) wrap.style.display = 'none';
  const res = document.getElementById('searchResults');
  if (res) res.style.display = 'none';
  const inp = document.getElementById('searchInput');
  if (inp) inp.value = '';
}

function debounceSearch(q) {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => doSearch(q), 320);
}

function doSearch(q) {
  const res  = document.getElementById('searchResults');
  const grid = document.getElementById('searchGrid');
  if (!res || !grid) return;

  if (!q.trim()) { res.style.display = 'none'; return; }

  fetch('/api/search?q=' + encodeURIComponent(q))
    .then(r => r.json())
    .then(songs => {
      res.style.display = 'block';
      if (!songs.length) {
        grid.innerHTML = '<p class="text-muted p-2">No songs found for "' + q + '"</p>';
        return;
      }
      grid.innerHTML = songs.map(s => `
        <div class="song-card" onclick="playSong(${s.id},'${esc(s.title)}','${esc(s.artist)}','/static/${s.image}','/static/${s.file_path}')">
          <div class="card-img-wrap">
            <img src="/static/${s.image}" alt="${esc(s.title)}" onerror="this.src='https://via.placeholder.com/200x200/0f0f1a/7c3aed?text=♪'" />
            <div class="card-play-overlay"><i class="bi bi-play-fill"></i></div>
          </div>
          <div class="card-info">
            <p class="card-title">${esc(s.title)}</p>
            <p class="card-artist">${esc(s.artist)}</p>
          </div>
        </div>`).join('');
    })
    .catch(() => {});
}

function esc(str) {
  return String(str).replace(/'/g, "\\'").replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/* ── Playlists ─────────────────────────────────────────────── */
document.getElementById('addPlaylistBtn')?.addEventListener('click', () => {
  const form = document.getElementById('createPlaylistForm');
  if (form) form.style.display = form.style.display === 'none' ? 'flex' : 'none';
  document.getElementById('playlistNameInput')?.focus();
});

document.getElementById('playlistNameInput')?.addEventListener('keydown', e => {
  if (e.key === 'Enter') createPlaylist();
  if (e.key === 'Escape') {
    document.getElementById('createPlaylistForm').style.display = 'none';
  }
});

function createPlaylist() {
  const inp  = document.getElementById('playlistNameInput');
  const name = inp?.value.trim();
  if (!name) return;

  fetch('/api/create-playlist', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name })
  })
  .then(r => r.json())
  .then(data => {
    if (data.id) {
      const list = document.getElementById('playlistList');
      const empty = list?.querySelector('p');
      if (empty) empty.remove();

      const item = document.createElement('div');
      item.className = 'playlist-item';
      item.dataset.id = data.id;
      item.innerHTML = `<i class="bi bi-music-note-list"></i><span>${esc(data.name)}</span>
        <button class="icon-btn ms-auto" onclick="deletePlaylist(${data.id},this)"><i class="bi bi-x"></i></button>`;
      list?.appendChild(item);

      inp.value = '';
      document.getElementById('createPlaylistForm').style.display = 'none';
    }
  })
  .catch(() => {});
}

function deletePlaylist(id, btn) {
  if (!confirm('Delete this playlist?')) return;
  fetch('/api/delete-playlist', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ playlist_id: id })
  })
  .then(r => r.json())
  .then(() => btn?.closest('.playlist-item')?.remove())
  .catch(() => {});
}

/* ── Sidebar ───────────────────────────────────────────────── */
function toggleSidebar() {
  document.getElementById('sidebar')?.classList.toggle('open');
}

/* ── Genre page list/grid view ─────────────────────────────── */
function setView(view, btn) {
  document.querySelectorAll('.gtv-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const list = document.getElementById('listView');
  const grid = document.getElementById('gridView');
  if (list) list.style.display = view === 'list' ? 'block' : 'none';
  if (grid) grid.style.display = view === 'grid' ? 'grid' : 'none';
}
