// 배치 산출물에서 new_concepts를 모아 중복을 합치고, 만들어야 할 카드 목록을 낸다.
const fs = require('fs'), path = require('path');
const P = __dirname, ROOT = path.dirname(P);
const have = new Set(fs.existsSync(path.join(ROOT, 'concepts'))
  ? fs.readdirSync(path.join(ROOT, 'concepts')).filter(f => f.endsWith('.json')).map(f => f.slice(0, -5)) : []);
// link_concepts.js가 이미 실제 카드로 연결해 둔 옛 이름은 새로 만들 대상이 아니다.
const linkSrc = fs.readFileSync(path.join(P, 'link_concepts.js'), 'utf8');
const mapBody = linkSrc.slice(linkSrc.indexOf('const MAP'), linkSrc.indexOf('};', linkSrc.indexOf('const MAP')));
for (const m of mapBody.matchAll(/'([^']+)'\s*:\s*'([^']+)'/g)) if (have.has(m[2])) have.add(m[1]);

const byslug = new Map();
// 정본(questions/)과 아직 적립 안 된 산출물(out/)을 모두 훑는다.
const files = [];
const qroot = path.join(ROOT, 'questions');
if (fs.existsSync(qroot)) for (const sec of fs.readdirSync(qroot)) {
  const d = path.join(qroot, sec);
  if (!fs.statSync(d).isDirectory()) continue;
  for (const f of fs.readdirSync(d).filter(x => x.endsWith('.json'))) files.push(path.join(d, f));
}
const outDir = path.join(P, 'out');
if (fs.existsSync(outDir))
  for (const f of fs.readdirSync(outDir).filter(x => /^q\d+\.json$/.test(x))) files.push(path.join(outDir, f));
for (const fp of files) {
  let d; try { d = JSON.parse(fs.readFileSync(fp, 'utf8')); } catch { continue; }
  for (const c of (d.new_concepts || [])) {
    const slug = (c.slug || '').trim();
    if (!slug || have.has(slug)) continue;
    if (!byslug.has(slug)) byslug.set(slug, { slug, title: c.title || '', why: [], qids: [], sections: new Set() });
    const e = byslug.get(slug);
    if (c.why) e.why.push(c.why);
    e.qids.push(d.id);
    if (d.section) e.sections.add(d.section);
    if (!e.title && c.title) e.title = c.title;
  }
}
const list = [...byslug.values()].sort((a, b) => b.qids.length - a.qids.length);
console.log(`만들어야 할 정리 카드 ${list.length}개 (이미 있는 카드 ${have.size}개)`);
for (const c of list) {
  console.log(`\n  ${c.slug}  [${[...c.sections].join(',')}]  문항 ${c.qids.join(', ')}`);
  console.log(`    제목: ${c.title}`);
  if (c.why[0]) console.log(`    이유: ${c.why[0].slice(0, 110)}`);
}
fs.writeFileSync(path.join(P, 'g_newconcepts.json'),
  JSON.stringify(list.map(c => ({ ...c, sections: [...c.sections] })), null, 1));
