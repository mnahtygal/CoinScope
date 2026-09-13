from __future__ import annotations

import atexit
import json
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
from flask import Flask, Response, jsonify, render_template, request, send_from_directory

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CAPTURES = DATA / "captures"
DB = DATA / "coinscope.db"
CATALOG = ROOT / "catalog" / "us_coins.json"
DATA.mkdir(exist_ok=True)
CAPTURES.mkdir(exist_ok=True)

app = Flask(__name__)


def db() -> sqlite3.Connection:
    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                obverse TEXT,
                reverse TEXT,
                country TEXT DEFAULT '',
                denomination TEXT DEFAULT '',
                year TEXT DEFAULT '',
                mint_mark TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                status TEXT DEFAULT 'capturing'
            )
        """)
        columns = {row[1] for row in connection.execute('PRAGMA table_info(scans)')}
        for name, definition in {'grade': "TEXT DEFAULT 'VF'", 'analysis_json': "TEXT DEFAULT ''"}.items():
            if name not in columns:
                connection.execute(f'ALTER TABLE scans ADD COLUMN {name} {definition}')


def analyze_record(payload: dict) -> dict:
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    try:
        year = int(str(payload.get('year', '')).strip())
    except ValueError:
        return {'matched': False, 'message': 'Enter a four-digit year before analysis.'}
    denomination = str(payload.get('denomination', '')).strip()
    mint_mark = str(payload.get('mint_mark', '')).strip().upper()
    matches = [r for r in catalog['records'] if r['country'] == 'USA' and r['denomination'] == denomination and r['year'] == year and r['mint_mark'] == mint_mark]
    if not matches:
        return {'matched': False, 'message': f'{year} {denomination} {mint_mark}'.strip() + ' is not curated yet. The scan remains safely saved.'}
    record = matches[0]
    grade = str(payload.get('grade', 'VF')).upper()
    low, high = record['prices'].get(grade, record['prices']['VF'])
    return {'matched': True, 'grade': grade, 'value_low': low, 'value_high': high, **record}


class Camera:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.capture: cv2.VideoCapture | None = None
        self.index = -1
        self.frame = None
        self.running = True
        self.thread = threading.Thread(target=self._reader, daemon=True)
        self.thread.start()

    def open(self, index: int) -> bool:
        # The page asks to select the default camera after startup. If that
        # camera is already streaming, do not attempt to open the busy V4L2
        # device a second time.
        with self.lock:
            if self.index == index and self.capture is not None and self.capture.isOpened():
                return True

        candidate = cv2.VideoCapture(index, cv2.CAP_V4L2)
        if not candidate.isOpened():
            candidate.release()
            return False
        candidate.set(cv2.CAP_PROP_FRAME_WIDTH, 1600)
        candidate.set(cv2.CAP_PROP_FRAME_HEIGHT, 1200)
        with self.lock:
            old = self.capture
            self.capture = candidate
            self.index = index
        if old:
            old.release()
        return True

    def close(self) -> None:
        self.running = False
        with self.lock:
            if self.capture:
                self.capture.release()

    def _reader(self) -> None:
        while self.running:
            with self.lock:
                cap = self.capture
                ok, frame = cap.read() if cap else (False, None)
                if ok:
                    self.frame = frame
            if not ok:
                time.sleep(0.08)

    def jpg(self) -> bytes | None:
        with self.lock:
            if self.frame is None:
                return None
            ok, encoded = cv2.imencode('.jpg', self.frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
            return encoded.tobytes() if ok else None


camera = Camera()
atexit.register(camera.close)
init_db()


def camera_devices() -> list[dict]:
    devices = []
    for path in sorted(Path('/dev').glob('video*')):
        try:
            index = int(path.name.removeprefix('video'))
        except ValueError:
            continue
        name_path = Path('/sys/class/video4linux') / path.name / 'name'
        name = name_path.read_text().strip() if name_path.exists() else path.name
        devices.append({'index': index, 'path': str(path), 'name': name})
    return devices


@app.get('/')
def home():
    return render_template('index.html')


@app.get('/api/devices')
def devices():
    return jsonify({'devices': camera_devices(), 'active': camera.index})


@app.post('/api/camera')
def select_camera():
    index = int(request.json.get('index', -1))
    return jsonify({'ok': camera.open(index), 'index': index})


@app.get('/video')
def video():
    def frames():
        while True:
            jpg = camera.jpg()
            if jpg:
                yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpg + b'\r\n'
            time.sleep(0.04)
    return Response(frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.post('/api/scans')
def create_scan():
    now = datetime.now(timezone.utc).isoformat()
    with db() as connection:
        cursor = connection.execute('INSERT INTO scans(created_at) VALUES (?)', (now,))
        scan_id = cursor.lastrowid
    (CAPTURES / str(scan_id)).mkdir(exist_ok=True)
    return jsonify({'id': scan_id, 'created_at': now})


@app.post('/api/scans/<int:scan_id>/capture/<side>')
def capture(scan_id: int, side: str):
    if side not in {'obverse', 'reverse'}:
        return jsonify({'error': 'Side must be obverse or reverse'}), 400
    jpg = camera.jpg()
    if not jpg:
        return jsonify({'error': 'No camera frame available'}), 503
    folder = CAPTURES / str(scan_id)
    folder.mkdir(exist_ok=True)
    filename = f'{side}.jpg'
    (folder / filename).write_bytes(jpg)
    relative = f'{scan_id}/{filename}'
    with db() as connection:
        exists = connection.execute('SELECT id FROM scans WHERE id=?', (scan_id,)).fetchone()
        if not exists:
            return jsonify({'error': 'Scan not found'}), 404
        connection.execute(f'UPDATE scans SET {side}=? WHERE id=?', (relative, scan_id))
    image = cv2.imdecode(__import__('numpy').frombuffer(jpg, dtype='uint8'), cv2.IMREAD_GRAYSCALE)
    sharpness = round(float(cv2.Laplacian(image, cv2.CV_64F).var()), 1)
    return jsonify({'ok': True, 'url': f'/captures/{relative}', 'sharpness': sharpness})


@app.put('/api/scans/<int:scan_id>')
def update_scan(scan_id: int):
    payload = request.json or {}
    fields = ['country', 'denomination', 'year', 'mint_mark', 'notes', 'status', 'grade']
    values = [str(payload.get(field, '')) for field in fields]
    with db() as connection:
        connection.execute(
            'UPDATE scans SET country=?, denomination=?, year=?, mint_mark=?, notes=?, status=?, grade=? WHERE id=?',
            (*values, scan_id),
        )
    return jsonify({'ok': True})


@app.post('/api/scans/<int:scan_id>/analyze')
def analyze_scan(scan_id: int):
    payload = request.json or {}
    result = analyze_record(payload)
    with db() as connection:
        connection.execute('UPDATE scans SET analysis_json=?, grade=? WHERE id=?', (json.dumps(result), str(payload.get('grade', 'VF')), scan_id))
    return jsonify(result)


@app.get('/api/scans')
def list_scans():
    with db() as connection:
        rows = connection.execute('SELECT * FROM scans ORDER BY id DESC LIMIT 100').fetchall()
    return jsonify({'scans': [dict(row) for row in rows]})


@app.get('/captures/<path:name>')
def captures(name: str):
    return send_from_directory(CAPTURES, name)


if __name__ == '__main__':
    devices_found = camera_devices()
    if devices_found:
        camera.open(devices_found[-1]['index'])
    print('\nCoinScope is ready: http://127.0.0.1:5050\n')
    app.run(host='127.0.0.1', port=5050, threaded=True)
