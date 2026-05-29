const state = {
  leads: [],
  contacts: [],
  leadHeaders: [],
  contactHeaders: [],
  selectedLeadId: "",
  newContactDraft: {},
};

const leadEditFields = [
  ["company_name", "公司名称"],
  ["website", "网站"],
  ["country", "国家"],
  ["city_or_region", "城市/区域"],
  ["customer_type", "客户类型"],
  ["company_email", "公司邮箱"],
  ["company_phone", "公司电话"],
  ["company_contact_page", "公司联系页"],
  ["company_contact_form_url", "公司表单 URL"],
  ["key_contact_name", "关键人姓名"],
  ["key_contact_job_title", "关键人职位"],
  ["key_contact_email", "关键人邮箱"],
  ["key_contact_phone", "关键人电话"],
  ["key_contact_linkedin_url", "关键人 LinkedIn"],
  ["key_contact_source_link", "关键人来源"],
  ["key_contact_confidence", "关键人可信度"],
  ["contact_data_level", "联系数据等级"],
  ["primary_contact_method", "主要联系路径"],
  ["outreach_contact_type", "外联类型"],
  ["contact_priority", "联系优先级"],
  ["contact_research_status", "联系研究状态"],
  ["verification_status", "验证状态"],
  ["contact_completeness_score", "完整度"],
  ["next_action", "下一步"],
  ["notes", "备注"],
  ["enrichment_notes", "补全备注"],
];

const longLeadFields = new Set(["notes", "enrichment_notes", "next_action", "key_contact_source_link", "company_contact_form_url"]);

const contactEditFields = [
  ["contact_name", "联系人姓名"],
  ["job_title", "职位"],
  ["department", "部门"],
  ["contact_role_type", "角色类型"],
  ["email", "邮箱"],
  ["phone", "电话"],
  ["linkedin_url", "LinkedIn"],
  ["source_link", "来源链接"],
  ["source_type", "来源类型"],
  ["contact_confidence", "可信度"],
  ["contact_status", "状态"],
  ["is_primary_contact", "主联系人"],
  ["contact_priority", "优先级"],
  ["outreach_contact_type", "外联类型"],
  ["notes", "备注"],
];

const longContactFields = new Set(["source_link", "notes"]);

const presetOptions = {
  next_action: [
    "继续查找关键人邮箱",
    "继续查找关键人电话",
    "验证公司联系表单是否可用",
    "验证公司邮箱和电话",
    "查找 F&B / Operations / Procurement 负责人",
    "优先人工确认客户类型后再外联",
    "当前信息足够，进入外联候选",
    "暂缓，信息不足或匹配度一般",
  ],
  notes: [
    "人工补充：已按官网信息更新。",
    "人工补充：已按公开来源更新，仍需二次确认。",
    "人工判断：餐厅/酒店最终客户方向相关。",
    "人工判断：可能是供应商/服务商，暂不作为优先最终客户。",
    "人工判断：公司级联系路径可用，但关键人直联仍缺失。",
    "人工判断：关键人已识别，但直接联系方式仍缺失。",
  ],
  enrichment_notes: [
    "已检查官网联系页。",
    "已检查官网团队/关于页面。",
    "已检查 LinkedIn 公开资料。",
    "已记录公司邮箱/电话/表单作为次级联系路径。",
    "已记录关键人姓名和职位，直接邮箱/电话待查。",
    "未发现可靠关键人直联，保留公司级联系路径。",
  ],
};

const els = {
  message: document.getElementById("message"),
  editorNameInput: document.getElementById("editorNameInput"),
  totalCount: document.getElementById("totalCount"),
  missingCoreCount: document.getElementById("missingCoreCount"),
  missingCompanyContactCount: document.getElementById("missingCompanyContactCount"),
  missingKeyContactCount: document.getElementById("missingKeyContactCount"),
  directKeyCount: document.getElementById("directKeyCount"),
  countryFilter: document.getElementById("countryFilter"),
  missingFilter: document.getElementById("missingFilter"),
  searchInput: document.getElementById("searchInput"),
  visibleCount: document.getElementById("visibleCount"),
  leadList: document.getElementById("leadList"),
  editorTitle: document.getElementById("editorTitle"),
  editorSubtitle: document.getElementById("editorSubtitle"),
  editFields: document.getElementById("editFields"),
  nextActionPreset: document.getElementById("nextActionPreset"),
  notesPreset: document.getElementById("notesPreset"),
  enrichmentNotesPreset: document.getElementById("enrichmentNotesPreset"),
  contactList: document.getElementById("contactList"),
  newContactFields: document.getElementById("newContactFields"),
  loadDefaultBtn: document.getElementById("loadDefaultBtn"),
  leadsCsvInput: document.getElementById("leadsCsvInput"),
  contactsCsvInput: document.getElementById("contactsCsvInput"),
  exportLeadsBtn: document.getElementById("exportLeadsBtn"),
  exportContactsBtn: document.getElementById("exportContactsBtn"),
  saveEditBtn: document.getElementById("saveEditBtn"),
  addContactBtn: document.getElementById("addContactBtn"),
  resetBtn: document.getElementById("resetBtn"),
  applyNextActionPresetBtn: document.getElementById("applyNextActionPresetBtn"),
  appendNotesPresetBtn: document.getElementById("appendNotesPresetBtn"),
  appendEnrichmentPresetBtn: document.getElementById("appendEnrichmentPresetBtn"),
};

function isBlank(value) {
  return String(value ?? "").trim() === "";
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let cell = "";
  let inQuotes = false;

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    const next = text[i + 1];

    if (char === '"' && inQuotes && next === '"') {
      cell += '"';
      i += 1;
    } else if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === "," && !inQuotes) {
      row.push(cell);
      cell = "";
    } else if ((char === "\n" || char === "\r") && !inQuotes) {
      if (char === "\r" && next === "\n") i += 1;
      row.push(cell);
      if (row.some((value) => value !== "")) rows.push(row);
      row = [];
      cell = "";
    } else {
      cell += char;
    }
  }

  row.push(cell);
  if (row.some((value) => value !== "")) rows.push(row);
  if (!rows.length) return { headers: [], records: [] };

  const headers = rows[0].map((header) => header.trim());
  const records = rows.slice(1).map((values) => {
    const record = {};
    headers.forEach((header, index) => {
      record[header] = values[index] ?? "";
    });
    return record;
  });

  return { headers, records };
}

function csvEscape(value) {
  const text = String(value ?? "");
  if (/[",\n\r]/.test(text)) return `"${text.replaceAll('"', '""')}"`;
  return text;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function toCsv(records, headers) {
  const finalHeaders = [...headers];
  records.forEach((record) => {
    Object.keys(record).forEach((key) => {
      if (!finalHeaders.includes(key)) finalHeaders.push(key);
    });
  });

  const lines = [
    finalHeaders.map(csvEscape).join(","),
    ...records.map((record) => finalHeaders.map((header) => csvEscape(record[header])).join(",")),
  ];
  return lines.join("\r\n");
}

async function loadCsvFromUrl(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(`Cannot load ${url}`);
  return response.text();
}

async function loadDefaults() {
  try {
    const [leadsText, contactsText] = await Promise.all([
      loadCsvFromUrl("../data/leads.csv"),
      loadCsvFromUrl("../data/contacts.csv"),
    ]);
    setLeads(leadsText);
    setContacts(contactsText);
    setMessage("已加载默认 CSV。修改会保存在当前页面，导出 leads.csv / contacts.csv 后作为最新数据源使用。");
  } catch (error) {
    setMessage("浏览器未允许直接读取本地 CSV，请手动导入 data/leads.csv 和 data/contacts.csv。", true);
  }
}

function setLeads(text) {
  const parsed = parseCsv(text);
  state.leadHeaders = ensureHeaders(parsed.headers, ["last_updated", "change_note"]);
  state.leads = parsed.records;
  if (!state.selectedLeadId && state.leads[0]) state.selectedLeadId = state.leads[0].lead_id;
  updateCountryOptions();
  render();
}

function setContacts(text) {
  const parsed = parseCsv(text);
  state.contactHeaders = ensureHeaders(parsed.headers, ["last_updated", "change_note"]);
  state.contacts = parsed.records;
  render();
}

function ensureHeaders(headers, required) {
  const output = [...headers];
  required.forEach((header) => {
    if (!output.includes(header)) output.push(header);
  });
  return output;
}

function setMessage(text, isError = false) {
  els.message.textContent = text;
  els.message.classList.toggle("error", isError);
}

function editorName() {
  return els.editorNameInput.value.trim() || "Manual User";
}

function editorStamp(action) {
  return `${currentTimestamp()} ${editorName()} ${action}`;
}

function getLeadContacts(leadId) {
  return state.contacts
    .map((contact, index) => ({ contact, index }))
    .filter((item) => item.contact.lead_id === leadId);
}

function getMissingFlags(lead) {
  const hasCompanyContact = !isBlank(lead.company_email)
    || !isBlank(lead.company_phone)
    || !isBlank(lead.company_contact_page)
    || !isBlank(lead.company_contact_form_url)
    || !isBlank(lead.official_contact_page)
    || !isBlank(lead.contact_form_url);
  const hasKeyPerson = !isBlank(lead.key_contact_name) || !isBlank(lead.contact_person);
  const hasDirectKey = !isBlank(lead.key_contact_email)
    || !isBlank(lead.key_contact_phone)
    || !isBlank(lead.key_contact_linkedin_url)
    || !isBlank(lead.email_address)
    || !isBlank(lead.phone_number)
    || !isBlank(lead.linkedin_url);

  return {
    core: isBlank(lead.company_name) || isBlank(lead.website) || isBlank(lead.country) || isBlank(lead.customer_type),
    company_contact: !hasCompanyContact,
    key_person: !hasKeyPerson,
    direct_key: !hasDirectKey,
    direct_key_found: hasDirectKey,
  };
}

function updateCountryOptions() {
  const current = els.countryFilter.value;
  const countries = [...new Set(state.leads.map((lead) => lead.country).filter((country) => !isBlank(country)))].sort();
  els.countryFilter.innerHTML = [
    '<option value="">全部国家</option>',
    ...countries.map((country) => `<option value="${escapeHtml(country)}">${escapeHtml(country)}</option>`),
  ].join("");

  if (countries.includes(current)) {
    els.countryFilter.value = current;
  } else if (countries.includes("Australia")) {
    els.countryFilter.value = "Australia";
  }
}

function filteredLeads() {
  const country = els.countryFilter.value;
  const missing = els.missingFilter.value;
  const search = els.searchInput.value.trim().toLowerCase();

  return state.leads.filter((lead) => {
    const flags = getMissingFlags(lead);
    if (country && lead.country !== country) return false;
    if (missing && !flags[missing]) return false;
    if (search) {
      const haystack = [
        lead.lead_id,
        lead.company_name,
        lead.website,
        lead.customer_type,
        lead.source_link,
        lead.notes,
        lead.enrichment_notes,
      ].join(" ").toLowerCase();
      if (!haystack.includes(search)) return false;
    }
    return true;
  });
}

function renderSummary(leads) {
  const counts = leads.reduce((acc, lead) => {
    const flags = getMissingFlags(lead);
    if (flags.core) acc.core += 1;
    if (flags.company_contact) acc.company += 1;
    if (flags.key_person) acc.key += 1;
    if (flags.direct_key_found) acc.direct += 1;
    return acc;
  }, { core: 0, company: 0, key: 0, direct: 0 });

  els.totalCount.textContent = leads.length;
  els.missingCoreCount.textContent = counts.core;
  els.missingCompanyContactCount.textContent = counts.company;
  els.missingKeyContactCount.textContent = counts.key;
  els.directKeyCount.textContent = counts.direct;
}

function badge(label, missing) {
  return `<span class="badge ${missing ? "missing" : "ok"}">${missing ? "缺 " : "有 "}${label}</span>`;
}

function valueOrMissing(value) {
  if (isBlank(value)) return '<span class="missing-text">待补充</span>';
  const text = String(value);
  const escaped = escapeHtml(text);
  if (/^https?:\/\//i.test(text)) return `<a href="${escaped}" target="_blank" rel="noreferrer">${escaped}</a>`;
  return escaped;
}

function renderLeadList(leads) {
  els.visibleCount.textContent = `${leads.length} 条`;
  els.leadList.innerHTML = "";

  if (!leads.length) {
    els.leadList.innerHTML = '<div class="empty">没有匹配的线索。</div>';
    return;
  }

  leads.forEach((lead) => {
    const flags = getMissingFlags(lead);
    const contactCount = getLeadContacts(lead.lead_id).length;
    const card = document.createElement("article");
    card.className = `lead-card ${lead.lead_id === state.selectedLeadId ? "active" : ""}`;
    card.innerHTML = `
      <div class="lead-head">
        <div>
          <h3>${escapeHtml(lead.company_name || "未命名公司")}</h3>
          <p>${escapeHtml(lead.lead_id || "")} · ${escapeHtml(lead.country || "国家待补充")} · ${escapeHtml(lead.customer_type || "类型待补充")} · 联系人 ${contactCount}</p>
        </div>
        <button type="button" data-select-lead="${escapeHtml(lead.lead_id)}">编辑</button>
      </div>
      <div class="badges">
        ${badge("基础", flags.core)}
        ${badge("公司联系", flags.company_contact)}
        ${badge("关键人", flags.key_person)}
        ${badge("关键人直联", flags.direct_key)}
      </div>
      <div class="card-grid">
        <div class="info"><label>网站</label><div>${valueOrMissing(lead.website)}</div></div>
        <div class="info"><label>公司联系</label><div>${valueOrMissing(lead.company_email || lead.company_phone || lead.company_contact_page || lead.company_contact_form_url)}</div></div>
        <div class="info"><label>关键人</label><div>${valueOrMissing(lead.key_contact_name || lead.contact_person)}</div></div>
        <div class="info"><label>下一步</label><div>${valueOrMissing(lead.next_action)}</div></div>
      </div>
    `;
    els.leadList.appendChild(card);
  });
}

function makeInput(name, label, value, isLong = false, extraAttrs = "") {
  const safeValue = escapeHtml(value);
  const safeName = escapeHtml(name);
  const safeLabel = escapeHtml(label);
  if (isLong) {
    return `<label class="wide">${safeLabel}<textarea data-field="${safeName}" ${extraAttrs}>${safeValue}</textarea></label>`;
  }
  return `<label>${safeLabel}<input data-field="${safeName}" value="${safeValue}" ${extraAttrs}></label>`;
}

function renderEditor() {
  const lead = state.leads.find((item) => item.lead_id === state.selectedLeadId);
  if (!lead) {
    els.editorTitle.textContent = "选择一条线索";
    els.editorSubtitle.textContent = "选择公司后，可编辑公司字段和该公司所有联系人。";
    els.editFields.innerHTML = '<div class="empty">暂无选中线索。</div>';
    els.contactList.innerHTML = "";
    els.newContactFields.innerHTML = "";
    return;
  }

  els.editorTitle.textContent = lead.company_name || "未命名公司";
  els.editorSubtitle.textContent = `${lead.lead_id || ""} · ${lead.country || "国家待补充"}`;
  els.editFields.classList.remove("empty-editor");
  els.editFields.innerHTML = leadEditFields
    .map(([name, label]) => makeInput(name, label, lead[name], longLeadFields.has(name)))
    .join("");

  renderContacts(lead);
  renderNewContactFields();
}

function renderContacts(lead) {
  const contacts = getLeadContacts(lead.lead_id);
  if (!contacts.length) {
    els.contactList.innerHTML = '<div class="empty">还没有联系人记录，可在下方新增。</div>';
    return;
  }

  els.contactList.innerHTML = contacts.map(({ contact, index }, visibleIndex) => `
    <article class="contact-card editable-contact">
      <div class="contact-title">
        <strong>联系人 ${visibleIndex + 1}: ${escapeHtml(contact.contact_name || "未命名联系人")}</strong>
        <span>${escapeHtml(contact.contact_id || "")}</span>
      </div>
      <div class="edit-grid">
        ${contactEditFields.map(([name, label]) => makeInput(`contact.${index}.${name}`, label, contact[name], longContactFields.has(name))).join("")}
      </div>
    </article>
  `).join("");
}

function renderNewContactFields() {
  els.newContactFields.innerHTML = contactEditFields
    .filter(([name]) => name !== "is_primary_contact")
    .map(([name, label]) => makeInput(`new_contact.${name}`, label, state.newContactDraft[name], longContactFields.has(name)))
    .join("");
}

function renderPresets() {
  fillPresetSelect(els.nextActionPreset, presetOptions.next_action);
  fillPresetSelect(els.notesPreset, presetOptions.notes);
  fillPresetSelect(els.enrichmentNotesPreset, presetOptions.enrichment_notes);
}

function fillPresetSelect(select, options) {
  select.innerHTML = options.map((option) => `<option value="${escapeHtml(option)}">${escapeHtml(option)}</option>`).join("");
}

function render() {
  const leads = filteredLeads();
  renderSummary(leads);
  renderLeadList(leads);
  renderEditor();
}

function applyLeadEdits({ rerender = true } = {}) {
  const lead = state.leads.find((item) => item.lead_id === state.selectedLeadId);
  if (!lead) return false;
  let changed = false;

  els.editFields.querySelectorAll("[data-field]").forEach((input) => {
    const field = input.dataset.field;
    const nextValue = input.value.trim();
    if ((lead[field] ?? "") !== nextValue) {
      lead[field] = nextValue;
      changed = true;
    }
  });

  if (changed) {
    lead.last_updated = currentTimestamp();
    lead.change_note = appendNote(lead.change_note, editorStamp("updated lead in dashboard."));
  }
  applyContactEdits();
  setMessage(`已应用 ${lead.company_name || lead.lead_id} 的当前修改。导出 leads.csv / contacts.csv 后即可作为最新数据源。`);
  if (rerender) render();
  return true;
}

function applyContactEdits() {
  els.contactList.querySelectorAll("[data-field^='contact.']").forEach((input) => {
    const [, indexText, field] = input.dataset.field.split(".");
    const contact = state.contacts[Number(indexText)];
    if (!contact) return;
    const nextValue = input.value.trim();
    if ((contact[field] ?? "") !== nextValue) {
      contact[field] = nextValue;
      contact.last_updated = currentTimestamp();
      contact.change_note = appendNote(contact.change_note, editorStamp("updated contact in dashboard."));
    }
  });
}

function addContact() {
  const lead = state.leads.find((item) => item.lead_id === state.selectedLeadId);
  if (!lead) return;
  applyLeadEdits({ rerender: false });

  const draft = {};
  els.newContactFields.querySelectorAll("[data-field]").forEach((input) => {
    const name = input.dataset.field.replace("new_contact.", "");
    draft[name] = input.value.trim();
  });

  const hasAnyValue = Object.values(draft).some((value) => !isBlank(value));
  if (!hasAnyValue) {
    setMessage("新增联系人至少需要填写一项信息。", true);
    return;
  }

  const contact = {};
  state.contactHeaders.forEach((header) => {
    contact[header] = "";
  });

  Object.assign(contact, draft, {
    contact_id: nextContactId(),
    lead_id: lead.lead_id,
    company_name: lead.company_name,
    is_primary_contact: getLeadContacts(lead.lead_id).length ? "No" : "Yes",
    last_researched_date: currentDate(),
    last_updated: currentTimestamp(),
    change_note: editorStamp("created contact in dashboard."),
  });

  state.contacts.push(contact);
  state.newContactDraft = {};
  setMessage(`已新增联系人到 ${lead.company_name || lead.lead_id}。导出 contacts.csv 后即可作为最新数据源。`);
  render();
}

function applyPreset(field, value, mode) {
  const input = els.editFields.querySelector(`[data-field="${field}"]`);
  if (!input) return;
  if (mode === "replace") {
    input.value = value;
  } else if (!input.value.includes(value)) {
    input.value = input.value.trim() ? `${input.value.trim()} ${value}` : value;
  }
}

function appendNote(existing, note) {
  const text = String(existing ?? "").trim();
  if (!text) return note;
  if (text.includes(note)) return text;
  return `${text} ${note}`;
}

function currentDate() {
  return new Date().toISOString().slice(0, 10);
}

function currentTimestamp() {
  const now = new Date();
  const pad = (value) => String(value).padStart(2, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`;
}

function nextContactId() {
  const maxId = state.contacts.reduce((max, contact) => {
    const match = String(contact.contact_id || "").match(/CONTACT-(\d+)/);
    return match ? Math.max(max, Number(match[1])) : max;
  }, 0);
  return `CONTACT-${String(maxId + 1).padStart(4, "0")}`;
}

function downloadCsv(filename, records, headers) {
  applyLeadEdits({ rerender: false });
  const blob = new Blob([toCsv(records, headers)], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  setMessage(`已导出 ${filename}。本次导出已写入编辑人、时间和修改记录。`);
  render();
}

function readFile(input, setter) {
  const file = input.files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    setter(String(reader.result || ""));
    setMessage(`已导入 ${file.name}。`);
  };
  reader.onerror = () => setMessage(`读取 ${file.name} 失败。`, true);
  reader.readAsText(file, "utf-8");
}

els.loadDefaultBtn.addEventListener("click", loadDefaults);
els.leadsCsvInput.addEventListener("change", () => readFile(els.leadsCsvInput, setLeads));
els.contactsCsvInput.addEventListener("change", () => readFile(els.contactsCsvInput, setContacts));
els.countryFilter.addEventListener("change", render);
els.missingFilter.addEventListener("change", render);
els.searchInput.addEventListener("input", render);
els.resetBtn.addEventListener("click", () => {
  els.countryFilter.value = "";
  els.missingFilter.value = "";
  els.searchInput.value = "";
  render();
});
els.leadList.addEventListener("click", (event) => {
  const button = event.target.closest("[data-select-lead]");
  if (!button) return;
  state.selectedLeadId = button.dataset.selectLead;
  render();
});
els.saveEditBtn.addEventListener("click", () => applyLeadEdits());
els.addContactBtn.addEventListener("click", addContact);
els.applyNextActionPresetBtn.addEventListener("click", () => applyPreset("next_action", els.nextActionPreset.value, "replace"));
els.appendNotesPresetBtn.addEventListener("click", () => applyPreset("notes", els.notesPreset.value, "append"));
els.appendEnrichmentPresetBtn.addEventListener("click", () => applyPreset("enrichment_notes", els.enrichmentNotesPreset.value, "append"));
els.exportLeadsBtn.addEventListener("click", () => downloadCsv("leads.csv", state.leads, state.leadHeaders));
els.exportContactsBtn.addEventListener("click", () => downloadCsv("contacts.csv", state.contacts, state.contactHeaders));

renderPresets();
loadDefaults();
