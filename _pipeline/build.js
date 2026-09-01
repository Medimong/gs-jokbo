// questions/**/q*.json -> data.js (사이트가 읽는 단일 번들)
const fs = require('fs'), path = require('path');
const ROOT = path.dirname(__dirname);
const qdir = path.join(ROOT, 'questions');
const SEC_ORDER = ['LV','BP','BR','ENDO','UGI','CR','VS','PDS','TACS','TX','총론'];
const SEC_NAME = { LV:'간(Liver)', BP:'담도췌장(Biliary·Pancreas)', BR:'유방(Breast)',
  ENDO:'내분비(Endocrine)', UGI:'상부위장관(Upper GI)', CR:'대장항문(Colorectal)',
  VS:'혈관(Vascular)', PDS:'소아외과(Pediatric Surgery)', TACS:'외상·급성기(Trauma·Acute Care)',
  TX:'이식(Transplantation)', '총론':'총론(General Principles)' };

let qs = [];
if (fs.existsSync(qdir)) for (const sec of fs.readdirSync(qdir)) {
  const d = path.join(qdir, sec);
  if (!fs.statSync(d).isDirectory()) continue;
  for (const f of fs.readdirSync(d).filter(f => f.endsWith('.json'))) {
    const q = JSON.parse(fs.readFileSync(path.join(d, f), 'utf8'));
    if (q.excluded) continue;   // 중복으로 판정돼 다른 문항에 합쳐진 것
    qs.push(q);
  }
}
// 비슷한 문항끼리 이웃하도록: 분과, 주제, 출제횟수 순
qs.sort((a, b) => (SEC_ORDER.indexOf(a.section) - SEC_ORDER.indexOf(b.section))
  || String(a.topic || '').localeCompare(String(b.topic || ''))
  || (b.examCount || 1) - (a.examCount || 1) || a.id - b.id);

const cdir = path.join(ROOT, 'concepts');
let concepts = {};
if (fs.existsSync(cdir)) for (const f of fs.readdirSync(cdir).filter(f => f.endsWith('.json'))) {
  const c = JSON.parse(fs.readFileSync(path.join(cdir, f), 'utf8'));
  concepts[c.slug] = c;
}
for (const c of Object.values(concepts)) c.questions = [];
for (const q of qs) for (const s of (q.explanation?.concepts || []))
  if (concepts[s]) concepts[s].questions.push(q.id);

const used = new Set(qs.flatMap(q => q.images_final || []));
const bundle = { meta: { built: new Date().toISOString().slice(0, 10),
    count: qs.length, sections: SEC_ORDER.filter(s => qs.some(q => q.section === s)),
    sectionNames: SEC_NAME }, questions: qs, concepts };
fs.writeFileSync(path.join(ROOT, 'data.js'), 'const DATA = ' + JSON.stringify(bundle) + ';');
const years = [...new Set(qs.flatMap(q => (q.appearances || []).map(a => String(a).slice(0, 4))))].sort();
console.log(`문항 ${qs.length}, 개념 ${Object.keys(concepts).length}, 이미지 ${used.size}, 연도 ${years.join(' ')}`);
console.log('분과별: ' + SEC_ORDER.map(s => s + ':' + qs.filter(q => q.section === s).length).filter(x => !x.endsWith(':0')).join('  '));
