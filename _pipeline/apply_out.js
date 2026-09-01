// _pipeline/out/q{id}.json (에이전트 산출) -> questions/{분과}/q{id}.json (정본)
const fs = require('fs'), path = require('path');
const P = __dirname, ROOT = path.dirname(P);
const SECTIONS = ['LV','BP','BR','ENDO','UGI','CR','VS','PDS','TACS','TX','총론'];

const outDir = path.join(P, 'out');
const files = fs.readdirSync(outDir).filter(f => /^q\d+\.json$/.test(f));
let ok = 0, bad = [], skipped = [];
for (const f of files) {
  let d;
  try { d = JSON.parse(fs.readFileSync(path.join(outDir, f), 'utf8')); }
  catch (e) { bad.push([f, 'JSON 파싱 실패: ' + e.message]); continue; }

  const errs = [];
  if (d.excluded) {
    if (!Number.isInteger(d.id)) { bad.push([f, 'excluded인데 id가 없음']); continue; }
    // 중복으로 판정된 문항. 이력으로만 남기므로 내용 검증을 하지 않는다.
    const sec = d.section || '_excluded';
    const dest2 = path.join(ROOT, 'questions', sec, `q${d.id}.json`);
    fs.mkdirSync(path.dirname(dest2), { recursive: true });
    fs.writeFileSync(dest2, JSON.stringify(d, null, 1));
    const done2 = path.join(outDir, 'applied');
    fs.mkdirSync(done2, { recursive: true });
    fs.renameSync(path.join(outDir, f), path.join(done2, f));
    ok++; continue;
  }
  if (!d.stem || d.stem.length < 10) errs.push('발문 없음');
  if (!Array.isArray(d.options) || d.options.length !== 5) errs.push(`선지 ${d.options?.length}개`);
  if (!Array.isArray(d.answerKeys) || !d.answerKeys.length) errs.push('정답 없음');
  if (!d.explanation?.approach || !d.explanation?.correct) errs.push('해설 누락');
  // 선지별 검토는 문항 유형에 따라 생략한다. optnotes_mode가 규칙이다.
  const on = d.optnotes || {};
  const mode = d.optnotes_mode || 'full';
  if (!['full', 'brief', 'none'].includes(mode)) errs.push('optnotes_mode 값 이상: ' + mode);
  if (mode === 'none' && Object.keys(on).length) errs.push('optnotes_mode가 none인데 선지해설이 남음');
  if (mode !== 'none' && Object.keys(on).length !== (d.options?.length || 0))
    errs.push(`선지해설 ${Object.keys(on).length}개`);
  const QT = ['guideline', 'calculation', 'differential', 'timing', 'knowledge'];
  const qt = d.explanation?.qtype;
  if (qt && !QT.includes(qt)) errs.push('qtype 값 이상: ' + qt);
  if (['guideline', 'differential'].includes(qt) && !(d.explanation?.concepts || []).length)
    errs.push('가이드라인·감별형인데 참조할 정리 카드가 없음');
  if (!SECTIONS.includes(d.section)) errs.push('분과 미상: ' + d.section);
  const banned = /[→←⇒—–]|--|✓|❌|⭐/;
  const blob = JSON.stringify(d);
  if (banned.test(blob)) errs.push('금지 문장부호 포함');
  if (errs.length) { bad.push([f, errs.join(', ')]); continue; }

  // 정본은 questions/다. out/의 산출물이 정본보다 오래됐으면 덮어쓰지 않는다.
  // (정본을 직접 고친 뒤 out/의 옛 버전이 되살아나 작업이 사라진 적이 있다)
  const dest = path.join(ROOT, 'questions', d.section, `q${d.id}.json`);
  if (fs.existsSync(dest)) {
    const outM = fs.statSync(path.join(outDir, f)).mtimeMs;
    const dstM = fs.statSync(dest).mtimeMs;
    if (dstM > outM) { skipped.push([f, '정본이 더 최신이라 건너뜀']); continue; }
  }
  d.source_version = d.source_version || 1;
  d.content_version = d.content_version || 1;
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.writeFileSync(dest, JSON.stringify(d, null, 1));
  // 적립이 끝난 산출물은 인박스에서 치운다. 옛 버전이 정본을 되살려 덮는 사고를 막는다.
  const done = path.join(outDir, 'applied');
  fs.mkdirSync(done, { recursive: true });
  fs.renameSync(path.join(outDir, f), path.join(done, f));
  ok++;
}
console.log(`적립 ${ok}개`);
if (skipped.length) { console.log(`건너뜀 ${skipped.length}개 (정본이 더 최신)`); }
if (bad.length) { console.log('보류:'); bad.forEach(b => console.log('  ' + b[0] + ' : ' + b[1])); }
