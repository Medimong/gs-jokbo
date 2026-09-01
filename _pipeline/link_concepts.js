// 에이전트가 제안한 개념 이름을 실제 개념 파일 slug에 연결한다.
const fs = require('fs'), path = require('path');
const ROOT = path.dirname(__dirname);
const MAP = {
  '위절제술-종류별-적응증-비교': 'gastrectomy-types',
  '유문보존위절제술-PPG-적응증과재건': 'gastrectomy-types',
  'acute-limb-ischemia-rutherford-classification': 'acute-limb-ischemia',
  'arterial-embolism-vs-thrombosis': 'acute-limb-ischemia',
  '갑상선결절-fna-적응증': 'thyroid-nodule-workup',
  '갑상선-순수낭종-처치': 'thyroid-nodule-workup',
  '장관발생-foregut-midgut-hindgut': 'gut-embryology',
  '유방암-위험인자': 'breast-cancer-risk-factors',
  '간이식-graft-recipient-weight-ratio': 'liver-graft-size',
  'hcc-bclc-치료알고리즘': 'hcc-treatment-algorithm',
  'child-pugh-분류': 'hcc-treatment-algorithm',
  '소아-서혜부탈장-수술시기': 'pediatric-inguinal-hernia',
  '소아-서혜부탈장-고위결찰': 'pediatric-inguinal-hernia',
  'pancreatic-trauma-aast-grade': 'pancreatic-trauma-management',
  'courvoisier-징후': 'periampullary-cancer-workup',
  '췌두부암-절제가능성평가-whipple': 'periampullary-cancer-workup',
  '직장암수술-하복신경-사정장애': 'pelvic-autonomic-nerve',
  '골반자율신경-교감부교감구분': 'pelvic-autonomic-nerve',
};
const have = new Set(fs.existsSync(path.join(ROOT, 'concepts'))
  ? fs.readdirSync(path.join(ROOT, 'concepts')).filter(f => f.endsWith('.json'))
      .map(f => f.replace(/\.json$/, '')) : []);
let n = 0;
for (const sec of fs.readdirSync(path.join(ROOT, 'questions'))) {
  const d = path.join(ROOT, 'questions', sec);
  if (!fs.statSync(d).isDirectory()) continue;
  for (const f of fs.readdirSync(d).filter(x => x.endsWith('.json'))) {
    const fp = path.join(d, f), q = JSON.parse(fs.readFileSync(fp, 'utf8'));
    if (q.excluded || !q.explanation) continue;   // 중복으로 합쳐진 문항
    const src = q.explanation?.concepts || [];
    const out = [...new Set(src.map(s => MAP[s] || s).filter(s => have.has(s)))];
    const pending = [...new Set(src.map(s => MAP[s] || s).filter(s => !have.has(s)))];
    q.explanation.concepts = out;
    if (pending.length) q.concepts_pending = pending;
    fs.writeFileSync(fp, JSON.stringify(q, null, 1));
    if (out.length) n++;
  }
}
console.log(`개념 연결된 문항 ${n}개 (사용 가능 개념 ${have.size}개)`);
