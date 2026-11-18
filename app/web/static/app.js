const key = "automation.operator-demo.v1";
const stages = ["미확인", "점검 중", "보고 초안 준비"];
const definitions = [
  ["DEMO-001", "센서 편차 알림 확인", "가상 알림: 표시된 센서 편차와 관찰 정보를 확인하고 추가 확인 사항을 기록합니다."],
  ["DEMO-002", "데이터 누락 확인", "가상 알림: 입력 데이터의 누락 여부를 확인하고 담당자에게 전달할 내용을 정리합니다."],
  ["DEMO-003", "이전 근무 미처리 사항", "가상 인계: 이전 근무에서 남긴 확인 사항을 검토하고 다음 담당자에게 전달합니다."]
];
let records = definitions.map(([id]) => ({id, stage:0, checks:[false,false,false], note:"", recipient:"", history:[]}));
let selected = 0;
const $ = selector => document.querySelector(selector);
function message(text) { $("#feedback").textContent = text; }
try {
  const saved = JSON.parse(localStorage.getItem(key));
  if (Array.isArray(saved) && saved.length === 3 && saved.every((r,i) =>
    r.id === definitions[i][0] && [0,1,2].includes(r.stage) &&
    Array.isArray(r.checks) && r.checks.length === 3 && r.checks.every(v => typeof v === "boolean") &&
    typeof r.note === "string" && typeof r.recipient === "string" &&
    Array.isArray(r.history) && r.history.every(v => typeof v === "string"))) records = saved;
} catch { message("저장 기록을 읽지 못했습니다. 현재 화면에서만 작업할 수 있습니다."); }
function persist() {
  try { localStorage.setItem(key, JSON.stringify(records)); return true; }
  catch { message("브라우저 저장에 실패했습니다. 인수인계 초안을 내려받아 보관하세요."); return false; }
}
function log(text) { records[selected].history.push(new Date().toLocaleString("ko-KR") + " · " + text); }
function capture() {
  const r = records[selected];
  const checks = [...document.querySelectorAll("[data-check]")].map(el => el.checked);
  if (r.stage === 2 && (r.note !== $("#observation").value ||
      r.recipient !== $("#recipient").value || checks.some((v,i)=>v!==r.checks[i]))) {
    r.stage = 1;
    log("내용 수정으로 보고 초안 재검토 필요");
  }
  r.note = $("#observation").value;
  r.recipient = $("#recipient").value;
  r.checks = checks;
}
function handover() {
  return "가상 업무 인수인계 초안 · 실제 보고 전송 아님\n\n" + records.map((r,i) =>
    definitions[i][0] + " · " + definitions[i][1] + "\n상태: " + stages[r.stage] +
    "\n확인 항목: " + r.checks.filter(Boolean).length + "/3" +
    "\n보고 대상: " + (r.recipient || "미입력") +
    "\n관찰·다음 확인 사항: " + (r.note || "미기록") +
    "\n이력:\n" + (r.history.join("\n") || "없음")).join("\n\n");
}
function render() {
  const r = records[selected];
  $("#overview").replaceChildren();
  [["미확인 알림",records.filter(r=>r.stage===0).length],["점검 중",records.filter(r=>r.stage===1).length],["보고 초안 준비",records.filter(r=>r.stage===2).length],["인계 대상",records.length]].forEach(([label,count])=>{
    const card=document.createElement("article");card.className="metric-card";
    const title=document.createElement("p");title.textContent=label;
    const value=document.createElement("strong");value.textContent=count+"건";
    const hint=document.createElement("p");hint.textContent="가상 업무 기록";
    card.append(title,value,hint);$("#overview").append(card);
  });
  $("#event-list").replaceChildren();
  definitions.forEach(([id,title],i)=>{
    const button=document.createElement("button");button.className="event-button";
    button.setAttribute("aria-pressed",String(i===selected));button.textContent=id+" · "+title;
    const small=document.createElement("small");small.textContent=stages[records[i].stage];button.append(small);
    button.onclick=()=>{capture();persist();selected=i;render();};$("#event-list").append(button);
  });
  $("#event-title").textContent=definitions[selected][1];
  $("#event-description").textContent=definitions[selected][2];
  $("#event-status").textContent=stages[r.stage];
  $("#observation").value=r.note;$("#recipient").value=r.recipient;
  $("#checklist").disabled=r.stage===0;
  $("#observation").disabled=r.stage===0;$("#recipient").disabled=r.stage===0;
  $("#acknowledge").disabled=r.stage!==0;
  $("#save").disabled=r.stage===0;$("#report").disabled=r.stage!==1;
  document.querySelectorAll("[data-check]").forEach((el,i)=>{el.checked=r.checks[i];});
  $("#history").replaceChildren();
  r.history.forEach(text=>{const li=document.createElement("li");li.textContent=text;$("#history").append(li);});
  $("#handover-text").textContent=handover();
}
$("#acknowledge").onclick=()=>{records[selected].stage=1;log("알림 확인 · 점검 시작");persist();render();};
$("#save").onclick=()=>{
  capture();
  if(records[selected].stage===2){records[selected].stage=1;log("내용 수정으로 보고 초안 재검토 필요");}
  log("작업 기록 저장");if(persist())message("이 브라우저에 기록했습니다.");render();
};
$("#report").onclick=()=>{
  capture();const r=records[selected];
  if(!r.checks.every(Boolean)||!r.note.trim()||!r.recipient.trim()){
    message("점검 항목 3개와 관찰 내용, 보고 대상을 모두 입력하세요.");return;
  }
  r.stage=2;log("보고 초안 준비 · 전송되지 않음");persist();render();
};
$("#export").onclick=()=>{
  capture();persist();render();
  const url=URL.createObjectURL(new Blob([handover()],{type:"text/plain;charset=utf-8"}));
  const a=document.createElement("a");a.href=url;a.download="가상-인수인계-초안.txt";a.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
};
render();

function appendText(parent, tag, text, className) {
  const element = document.createElement(tag);
  element.textContent = text;
  if (className) element.className = className;
  parent.append(element);
  return element;
}
function appendList(parent, title, items) {
  appendText(parent, "h3", title);
  const list = document.createElement("ul");
  list.className = "analysis-list";
  items.forEach(item => appendText(list, "li", item));
  parent.append(list);
}
$("#run-actual").onclick = async () => {
  const button = $("#run-actual");
  const output = $("#actual-result");
  button.disabled = true;
  button.textContent = "분석 중…";
  output.hidden = false;
  output.replaceChildren();
  appendText(output, "p", "모델과 지식 검색을 준비하고 있습니다.");
  try {
    const response = await fetch("/api/v1/analyze", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({sample_index: 1363})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "분석 요청에 실패했습니다.");
    output.replaceChildren();
    appendText(
      output,
      "span",
      data.anomalous ? "이상 판정 · 검토 필요" : "정상 판정 · 참고 결과",
      "analysis-badge" + (data.anomalous ? " anomaly" : "")
    );
    appendText(output, "p", "분석 ID: " + data.analysis_id + " · 상태: " + data.status);
    appendList(output, "상위 센서 편차", data.result.top_deviations.map(
      item => item.sensor + " · |z| " + item.z_score.toFixed(2)
    ));
    appendList(output, "검색된 가상 사례", data.result.retrieved_cases.map(
      item => item.case_id + " · " + item.title
    ));
    appendText(output, "h3", "작업자 점검·보고 초안");
    appendText(output, "p", data.result.guide.summary);
    appendList(output, "확인 항목", data.result.guide.check_items);
    appendText(output, "p", data.result.guide.report_draft);
    appendList(output, "주의사항", data.result.guide.cautions);
    appendText(
      output,
      "p",
      "이 결과는 생산 재개나 설비 조작을 승인하지 않습니다.",
      "help"
    );
  } catch (error) {
    output.replaceChildren();
    appendText(output, "p", error.message);
  } finally {
    button.disabled = false;
    button.textContent = "샘플 분석 다시 실행";
  }
};
