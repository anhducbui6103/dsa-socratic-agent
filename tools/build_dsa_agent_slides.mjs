import fs from "node:fs/promises";
import path from "node:path";
import {
  Presentation,
  PresentationFile,
} from "file:///C:/Users/anhdu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const ROOT = "D:/Workspace/GR";
const OUT = path.join(ROOT, "Duc_BA_20241582E_slides.pptx");
const PREVIEW = path.join(ROOT, ".codex_presentation_tmp", "preview");
const ASSETS = path.join(ROOT, "docs", "report-assets");

const W = 1280;
const H = 720;
const frame = { left: 70, top: 58, width: 1140, height: 604 };

const colors = {
  bg: "slate-50",
  ink: "slate-950",
  muted: "slate-600",
  line: "slate-200",
  blue: "#1F4E79",
  blue2: "#EAF2FF",
  green: "#EAF7EE",
  orange: "#FFF7E6",
  purple: "#F1EAFE",
  teal: "#EAF7F8",
};

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

async function imageBlob(fileName) {
  const bytes = await fs.readFile(path.join(ASSETS, fileName));
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

function addText(slide, text, position, style = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontSize: style.fontSize ?? 22,
    bold: style.bold ?? false,
    color: style.color ?? colors.ink,
    alignment: style.alignment,
  };
  return shape;
}

function addTitle(slide, title, eyebrow = "DSA SOCRATIC AGENT") {
  addText(slide, eyebrow, { left: frame.left, top: 36, width: 420, height: 28 }, {
    fontSize: 14,
    bold: true,
    color: colors.blue,
  });
  addText(slide, title, { left: frame.left, top: 72, width: 850, height: 58 }, {
    fontSize: 38,
    bold: true,
  });
}

function addFooter(slide, index) {
  addText(slide, String(index).padStart(2, "0"), { left: 1160, top: 660, width: 50, height: 24 }, {
    fontSize: 14,
    color: "slate-400",
    alignment: "right",
  });
}

function addPill(slide, text, x, y, w, fill = colors.blue2) {
  const pill = slide.shapes.add({
    geometry: "roundRect",
    position: { left: x, top: y, width: w, height: 38 },
    fill,
    line: { style: "solid", fill: "slate-200", width: 1 },
    borderRadius: "rounded-xl",
  });
  pill.text = text;
  pill.text.style = { fontSize: 16, bold: true, color: colors.blue, alignment: "center" };
  return pill;
}

function addCard(slide, title, body, x, y, w, h, fill = "white") {
  slide.shapes.add({
    geometry: "roundRect",
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: colors.line, width: 1 },
    borderRadius: "rounded-xl",
    shadow: "shadow-sm",
  });
  addText(slide, title, { left: x + 24, top: y + 18, width: w - 48, height: 32 }, {
    fontSize: 21,
    bold: true,
    color: colors.ink,
  });
  addText(slide, body, { left: x + 24, top: y + 62, width: w - 48, height: h - 76 }, {
    fontSize: 17,
    color: colors.muted,
  });
}

function addBullets(slide, items, x, y, w, h, fontSize = 22) {
  addText(slide, items.map((item) => `• ${item}`).join("\n"), { left: x, top: y, width: w, height: h }, {
    fontSize,
    color: colors.ink,
  });
}

async function addImage(slide, fileName, position, alt, fit = "contain") {
  slide.images.add({
    blob: await imageBlob(fileName),
    contentType: "image/png",
    alt,
    fit,
    position,
    geometry: "roundRect",
    borderRadius: "rounded-xl",
  });
}

async function build() {
  await fs.mkdir(PREVIEW, { recursive: true });
  const deck = Presentation.create({ slideSize: { width: W, height: H } });
  let n = 1;

  {
    const s = deck.slides.add();
    s.background.fill = colors.bg;
    addText(s, "AI Agent hỗ trợ học\nCấu trúc dữ liệu và Giải thuật", { left: 78, top: 120, width: 720, height: 150 }, {
      fontSize: 52,
      bold: true,
    });
    addText(s, "LLM-powered multi-agent tutor theo phương pháp Socratic", { left: 82, top: 292, width: 640, height: 42 }, {
      fontSize: 24,
      color: colors.muted,
    });
    addPill(s, "Python", 82, 382, 110);
    addPill(s, "LangGraph", 210, 382, 150);
    addPill(s, "Gemini API", 378, 382, 150);
    addPill(s, "Streamlit", 546, 382, 140);
    await addImage(s, "architecture.png", { left: 760, top: 92, width: 430, height: 470 }, "Architecture overview");
    addFooter(s, n++);
  }

  {
    const s = deck.slides.add();
    s.background.fill = "white";
    addTitle(s, "Vấn đề và hướng tiếp cận");
    addCard(s, "Khó khăn khi học DSA", "Người học không chỉ cần đáp án, mà cần biết phân tích đề, chọn cấu trúc dữ liệu, trace edge case và đánh giá độ phức tạp.", 80, 170, 340, 300, "#FFF7E6");
    addCard(s, "Hạn chế của chatbot thường", "Dễ trả lời trực tiếp, thiếu trạng thái học tập và khó kiểm soát mức độ gợi ý.", 470, 170, 340, 300, "#F1EAFE");
    addCard(s, "Hướng giải quyết", "Thiết kế tutor agent theo Socratic, có workflow, state và quality layer để dẫn dắt thay vì làm hộ.", 860, 170, 340, 300, "#EAF7EE");
    addFooter(s, n++);
  }

  {
    const s = deck.slides.add();
    s.background.fill = colors.bg;
    addTitle(s, "Cơ sở lý thuyết");
    addBullets(s, [
      "Socratic tutoring: đặt câu hỏi gợi mở thay vì đưa lời giải hoàn chỉnh.",
      "LLM Agent: dùng LLM trong workflow có state và policy kiểm soát.",
      "Multi-agent: chia nhiệm vụ thành các agent chuyên trách.",
      "Testcase trong học thuật toán: hỗ trợ trace, phát hiện edge case và kiểm giả định.",
    ], 92, 170, 650, 350, 24);
    addCard(s, "Nguyên tắc phản hồi", "Mỗi lượt chỉ tập trung 1-2 gợi ý chính; tăng dần hint_level; không đưa full code trong chế độ mặc định.", 805, 175, 345, 250, "#EAF2FF");
    addFooter(s, n++);
  }

  {
    const s = deck.slides.add();
    s.background.fill = "white";
    addTitle(s, "Mục tiêu hệ thống");
    addCard(s, "Điều phối bằng LangGraph", "Tách workflow theo intent để dễ mở rộng và quan sát.", 85, 165, 340, 170);
    addCard(s, "LLM cho tác vụ ngữ cảnh", "Detect intent, classify problem, generate hint, testcase và review phản hồi.", 470, 165, 340, 170);
    addCard(s, "Quality Layer", "Testcase generator, execution validator và pedagogy critic.", 855, 165, 340, 170);
    addCard(s, "Giao diện tương tác", "Streamlit chat UI nhiều phiên, hiển thị trạng thái và Agent Trace.", 275, 390, 730, 145, "#EAF7F8");
    addFooter(s, n++);
  }

  {
    const s = deck.slides.add();
    s.background.fill = colors.bg;
    addTitle(s, "Công nghệ sử dụng");
    addCard(s, "Python", "Core agent, schema dữ liệu, validator và kiểm thử.", 75, 160, 250, 160);
    addCard(s, "LangGraph", "Workflow orchestration bằng node và conditional edge.", 365, 160, 250, 160);
    addCard(s, "Gemini API", "LLM provider cho intent, hint, testcase và pedagogy review.", 655, 160, 250, 160);
    addCard(s, "Streamlit", "Giao diện chat demo, nhiều phiên học và panel trạng thái.", 945, 160, 250, 160);
    addCard(s, "Quality + Sandbox", "Chạy code Python có timeout; chuẩn hóa PASSED/FAILED/TIMEOUT/SKIPPED.", 220, 390, 380, 150, "#FFF7E6");
    addCard(s, "unittest", "Kiểm tra schema, validator và các nhánh xử lý chính.", 680, 390, 380, 150, "#EAF7EE");
    addFooter(s, n++);
  }

  {
    const s = deck.slides.add();
    s.background.fill = "white";
    addTitle(s, "Kiến trúc tổng quan");
    await addImage(s, "architecture.png", { left: 80, top: 145, width: 710, height: 430 }, "Architecture overview");
    addBullets(s, [
      "AI Tutor Agent là trung tâm điều phối.",
      "Learning Modules xử lý phân loại, gợi ý và phân tích code.",
      "Quality Layer kiểm testcase, validation và phản hồi sư phạm.",
      "State & Memory giúp cá nhân hóa theo tiến trình học.",
    ], 835, 160, 350, 400, 20);
    addFooter(s, n++);
  }

  {
    const s = deck.slides.add();
    s.background.fill = colors.bg;
    addTitle(s, "Workflow LangGraph");
    await addImage(s, "langgraph.png", { left: 72, top: 140, width: 720, height: 392 }, "LangGraph workflow");
    await addImage(s, "code-langgraph-nodes.png", { left: 825, top: 160, width: 345, height: 210 }, "LangGraph code snippet", "contain");
    addText(s, "Tách node giúp workflow rõ ràng, dễ debug và dễ thêm agent mới.", { left: 825, top: 405, width: 345, height: 90 }, {
      fontSize: 20,
      color: colors.muted,
    });
    addFooter(s, n++);
  }

  {
    const s = deck.slides.add();
    s.background.fill = "white";
    addTitle(s, "Các agent chính");
    const agents = [
      ["Intent Detector", "Phân loại message"],
      ["Problem Classifier", "Nhận diện dạng bài"],
      ["Hint Generator", "Sinh gợi ý Socratic"],
      ["Testcase Generator", "Tạo case trace/validate"],
      ["Execution Validator", "Chạy code Python"],
      ["Pedagogy Critic", "Review phản hồi"],
      ["Session Title", "Đặt tên phiên chat"],
    ];
    agents.forEach(([a, b], i) => {
      const col = i % 3;
      const row = Math.floor(i / 3);
      addCard(s, a, b, 95 + col * 370, 160 + row * 150, 320, 115, i % 2 ? "#F8FAFC" : "#EAF2FF");
    });
    addFooter(s, n++);
  }

  {
    const s = deck.slides.add();
    s.background.fill = colors.bg;
    addTitle(s, "State & Memory");
    await addImage(s, "code-state-schema.png", { left: 80, top: 150, width: 540, height: 310 }, "LearningState code snippet");
    addCard(s, "LearningState lưu gì?", "current_problem, problem_type, concepts, hint_level, student_attempts, generated_tests, latest_validation, pedagogy_flags và next_action.", 700, 170, 420, 190, "#EAF7EE");
    addCard(s, "Vì sao quan trọng?", "Cùng một câu xin gợi ý có thể sinh phản hồi khác nhau tùy bài, số lần hint và kết quả validation gần nhất.", 700, 390, 420, 160, "#FFF7E6");
    addFooter(s, n++);
  }

  {
    const s = deck.slides.add();
    s.background.fill = "white";
    addTitle(s, "Quality Layer");
    addCard(s, "Testcase Generator", "Sinh basic, edge, adversarial/stress cases. Phân biệt validation và trace-only testcase.", 85, 160, 345, 210, "#EAF2FF");
    addCard(s, "Execution Validator", "Chạy Python code trên testcase có expected output, giới hạn timeout và chuẩn hóa kết quả.", 468, 160, 345, 210, "#EAF7EE");
    addCard(s, "Pedagogy Critic", "Kiểm phản hồi nháp: không lộ full solution, đúng hint_level, đủ tính Socratic.", 850, 160, 345, 210, "#F1EAFE");
    await addImage(s, "code-quality-review.png", { left: 260, top: 430, width: 760, height: 170 }, "Pedagogy review code snippet");
    addFooter(s, n++);
  }

  {
    const s = deck.slides.add();
    s.background.fill = colors.bg;
    addTitle(s, "Kết quả đạt được");
    addBullets(s, [
      "Có kiến trúc multi-agent rõ ràng cho DSA tutor.",
      "Có LangGraph workflow tách node theo intent.",
      "Có cơ chế hint nhiều cấp độ theo phương pháp Socratic.",
      "Có Quality Layer: testcase, validation, pedagogy review.",
      "Có Streamlit UI nhiều phiên và hiển thị trạng thái học tập.",
    ], 90, 170, 610, 360, 24);
    await addImage(s, "demo-ui.png", { left: 735, top: 165, width: 420, height: 300 }, "Streamlit demo UI");
    addFooter(s, n++);
  }

  {
    const s = deck.slides.add();
    s.background.fill = "white";
    addTitle(s, "Hạn chế và hướng phát triển");
    addCard(s, "Chưa làm được", "Chưa có database bền vững; sandbox mới tập trung Python; testcase expected output còn phụ thuộc độ rõ của đề; chưa có benchmark lớn.", 90, 170, 500, 260, "#FFF7E6");
    addCard(s, "Phát triển tiếp", "Lưu session bằng database; nâng cấp sandbox; thêm Evaluation Agent; xây benchmark DSA; mở rộng UI theo dõi tiến độ học.", 690, 170, 500, 260, "#EAF7EE");
    addText(s, "Kết luận: hệ thống đặt nền tảng cho một AI tutor có trạng thái, có workflow và có lớp kiểm soát chất lượng, phù hợp để mở rộng thành trợ giảng cá nhân hóa.", { left: 145, top: 500, width: 990, height: 80 }, {
      fontSize: 24,
      bold: true,
      color: colors.blue,
      alignment: "center",
    });
    addFooter(s, n++);
  }

  for (const [index, slide] of deck.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    await writeBlob(path.join(PREVIEW, `${stem}.png`), await deck.export({ slide, format: "png", scale: 1 }));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(PREVIEW, `${stem}.layout.json`), await layout.text());
  }
  await writeBlob(path.join(PREVIEW, "deck-montage.webp"), await deck.export({ format: "webp", montage: true, scale: 1 }));
  const pptx = await PresentationFile.exportPptx(deck);
  await pptx.save(OUT);
}

build().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
