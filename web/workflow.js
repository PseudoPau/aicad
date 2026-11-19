(() => {
  const $ = id => document.getElementById(id);
  const root = $("workflow");
  if (!root) return;
  const stages = [
    ["input", "准备现场资料", "照片仅作对照；可载入示例或 JSON。"],
    ["confirm", "核对关键尺寸", "宽、高、深、跨数、层数和排布由人确认。"],
    ["check", "检查参数契约", "Schema 与 geometry_contract 检查尺寸和组件。"],
    ["build", "构造同版几何", "pipeline 与 translator 共用同一 Layout。"],
    ["export", "导出交接文件", "JSON 可保存；STEP 依赖 CadQuery。"]
  ];
  const text = id => ($(id)?.textContent || "").trim();
  function state() {
    const r = text("results");
    return {
      doc: !!window.doc,
      checked: r.includes("参数校验通过"),
      invalid: r.includes("must be") || r.includes("必须") || r.includes("缺少"),
      blocked: text("view-title").includes("生成受阻") || r.includes("缺少 CadQuery"),
      built: !!window.revision || text("dirty") === "已生成",
      step: !!$("save-step")?.getAttribute("href")
    };
  }
  function status(id, s) {
    if (id === "input") return s.doc ? "done" : "active";
    if (id === "confirm") return s.doc && !s.checked && !s.invalid ? "active" : (s.checked || s.built ? "done" : "pending");
    if (id === "check") return s.invalid ? "blocked" : (s.checked ? "done" : (s.doc ? "active" : "pending"));
    if (id === "build") return s.blocked ? "blocked" : (s.built ? "done" : (s.checked ? "active" : "pending"));
    return s.step ? "done" : (s.blocked ? "blocked" : "pending");
  }
  function render() {
    const s = state();
    let html = '<div class="workflow-head"><div><span class="eyebrow">ONE TASK · ONE VERSION</span><strong>从现场资料到可交接方案</strong></div><span class="workflow-status">' + (s.blocked ? "当前停在环境阻塞" : (s.step ? "可交接" : "进行中")) + "</span></div><div class=\"workflow-track\">";
    stages.forEach((stage, i) => {
      const current = status(stage[0], s);
      const label = current === "done" ? "完成" : current === "blocked" ? "阻塞" : current === "active" ? "当前" : "待处理";
      html += '<div class="workflow-step ' + current + '"><div class="workflow-node">' + (current === "done" ? "✓" : (i + 1)) + '</div><div class="workflow-copy"><strong>' + stage[1] + "</strong><span>" + label + "</span><small>" + stage[2] + "</small></div></div>";
      if (i < stages.length - 1) html += '<div class="workflow-arrow">→</div>';
    });
    html += '</div><div class="workflow-modules"><span><b>输入</b>照片 / JSON / 示例</span><span><b>领域</b>geometry_contract</span><span><b>管线</b>pipeline</span><span><b>构造</b>translator + CadQuery</span><span><b>输出</b>manifest / STEP / JSON</span></div>';
    root.innerHTML = html;
    const output = $("output-state");
    if (output) {
      output.textContent = s.step ? "当前版本：JSON + STEP 可交接" : (s.blocked ? "当前版本：JSON 可保存；STEP 等待 CadQuery" : "当前版本：先检查并生成同版预览");
      output.className = s.blocked ? "output-blocked" : (s.step ? "output-ready" : "output-pending");
    }
  }
  const observer = new MutationObserver(render);
  ["results", "view-title", "dirty", "environment", "save-step", "source-note"].forEach(id => {
    const el = $(id);
    if (el) observer.observe(el, { childList: true, subtree: true, characterData: true, attributes: true });
  });
  render();
})();
