// 사이트 전체 무결성 점검. 빌드 전에 돌린다.
const fs = require('fs'), path = require('path');
const ROOT = path.dirname(__dirname);
const imgs = new Set(fs.existsSync(path.join(ROOT, 'images')) ? fs.readdirSync(path.join(ROOT, 'images')) : []);
const concepts = new Set(fs.existsSync(path.join(ROOT, 'concepts'))
  ? fs.readdirSync(path.join(ROOT, 'concepts')).filter(f => f.endsWith('.json')).map(f => f.slice(0, -5)) : []);
const BAN = /[→←⇒—–]|--|✓|❌|⭐/;
let n = 0, warn = [];
for (const sec of fs.readdirSync(path.join(ROOT, 'questions'))) {
  const dir = path.join(ROOT, 'questions', sec);
  if (!fs.statSync(dir).isDirectory()) continue;
  for (const f of fs.readdirSync(dir).filter(x => x.endsWith('.json'))) {
    const q = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8'));
    if (q.excluded) continue;
    n++;
    const tag = `${sec}/q${q.id}`;
    if (q.section !== sec) warn.push(`${tag} 분과 불일치 (${q.section})`);
    (q.images_final || []).forEach(i => { if (!imgs.has(i)) warn.push(`${tag} 이미지 없음 ${i}`); });
    (q.explanation?.concepts || []).forEach(c => { if (!concepts.has(c)) warn.push(`${tag} 끊긴 정리 카드 ${c}`); });
    if (BAN.test(JSON.stringify(q))) warn.push(`${tag} 금지 문장부호`);
    if (!q.explanation?.qtype) warn.push(`${tag} qtype 없음`);
    const mode = q.optnotes_mode || 'full';
    const cnt = Object.keys(q.optnotes || {}).length;
    if (mode === 'none' && cnt) warn.push(`${tag} optnotes_mode none인데 해설 ${cnt}개`);
    if (mode !== 'none' && cnt !== q.options.length) warn.push(`${tag} 선지해설 ${cnt}/${q.options.length}`);
  }
}
let cn = 0;
for (const s of concepts) {
  const c = JSON.parse(fs.readFileSync(path.join(ROOT, 'concepts', s + '.json'), 'utf8')); cn++;
  if (BAN.test(JSON.stringify(c))) warn.push(`정리/${s} 금지 문장부호`);
  if (!/<table|class="flow"/.test(c.body || '')) warn.push(`정리/${s} 판단표나 프로토콜 없음`);
  const bad = [...(c.body || '').matchAll(/<(\w+)/g)].map(m => m[1])
    .filter(t => !['h3','p','table','thead','tbody','tr','th','td','ul','ol','li','strong','em','code'].includes(t));
  if (bad.length) warn.push(`정리/${s} 비허용 태그 ${[...new Set(bad)].join(',')}`);
}
console.log(`문항 ${n}, 정리 카드 ${cn}`);
console.log(warn.length ? '경고:\n  ' + warn.join('\n  ') : '경고 없음');
