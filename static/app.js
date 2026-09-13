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
  $('grade-status').textContent=''; $('detect-status').textContent='';
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
    const response=await fetch(`/api/scans/${scanId}/identify`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({denomination_hint:$('denomination').value})}); const result=await response.json();
    if(!response.ok||!result.ok){$('detect-status').textContent=result.message||'Detection failed.';return;}
    $('denomination').value=result.denomination; $('year').value=result.year; $('mint_mark').value=result.mint_mark;
    const dc=Math.round(result.denomination_confidence*100), yc=Math.round(result.year_confidence*100), mc=Math.round(result.mint_confidence*100);
    $('detect-status').textContent=`${result.coin_series||'Coin'}${result.coin_variant?' • '+result.coin_variant:''} • ${result.denomination}${result.denomination_text?' • read “'+result.denomination_text+'”':''} • ${result.year}${result.mint_mark?'-'+result.mint_mark:''} • confidence ${dc}/${yc}/${mc}%`;
  } finally {$('detect-date').disabled=false;}
}

async function gradeCoin(){
  if(!scanId) return;
  $('grade-status').textContent='Gemma is estimating a conservative grade…';
  const response=await fetch(`/api/scans/${scanId}/grade`,{method:'POST'}); const result=await response.json();
  if(!response.ok||!result.ok){$('grade-status').textContent=result.message||'Automatic grading failed.';return;}
  $('grade').value=result.grade;
  $('grade-status').textContent=`AI screening grade ${result.grade} • ${Math.round(result.confidence*100)}% confidence${result.reason?' • '+result.reason:''}`;
}

async function captureSide(side) {
  if(!scanId) await newScan();
  const response=await fetch(`/api/scans/${scanId}/capture/${side}`,{method:'POST'}); const data=await response.json();
  if(!response.ok) return alert(data.error);
  $(side).innerHTML=`<img src="${data.url}?t=${Date.now()}" alt="${side}">`;
  $(`${side}-quality`).textContent=`Focus score: ${data.sharpness} ${data.sharpness>120?'• Sharp':'• Try adjusting focus'}`;
  if(side==='reverse' && $('obverse').querySelector('img')) { await identifyCoin(); await gradeCoin(); }
}

async function save() {
  if(!scanId) return alert('Capture a coin first.');
  const payload=Object.fromEntries(fields.map(f=>[f,$(f).value])); payload.status='saved';
  const result=await fetch(`/api/scans/${scanId}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json());
  $('scan-title').textContent=[payload.year,payload.denomination].filter(Boolean).join(' ')||'Saved coin';
  if(result.location?.storage_status==='hold') $('detect-status').textContent=`⚠ HOLD — DO NOT TUBE • ${result.location.hold_reason}`;
  else if(result.location?.tube_number) $('detect-status').textContent=`Stored in ${result.location.tube_label} Tube ${String(result.location.tube_number).padStart(3,'0')} • position ${String(result.location.tube_position).padStart(2,'0')}/${result.location.capacity}`;
  await loadHistory();
  await analyze();
}

async function loadHistory(){
  const {scans}=await fetch('/api/scans').then(r=>r.json()); $('count').textContent=`${scans.length} coin${scans.length===1?'':'s'}`;
  const capacities={'1c':50,'5c':40,'10c':50,'25c':40,'50c':20,'1 Dollar':20,'Silver Dollar':20}; const labels={'1c':'1C','5c':'5C','10c':'10C','25c':'25C','50c':'50C','1 Dollar':'DOLLAR','Silver Dollar':'DOLLAR'};
  $('history').innerHTML=scans.length?scans.map(s=>`<div class="history-item${s.storage_status==='hold'?' hold-item':''}">${s.obverse?`<img src="/captures/${s.obverse}">`:'<div class="history-placeholder">◉</div>'}<div><b>${[s.year,s.denomination].filter(Boolean).join(' ')||`Scan #${s.id}`}</b><small>${s.country||'Identification pending'}</small>${s.storage_status==='hold'?`<small class="hold-label">⚠ HOLD — DO NOT TUBE</small>`:s.tube_number?`<small>${labels[s.denomination]||s.denomination.toUpperCase()} Tube ${String(s.tube_number).padStart(3,'0')} • ${String(s.tube_position).padStart(2,'0')}/${capacities[s.denomination]||'?'}</small>`:''}<small>${new Date(s.created_at).toLocaleString()}</small></div></div>`).join(''):'<p>No saved coins yet. Put one under the microscope and start scanning.</p>';
  await loadCollectionSummary();
}

async function loadCollectionSummary(){
  const s=await fetch('/api/collection-summary').then(r=>r.json());
  $('collection-value').textContent=`$${s.value_low.toFixed(2)}–$${s.value_high.toFixed(2)}`;
  $('tube-summary').innerHTML=s.tubes.length?s.tubes.map(t=>`<div class="tube-card"><b>${t.label} Tube ${String(t.tube_number).padStart(3,'0')}</b><span>${t.count}/${t.capacity}</span><progress value="${t.count}" max="${t.capacity}"></progress><small>$${t.value_low.toFixed(2)}–$${t.value_high.toFixed(2)}</small></div>`).join(''):'<p>No filled tube positions yet.</p>';
  const coverage=`${s.priced_count} collector-priced${s.face_value_count?` • ${s.face_value_count} at face value`:''}`;
  $('hold-summary').textContent=s.hold_count?`⚠ ${s.hold_count} coin${s.hold_count===1?'':'s'} held out for inspection • ${coverage}`:coverage;
  $('metric-total').textContent=s.coin_count; $('metric-tubed').textContent=s.tubed_count; $('metric-held').textContent=s.hold_count;
  $('metric-value').textContent=`$${s.value_low.toFixed(2)}–$${s.value_high.toFixed(2)}`;
  $('report-time').textContent=`Updated ${new Date(s.generated_at).toLocaleString()}`;
  $('denomination-report').innerHTML=s.denominations.map(d=>`<tr><td>${d.denomination}</td><td>${d.count}</td><td>${d.tubed}</td><td>${d.held}</td><td>$${d.value_low.toFixed(2)}–$${d.value_high.toFixed(2)}</td></tr>`).join('');
  const maxGrade=Math.max(1,...Object.values(s.grades));
  $('grade-report').innerHTML=Object.entries(s.grades).map(([grade,count])=>`<div class="grade-row"><b>${grade}</b><span><i style="width:${count/maxGrade*100}%"></i></span><strong>${count}</strong></div>`).join('')||'<p>No grades recorded yet.</p>';
  $('hold-report').innerHTML=s.hold_items.length?s.hold_items.map(c=>`<div class="hold-row"><b>#${c.id} • ${c.year}${c.mint_mark?'-'+c.mint_mark:''} ${c.denomination}</b><span>${c.grade||'Ungraded'} • up to $${c.value_high.toFixed(2)}</span><small>${c.reason||'Collector inspection required'}</small></div>`).join(''):'<p>No coins are currently held aside.</p>';
}

$('refresh').onclick=loadDevices; $('camera').onchange=e=>chooseCamera(e.target.value); $('new-scan').onclick=newScan; $('save').onclick=save; $('analyze').onclick=analyze; $('detect-date').onclick=identifyCoin;
document.querySelectorAll('[data-side]').forEach(b=>b.onclick=()=>captureSide(b.dataset.side));
$('print-report').onclick=()=>window.print();
loadDevices(); loadHistory();
