let scanId = null;
const $ = id => document.getElementById(id);
const fields = ['country','denomination','year','mint_mark','notes','grade'];

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
  try {
    const response = await fetch('/api/camera', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({index:Number(index)})});
    const data = await response.json();
    setCameraStatus(data.ok, data.ok ? 'Microscope live' : 'Camera is busy — close other camera apps');
    if (data.ok) $('feed').src = `/video?t=${Date.now()}`;
  } catch (error) {
    setCameraStatus(false, 'CoinScope connection lost — restart the app');
  }
}

function setCameraStatus(live, text) { $('camera-status').textContent=text; $('camera-status').parentElement.classList.toggle('live',live); $('no-camera').style.display=live?'none':'block'; }

async function newScan() {
  const data = await fetch('/api/scans',{method:'POST'}).then(r=>r.json());
  scanId=data.id; $('scan-id').textContent=`#${scanId}`; $('scan-title').textContent='Capturing coin';
  for(const side of ['obverse','reverse']) { $(side).innerHTML='<b>Not captured</b>'; $(`${side}-quality`).textContent=''; }
  fields.forEach(f=>$(f).value='');
  $('country').value='USA'; $('grade').value='VF';
}

async function analyze(){
  if(!scanId) return alert('Capture a coin first.');
  const payload=Object.fromEntries(fields.map(f=>[f,$(f).value]));
  const result=await fetch(`/api/scans/${scanId}/analyze`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json());
  if(!result.matched){$('analysis').innerHTML=`<div class="analysis-icon">?</div><div><h3>Not curated yet</h3><p>${result.message}</p></div>`;return;}
  const checks=result.checks.map(c=>`<li class="${c.severity}"><b>${c.name}</b> — ${c.instruction}<small>${c.potential}</small></li>`).join('');
  $('analysis').innerHTML=`<div class="analysis-icon">✦</div><div><h3>${result.name}</h3><p>${result.mint} • ${result.composition} • ${result.weight_g} g • ${result.diameter_mm} mm</p><div class="value">$${result.value_low.toFixed(2)}–$${result.value_high.toFixed(2)} <small>estimated ${result.grade}</small></div><p class="source">${result.price_source} • updated ${result.price_updated}</p><h4>Collector checks</h4><ul class="checks">${checks}</ul><a href="${result.source_url}" target="_blank" rel="noopener">Open reference source</a></div>`;
}

async function identifyCoin(){
  if(!scanId) return alert('Capture both sides of a coin first.');
  $('detect-date').disabled=true; $('detect-status').textContent='Gemma is identifying both sides…';
  try{
    const response=await fetch(`/api/scans/${scanId}/identify`,{method:'POST'}); const result=await response.json();
    if(!response.ok||!result.ok){$('detect-status').textContent=result.message||'Detection failed.';return;}
    $('denomination').value=result.denomination; $('year').value=result.year; $('mint_mark').value=result.mint_mark;
    const dc=Math.round(result.denomination_confidence*100), yc=Math.round(result.year_confidence*100), mc=Math.round(result.mint_confidence*100);
    $('detect-status').textContent=`${result.coin_series||'Coin'} • ${result.denomination} • ${result.year}${result.mint_mark?'-'+result.mint_mark:''} • confidence ${dc}/${yc}/${mc}%`;
  } finally {$('detect-date').disabled=false;}
}

async function captureSide(side) {
  if(!scanId) await newScan();
  const response=await fetch(`/api/scans/${scanId}/capture/${side}`,{method:'POST'}); const data=await response.json();
  if(!response.ok) return alert(data.error);
  $(side).innerHTML=`<img src="${data.url}?t=${Date.now()}" alt="${side}">`;
  $(`${side}-quality`).textContent=`Focus score: ${data.sharpness} ${data.sharpness>120?'• Sharp':'• Try adjusting focus'}`;
  if(side==='reverse' && $('obverse').querySelector('img')) await identifyCoin();
}

async function save() {
  if(!scanId) return alert('Capture a coin first.');
  const payload=Object.fromEntries(fields.map(f=>[f,$(f).value])); payload.status='saved';
  const result=await fetch(`/api/scans/${scanId}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json());
  $('scan-title').textContent=[payload.year,payload.denomination].filter(Boolean).join(' ')||'Saved coin';
  if(result.location?.tube_number) $('detect-status').textContent=`Stored in 1C Tube ${String(result.location.tube_number).padStart(3,'0')} • position ${String(result.location.tube_position).padStart(2,'0')}/50`;
  await loadHistory();
}

async function loadHistory(){
  const {scans}=await fetch('/api/scans').then(r=>r.json()); $('count').textContent=`${scans.length} coin${scans.length===1?'':'s'}`;
  $('history').innerHTML=scans.length?scans.map(s=>`<div class="history-item">${s.obverse?`<img src="/captures/${s.obverse}">`:'<div class="history-placeholder">◉</div>'}<div><b>${[s.year,s.denomination].filter(Boolean).join(' ')||`Scan #${s.id}`}</b><small>${s.country||'Identification pending'}</small>${s.tube_number?`<small>1C Tube ${String(s.tube_number).padStart(3,'0')} • ${String(s.tube_position).padStart(2,'0')}/50</small>`:''}<small>${new Date(s.created_at).toLocaleString()}</small></div></div>`).join(''):'<p>No saved coins yet. Put one under the microscope and start scanning.</p>';
}

$('refresh').onclick=loadDevices; $('camera').onchange=e=>chooseCamera(e.target.value); $('new-scan').onclick=newScan; $('save').onclick=save; $('analyze').onclick=analyze; $('detect-date').onclick=identifyCoin;
document.querySelectorAll('[data-side]').forEach(b=>b.onclick=()=>captureSide(b.dataset.side));
loadDevices(); loadHistory();
