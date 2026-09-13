let scanId = null;
const $ = id => document.getElementById(id);
$('feed').addEventListener('load', () => {
  setCameraStatus(true, 'Microscope live');
});
const fields = ['country','denomination','year','mint_mark','notes'];

async function loadDevices() {
  const data = await fetch('/api/devices').then(r => r.json());
  $('camera').innerHTML = data.devices.length ? data.devices.map(d => `<option value="${d.index}">${d.name} — ${d.path}</option>`).join('') : '<option>No camera detected</option>';
  if (data.devices.length) {
    const chosen = data.active >= 0 ? data.active : data.devices[data.devices.length - 1].index;
    $('camera').value = chosen;
    await chooseCamera(chosen);
  } else setCameraStatus(false, 'No microscope detected');
}

async function chooseCamera(index) {
  setCameraStatus(false, 'Opening camera…');
  const data = await fetch('/api/camera', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({index:Number(index)})}).then(r => r.json());
  setCameraStatus(data.ok, data.ok ? 'Microscope live' : 'Could not open camera');
  if (data.ok) $('feed').src = `/video?t=${Date.now()}`;
}

function setCameraStatus(live, text) { $('camera-status').textContent=text; $('camera-status').parentElement.classList.toggle('live',live); $('no-camera').style.display=live?'none':'block'; }

async function newScan() {
  const data = await fetch('/api/scans',{method:'POST'}).then(r=>r.json());
  scanId=data.id; $('scan-id').textContent=`#${scanId}`; $('scan-title').textContent='Capturing coin';
  for(const side of ['obverse','reverse']) { $(side).innerHTML='<b>Not captured</b>'; $(`${side}-quality`).textContent=''; }
  fields.forEach(f=>$(f).value='');
  $('country').value='USA';
}

async function captureSide(side) {
  if(!scanId) await newScan();
  const response=await fetch(`/api/scans/${scanId}/capture/${side}`,{method:'POST'}); const data=await response.json();
  if(!response.ok) return alert(data.error);
  $(side).innerHTML=`<img src="${data.url}?t=${Date.now()}" alt="${side}">`;
  $(`${side}-quality`).textContent=`Focus score: ${data.sharpness} ${data.sharpness>120?'• Sharp':'• Try adjusting focus'}`;
}

async function save() {
  if(!scanId) return alert('Capture a coin first.');
  const payload=Object.fromEntries(fields.map(f=>[f,$(f).value])); payload.status='saved';
  await fetch(`/api/scans/${scanId}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  $('scan-title').textContent=[payload.year,payload.denomination].filter(Boolean).join(' ')||'Saved coin'; await loadHistory();
}

async function loadHistory(){
  const {scans}=await fetch('/api/scans').then(r=>r.json()); $('count').textContent=`${scans.length} coin${scans.length===1?'':'s'}`;
  $('history').innerHTML=scans.length?scans.map(s=>`<div class="history-item">${s.obverse?`<img src="/captures/${s.obverse}">`:'<div class="history-placeholder">◉</div>'}<div><b>${[s.year,s.denomination].filter(Boolean).join(' ')||`Scan #${s.id}`}</b><small>${s.country||'Identification pending'}</small><small>${new Date(s.created_at).toLocaleString()}</small></div></div>`).join(''):'<p>No saved coins yet. Put one under the microscope and start scanning.</p>';
}

$('refresh').onclick=loadDevices; $('camera').onchange=e=>chooseCamera(e.target.value); $('new-scan').onclick=newScan; $('save').onclick=save;
document.querySelectorAll('[data-side]').forEach(b=>b.onclick=()=>captureSide(b.dataset.side));
loadDevices(); loadHistory();

