from __future__ import annotations

import atexit
import base64
import json
import re
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

import cv2
from flask import Flask, Response, jsonify, render_template, request, send_from_directory

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CAPTURES = DATA / "captures"
DB = DATA / "coinscope.db"
CATALOG = ROOT / "catalog" / "us_coins.json"
VISION_URL = "http://127.0.0.1:8081/v1/chat/completions"
HOLD_VALUE_THRESHOLD = 5.00
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
        columns = {row[1] for row in connection.execute('PRAGMA table_info(scans)')}
        for name, definition in {
            'coin_series': "TEXT DEFAULT ''",
            'tube_number': 'INTEGER',
            'tube_position': 'INTEGER',
            'grade_confidence': 'REAL',
            'grade_reason': "TEXT DEFAULT ''",
            'storage_status': "TEXT DEFAULT 'unassigned'",
            'hold_reason': "TEXT DEFAULT ''",
        }.items():
            if name not in columns:
                connection.execute(f'ALTER TABLE scans ADD COLUMN {name} {definition}')


def analyze_record(payload: dict) -> dict:
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    try:
        year = int(str(payload.get('year', '')).strip())
    except ValueError:
        return {'matched': False, 'message': 'Enter a four-digit year before analysis.'}
    if year < 1792 or year > datetime.now().year + 1:
        return {'matched': False, 'message': 'Enter a valid four-digit U.S. coin year.'}
    denomination = str(payload.get('denomination', '')).strip()
    mint_mark = str(payload.get('mint_mark', '')).strip().upper()
    if denomination == '1c' and year == 2026:
        return {
            'matched': False,
            'message': catalog.get('scope', {}).get(
                '2026_status', 'No circulating United States cent was issued for 2026.'
            ),
        }
    matches = [r for r in catalog['records'] if r['country'] == 'USA' and r['denomination'] == denomination and r['year'] == year and r['mint_mark'] == mint_mark]
    if not matches:
        return {'matched': False, 'message': f'{year} {denomination} {mint_mark}'.strip() + ' is not curated yet. The scan remains safely saved.'}
    detected_series = str(payload.get('coin_series', '')).lower()
    if len(matches) > 1 and detected_series:
        ignored = {'cent', 'coin', 'united', 'states', 'the', 'reverse'}
        wanted = set(re.findall(r'[a-z]+', detected_series)) - ignored
        record = max(matches, key=lambda item: len(wanted & (set(re.findall(r'[a-z]+', item['series'].lower())) - ignored)))
    else:
        record = matches[0]
    grade = str(payload.get('grade', 'VF')).upper()
    low, high = record['prices'].get(grade, record['prices']['VF'])
    date_checks = record.get('checks', [])
    checks = [*date_checks, *catalog.get('universal_error_checks', [])]
    return {'matched': True, 'grade': grade, 'value_low': low, 'value_high': high,
            **record, 'checks': checks, 'date_specific_checks': date_checks}


def detect_year_and_mint(image_path: Path) -> dict:
    encoded = base64.b64encode(image_path.read_bytes()).decode('ascii')
    prompt = (
        'Examine this United States coin obverse. Read only the visible four-digit mint year '
        'and mint mark near the date. Mint mark must be D, S, P, or blank. Do not infer from '
        'rarity or coin history. Return only compact JSON with keys year, mint_mark, '
        'year_confidence, and mint_confidence.'
    )
    body = json.dumps({
        'model': 'ggml-org/gemma-3-4b-it-qat-GGUF',
        'temperature': 0,
        'max_tokens': 150,
        'messages': [{'role': 'user', 'content': [
            {'type': 'text', 'text': prompt},
            {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{encoded}'}},
        ]}],
    }).encode('utf-8')
    request_data = Request(VISION_URL, data=body, headers={'Content-Type': 'application/json'})
    try:
        with urlopen(request_data, timeout=120) as response:
            api_result = json.loads(response.read())
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        return {'ok': False, 'message': f'Local Gemma vision is unavailable: {error}'}
    content = api_result.get('choices', [{}])[0].get('message', {}).get('content', '')
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if not match:
        return {'ok': False, 'message': 'Gemma did not return readable year/mint JSON.'}
    try:
        detected = json.loads(match.group(0))
        year = int(detected['year'])
        mint = str(detected.get('mint_mark', '')).strip().upper()
        if year < 1792 or year > datetime.now().year + 1 or mint not in {'', 'P', 'D', 'S'}:
            raise ValueError('invalid year or mint mark')
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return {'ok': False, 'message': 'Gemma returned an invalid year or mint mark.'}
    return {
        'ok': True, 'year': year, 'mint_mark': mint,
        'year_confidence': float(detected.get('year_confidence', 0)),
        'mint_confidence': float(detected.get('mint_confidence', 0)),
    }


def identify_coin(obverse_path: Path, reverse_path: Path) -> dict:
    def data_url(path: Path) -> str:
        encoded = base64.b64encode(path.read_bytes()).decode('ascii')
        return f'data:image/jpeg;base64,{encoded}'

    prompt = (
        'These are the obverse and reverse of the same United States coin. Read only what is '
        'visible in the images. Identify the denomination, four-digit year, mint mark, and coin '
        'series. Denomination must be exactly one of: 1c, 5c, 10c, 25c, 50c, Silver Dollar. '
        'Mint mark must be D, S, P, or blank. Return only compact JSON with keys denomination, '
        'year, mint_mark, coin_series, denomination_confidence, year_confidence, mint_confidence.'
    )
    body = json.dumps({
        'model': 'ggml-org/gemma-3-4b-it-qat-GGUF',
        'temperature': 0,
        'max_tokens': 180,
        'messages': [{'role': 'user', 'content': [
            {'type': 'text', 'text': prompt},
            {'type': 'image_url', 'image_url': {'url': data_url(obverse_path)}},
            {'type': 'image_url', 'image_url': {'url': data_url(reverse_path)}},
        ]}],
    }).encode('utf-8')
    request_data = Request(VISION_URL, data=body, headers={'Content-Type': 'application/json'})
    try:
        with urlopen(request_data, timeout=120) as response:
            api_result = json.loads(response.read())
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        return {'ok': False, 'message': f'Local Gemma vision is unavailable: {error}'}
    content = api_result.get('choices', [{}])[0].get('message', {}).get('content', '')
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if not match:
        return {'ok': False, 'message': 'Gemma did not return readable coin JSON.'}
    try:
        detected = json.loads(match.group(0))
        year = int(detected['year'])
        mint = str(detected.get('mint_mark', '')).strip().upper()
        denomination = str(detected['denomination']).strip()
        valid_denominations = {'1c', '5c', '10c', '25c', '50c', 'Silver Dollar'}
        if year < 1792 or year > datetime.now().year + 1:
            raise ValueError('invalid year')
        if mint not in {'', 'P', 'D', 'S'} or denomination not in valid_denominations:
            raise ValueError('invalid denomination or mint mark')
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return {'ok': False, 'message': 'Gemma returned invalid coin identification data.'}
    return {
        'ok': True, 'denomination': denomination, 'year': year, 'mint_mark': mint,
        'coin_series': str(detected.get('coin_series', '')).strip(),
        'denomination_confidence': float(detected.get('denomination_confidence', 0)),
        'year_confidence': float(detected.get('year_confidence', 0)),
        'mint_confidence': float(detected.get('mint_confidence', 0)),
    }


def estimate_grade(obverse_path: Path, reverse_path: Path) -> dict:
    def data_url(path: Path) -> str:
        encoded = base64.b64encode(path.read_bytes()).decode('ascii')
        return f'data:image/jpeg;base64,{encoded}'

    prompt = (
        'Estimate a conservative screening grade for this United States coin from the obverse '
        'and reverse photographs. Judge visible wear on high points, remaining detail, rims, '
        'surface damage, and apparent luster. Do not claim professional certification. Grade '
        'must be exactly one of G, F, VF, XF, AU, or MS. When uncertain choose the lower grade. '
        'Return only compact JSON with keys grade, confidence, and reason. Keep reason under 140 characters.'
    )
    body = json.dumps({
        'model': 'ggml-org/gemma-3-4b-it-qat-GGUF', 'temperature': 0,
        'max_tokens': 160,
        'messages': [{'role': 'user', 'content': [
            {'type': 'text', 'text': prompt},
            {'type': 'image_url', 'image_url': {'url': data_url(obverse_path)}},
            {'type': 'image_url', 'image_url': {'url': data_url(reverse_path)}},
        ]}],
    }).encode('utf-8')
    request_data = Request(VISION_URL, data=body, headers={'Content-Type': 'application/json'})
    try:
        with urlopen(request_data, timeout=120) as response:
            api_result = json.loads(response.read())
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        return {'ok': False, 'message': f'Local Gemma grading is unavailable: {error}'}
    content = api_result.get('choices', [{}])[0].get('message', {}).get('content', '')
    match = re.search(r'\{.*\}', content, re.DOTALL)
    try:
        detected = json.loads(match.group(0)) if match else {}
        grade = str(detected['grade']).strip().upper()
        confidence = max(0.0, min(1.0, float(detected.get('confidence', 0))))
        reason = str(detected.get('reason', '')).strip()[:140]
        if grade not in {'G', 'F', 'VF', 'XF', 'AU', 'MS'}:
            raise ValueError('invalid grade')
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return {'ok': False, 'message': 'Gemma returned invalid grading data.'}
    return {'ok': True, 'grade': grade, 'confidence': confidence, 'reason': reason}


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
        candidate.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
        candidate.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
        candidate.set(cv2.CAP_PROP_FPS, 21)
        candidate.set(cv2.CAP_PROP_BUFFERSIZE, 1)
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
                with self.lock:
                    self.frame = frame
            if not ok:
                time.sleep(0.08)

    def jpg(self) -> bytes | None:
        with self.lock:
            if self.frame is None:
                return None
            frame = self.frame.copy()
        ok, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
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
        existing = connection.execute('SELECT coin_series, tube_number, tube_position FROM scans WHERE id=?', (scan_id,)).fetchone()
        if not existing:
            return jsonify({'error': 'Scan not found'}), 404
        connection.execute(
            'UPDATE scans SET country=?, denomination=?, year=?, mint_mark=?, notes=?, status=?, grade=? WHERE id=?',
            (*values, scan_id),
        )
        storage = {'storage_status': 'unassigned'}
        analysis = None
        if payload.get('status') == 'saved' and payload.get('denomination') == '1c':
            analysis_payload = {**payload, 'coin_series': existing['coin_series'] or ''}
            analysis = analyze_record(analysis_payload)
            critical_checks = [c for c in analysis.get('date_specific_checks', []) if c.get('severity') == 'critical'] if analysis.get('matched') else []
            high_value = analysis.get('matched') and float(analysis.get('value_high', 0)) >= HOLD_VALUE_THRESHOLD
            if high_value or critical_checks:
                reasons = []
                if high_value:
                    reasons.append(f"estimated {analysis['grade']} range reaches ${analysis['value_high']:.2f}")
                if critical_checks:
                    reasons.append('critical date-specific collector check')
                hold_reason = '; '.join(reasons)
                connection.execute(
                    "UPDATE scans SET tube_number=NULL, tube_position=NULL, storage_status='hold', hold_reason=?, analysis_json=? WHERE id=?",
                    (hold_reason, json.dumps(analysis), scan_id),
                )
                storage = {'storage_status': 'hold', 'hold_reason': hold_reason}
            else:
                tube_number, tube_position = existing['tube_number'], existing['tube_position']
                if tube_number is None:
                    last = connection.execute("SELECT MAX((tube_number - 1) * 50 + tube_position) FROM scans WHERE denomination='1c'").fetchone()[0] or 0
                    sequence = last + 1
                    tube_number = ((sequence - 1) // 50) + 1
                    tube_position = ((sequence - 1) % 50) + 1
                connection.execute(
                    "UPDATE scans SET tube_number=?, tube_position=?, storage_status='tube', hold_reason='', analysis_json=? WHERE id=?",
                    (tube_number, tube_position, json.dumps(analysis), scan_id),
                )
                storage = {'storage_status': 'tube', 'tube_number': tube_number, 'tube_position': tube_position}
    return jsonify({'ok': True, 'location': storage, 'analysis': analysis})


@app.post('/api/scans/<int:scan_id>/analyze')
def analyze_scan(scan_id: int):
    payload = request.json or {}
    with db() as connection:
        scan = connection.execute('SELECT coin_series FROM scans WHERE id=?', (scan_id,)).fetchone()
    if scan and scan['coin_series']:
        payload['coin_series'] = scan['coin_series']
    result = analyze_record(payload)
    with db() as connection:
        connection.execute('UPDATE scans SET analysis_json=?, grade=? WHERE id=?', (json.dumps(result), str(payload.get('grade', 'VF')), scan_id))
    return jsonify(result)


@app.post('/api/scans/<int:scan_id>/detect-date')
def detect_scan_date(scan_id: int):
    with db() as connection:
        scan = connection.execute('SELECT obverse FROM scans WHERE id=?', (scan_id,)).fetchone()
    if not scan or not scan['obverse']:
        return jsonify({'ok': False, 'message': 'Capture the front/obverse first.'}), 400
    image_path = CAPTURES / scan['obverse']
    if not image_path.is_file():
        return jsonify({'ok': False, 'message': 'The obverse image file is missing.'}), 404
    result = detect_year_and_mint(image_path)
    if result['ok']:
        with db() as connection:
            connection.execute('UPDATE scans SET year=?, mint_mark=? WHERE id=?', (str(result['year']), result['mint_mark'], scan_id))
    return jsonify(result), 200 if result['ok'] else 503


@app.post('/api/scans/<int:scan_id>/identify')
def identify_scan(scan_id: int):
    with db() as connection:
        scan = connection.execute('SELECT obverse, reverse FROM scans WHERE id=?', (scan_id,)).fetchone()
    if not scan or not scan['obverse'] or not scan['reverse']:
        return jsonify({'ok': False, 'message': 'Capture both front and back first.'}), 400
    obverse_path, reverse_path = CAPTURES / scan['obverse'], CAPTURES / scan['reverse']
    if not obverse_path.is_file() or not reverse_path.is_file():
        return jsonify({'ok': False, 'message': 'One or both scan images are missing.'}), 404
    result = identify_coin(obverse_path, reverse_path)
    if result['ok']:
        with db() as connection:
            connection.execute(
                'UPDATE scans SET denomination=?, year=?, mint_mark=?, coin_series=? WHERE id=?',
                (result['denomination'], str(result['year']), result['mint_mark'], result['coin_series'], scan_id),
            )
    return jsonify(result), 200 if result['ok'] else 503


@app.post('/api/scans/<int:scan_id>/grade')
def grade_scan(scan_id: int):
    with db() as connection:
        scan = connection.execute('SELECT obverse, reverse FROM scans WHERE id=?', (scan_id,)).fetchone()
    if not scan or not scan['obverse'] or not scan['reverse']:
        return jsonify({'ok': False, 'message': 'Capture both front and back first.'}), 400
    obverse_path, reverse_path = CAPTURES / scan['obverse'], CAPTURES / scan['reverse']
    if not obverse_path.is_file() or not reverse_path.is_file():
        return jsonify({'ok': False, 'message': 'One or both scan images are missing.'}), 404
    result = estimate_grade(obverse_path, reverse_path)
    if result['ok']:
        with db() as connection:
            connection.execute(
                'UPDATE scans SET grade=?, grade_confidence=?, grade_reason=? WHERE id=?',
                (result['grade'], result['confidence'], result['reason'], scan_id),
            )
    return jsonify(result), 200 if result['ok'] else 503


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
        preferred = next((d for d in devices_found if 'microscope' in d['name'].lower() and d['index'] % 2 == 0), devices_found[0])
        camera.open(preferred['index'])
    print('\nCoinScope is ready: http://127.0.0.1:5050\n')
    app.run(host='127.0.0.1', port=5050, threaded=True)
