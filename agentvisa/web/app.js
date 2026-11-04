"use strict";
const $ = (id) => document.getElementById(id),
  visas = new Map(),
  pages = {};
let sandboxVisa = null,
  session = null,
  draft = null,
  selectedVisa = null,
  lastRequest = null,
  inspected = null,
  imported = null,
  busy = false;
const money = (c) =>
    new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(c / 100),
  stamp = (s) => new Date(s * 1000).toLocaleString();
function el(tag, text, cls) {
  const e = document.createElement(tag);
  if (text !== undefined) e.textContent = text;
  if (cls) e.className = cls;
  return e;
}
function details(data, label = "Technical details") {
  const e = el("details");
  e.append(el("summary", label), el("pre", JSON.stringify(data, null, 2)));
  return e;
}
function notice(text, error = false) {
  $("notice").textContent = text;
  $("notice").className = error ? "error" : "";
  $("notice").hidden = false;
}

function updateGuide() {
  const connected = !!session;
  $("sandbox-shortcut").hidden = connected;
  const ready = connected && !!selectedVisa;
  $("next-step").hidden = !!session?.sandbox || (document.body.dataset.hosted === "true" && !connected);
  $("mission-connect-hint").hidden = connected;
  if (session?.sandbox) {
    $("guide-title").textContent = "Your sandbox is ready";
    $("guide-text").textContent = "Explore the sample mission, review a purchase, or create your own spending limits. Nothing spends real money. This workspace lasts 15 minutes.";
    $("guide-next").textContent = "Try an action";
    return;
  }
  $("guide-title").textContent = !connected ? "1. Connect your workspace" : ready ? "3. Try an action" : "2. Set your agent’s limits";
  $("guide-text").textContent = !connected
    ? "Connect once, set a spending limit, then see which actions are allowed or need your approval."
    : ready ? "Start with a catalog search. Then try a $275 monitor to see human review, or a $450 monitor to test the budget limit. Purchases use your remaining budget."
    : "The example is ready: a $300 monitor budget, with approval above $250. Preview the limits, then create your mission.";
  $("guide-next").textContent = !connected ? "Show connection options" : ready ? "Choose an action" : "Set up my mission";
}
$("guide-next").addEventListener("click", () => {
  if (!session) {
    $("connection").hidden = false;
    $("connection").scrollIntoView({ behavior: "smooth", block: "start" });
  } else if (selectedVisa) {
    $("action-visa").value = selectedVisa;
    view("actions");
    $("scenario").focus();
  } else {
    view("missions");
    $("budget").focus();
  }
});
if (document.body.dataset.hosted === "true") {
  $("manual-connection").open = true;
  $("connection").hidden = true;
}

function controls() {
  document
    .querySelectorAll("button")
    .forEach(
      (b) =>
        (b.disabled = busy || (b.hasAttribute("data-connected") && !session)),
    );
  $("issue").disabled = busy || !session || !draft;
  updateGuide();
}
async function run(fn) {
  if (busy) return;
  busy = true;
  controls();
  try {
    await fn();
  } catch (e) {
    notice(
      e.message ||
        "Request failed. Refresh current state before repeating a change.",
      true,
    );
  } finally {
    busy = false;
    controls();
  }
}
function bind(id, event, fn) {
  $(id).addEventListener(event, (e) => {
    if (event === "submit") e.preventDefault();
    return run(() => fn(e));
  });
}
async function api(
  path,
  role = "admin",
  method = "GET",
  body,
  allowMissing = false,
) {
  if (!session) throw Error("Connect your workspace first.");
  let r;
  try {
    r = await fetch((session.sandbox ? "/sandbox/api" : "") + path, {
      method,
      headers: {
        Authorization: "Bearer " + session[role],
        ...(session.sandbox ? { "X-Sandbox-ID": session.sandbox } : {}),
        ...(body ? { "Content-Type": "application/json" } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
      cache: "no-store",
      credentials: "omit",
      redirect: "error",
      signal: AbortSignal.timeout(15000),
    });
  } catch {
    throw Error(
      "Connection interrupted; outcome may be unknown. Refresh before repeating a change. For actions, check status or retry the exact request.",
    );
  }
  const data = await r.json();
  if (r.status === 404 && allowMissing) return null;
  if (!r.ok) {
    if (r.status === 401 || r.status === 403)
      throw Error(
        "Credential rejected. Check administrator and agent tokens and their roles.",
      );
    if (r.status === 404)
      throw Error(
        "Record not found in this snapshot. Refresh. A missing request does not rule out an in-flight action.",
      );
    throw Error(
      typeof data.detail === "string"
        ? data.detail
        : "Request rejected. Check values and refresh current state.",
    );
  }
  return data;
}
const titles = {
  missions: "Mission control",
  actions: "Try an action",
  approvals: "Human review",
  audit: "Activity",
};
function view(name) {
  document
    .querySelectorAll(".view")
    .forEach((e) => (e.hidden = e.id !== name + "-view"));
  document
    .querySelectorAll(".nav")
    .forEach((e) => {
      e.classList.toggle("active", e.dataset.view === name);
      if (e.dataset.view === name) e.setAttribute("aria-current", "page");
      else e.removeAttribute("aria-current");
    });
  $("welcome").hidden = !!session || name !== "missions";
  if (document.body.dataset.hosted === "true") $("connection").hidden = true;
  $("page-title").textContent = titles[name];
}
document
  .querySelectorAll(".nav")
  .forEach((e) => e.addEventListener("click", () => view(e.dataset.view)));
function clear() {
  session = draft = selectedVisa = lastRequest = inspected = imported = sandboxVisa = null;
  $("sandbox-tour").hidden = true;
  visas.clear();
  Object.keys(pages).forEach((k) => delete pages[k]);
  [
    "draft-panel",
    "visa-detail",
    "request-controls",
    "review-controls",
    "execute-approved",
    "identity-label",
  ].forEach((id) => ($(id).hidden = true));
  [
    "mission-list",
    "approval-list",
    "audit-list",
    "decision",
    "review-detail",
  ].forEach((id) =>
    $(id).replaceChildren(
      el("p", "Connect your workspace to get started.", "empty"),
    ),
  );
  ["draft-json", "visa-json", "draft-summary", "request-label"].forEach(
    (id) => ($(id).textContent = ""),
  );
  ["visa-summary", "identity-choice"].forEach((id) => $(id).replaceChildren());
  $("action-visa").replaceChildren(
    el("option", "Create or select a mission first"),
  );
  $("action-visa").firstChild.value = "";
  ["admin-token", "agent-token", "config-file"].forEach(
    (id) => ($(id).value = ""),
  );
  ["missions", "approvals", "audit"].forEach(
    (k) => ($("more-" + k).hidden = true),
  );
  $("connection").hidden = document.body.dataset.hosted === "true";
  $("session-toggle").textContent = document.body.dataset.hosted === "true" ? "Owner sign-in" : "Connect workspace";
  view("missions");
}
async function connect(admin, agent, identity, sandbox = null) {
  if (
    typeof admin !== "string" ||
    typeof agent !== "string" ||
    admin.length < 32 ||
    agent.length < 32 ||
    !identity ||
    admin === agent
  )
    throw Error(
      "Separate administrator and agent credentials and an agent identity are required.",
    );
  clear();
  session = { admin, agent, identity, sandbox };
  try {
    await api(
      "/requests/status?request_id=" + crypto.randomUUID(),
      "agent",
      "GET",
      undefined,
      true,
    );
    await load("missions");
  } catch (e) {
    clear();
    throw e;
  }
  $("connection").hidden = true;
  $("session-toggle").textContent = sandbox ? "Exit sandbox" : "Disconnect";
  $("welcome").hidden = true;
  $("decision").replaceChildren(
    el("p", "Submit an action to see its decision and explanation.", "empty"),
  );
  $("review-detail").replaceChildren(
    el("p", "Select a request to inspect its exact action.", "empty"),
  );
  notice(
    sandbox ? "Your private sandbox is ready. All purchases are simulated." : "Connected as human operator · agent " +
      identity +
      ". Credentials stay only in this page.",
  );
  await refresh();
}
bind("session-toggle", "click", () => {
  if (session) {
    clear();
    notice("Disconnected. Credentials and displayed records cleared.");
  } else {
    $("connection").hidden = !$("connection").hidden;
    if (!$("connection").hidden) $("connection").scrollIntoView({ behavior: "smooth" });
  }
});
bind("connect-form", "submit", () =>
  connect(
    $("admin-token").value.trim(),
    $("agent-token").value.trim(),
    $("agent-id").value.trim(),
  ),
);
bind("config-file", "change", async () => {
  const file = $("config-file").files[0];
  if (!file) return;
  if (file.size > 65536) throw Error("Configuration file is too large.");
  let c;
  try {
    c = JSON.parse(await file.text());
  } catch {
    throw Error("Choose a valid AgentVisa JSON configuration.");
  }
  const entries = Object.entries(c.agent_tokens || {});
  if (
    typeof c.admin_token !== "string" ||
    !entries.length ||
    entries.some(([t, id]) => typeof id !== "string" || t.length < 32)
  )
    throw Error(
      "Configuration needs an administrator token and configured agents.",
    );
  if (entries.length === 1)
    await connect(c.admin_token, entries[0][0], entries[0][1]);
  else {
    imported = { admin: c.admin_token, entries };
    $("identity-choice").replaceChildren(el("option", "Choose an agent"));
    $("identity-choice").firstChild.value = "";
    entries.forEach(([, id], i) => {
      const o = el("option", id);
      o.value = i;
      $("identity-choice").append(o);
    });
    $("identity-label").hidden = false;
  }
  $("config-file").value = "";
});
bind("identity-choice", "change", async () => {
  if (!imported || $("identity-choice").value === "") return;
  const c = imported,
    [token, id] = c.entries[Number($("identity-choice").value)];
  await connect(c.admin, token, id);
});
const configs = {
  missions: ["/visas", "mission-list"],
  approvals: ["/approvals", "approval-list"],
  audit: ["/audit/events", "audit-list"],
};
async function load(kind, more = false) {
  const [path, id] = configs[kind],
    q = new URLSearchParams({ limit: "25" });
  if (more && pages[kind]?.has_more) {
    q.set("after", pages[kind].next_after);
    q.set("through", pages[kind].through);
  }
  const result = await api(path + "?" + q);
  pages[kind] = result;
  if (!more) {
    $(id).replaceChildren();
    if (kind === "missions") visas.clear();
  }
  if (!result.items.length && !more)
    $(id).append(
      el(
        "p",
        kind === "missions"
          ? "No missions yet. Create your first mission."
          : kind === "approvals"
            ? "No outstanding requests. Actions needing approval appear here."
            : "No activity yet. Issue a mission to begin.",
        "empty",
      ),
    );
  for (const item of result.items) {
    const card = el("article", undefined, "row-card");
    if (kind === "missions") {
      visas.set(item.id, item);
      card.append(
        el("h3", item.contract.mission),
        el(
          "p",
          item.contract.agent_id +
            " · " +
            item.status +
            " · " +
            money(item.spent) +
            " spent of " +
            money(item.contract.spending_limit),
        ),
        el("p", "Expires " + stamp(item.contract.expires_at)),
      );
      const b = el("button", "Inspect mission", "secondary");
      b.addEventListener("click", () => run(() => inspectVisa(item.id)));
      card.append(b);
    } else if (kind === "approvals") {
      card.append(
        el("h3", item.action.tool.replaceAll("_", " ")),
        el(
          "p",
          item.agent +
            " · " +
            item.approval_status +
            " · " +
            (item.cost_cents === null
              ? "Cost unavailable"
              : money(item.cost_cents)),
        ),
        el("p", item.request_id),
      );
      const b = el("button", "Inspect request", "secondary");
      b.addEventListener("click", () =>
        run(() => inspectReview(item.agent, item.request_id)),
      );
      card.append(b);
    } else {
      const e = item.event;
      card.append(
        el(
          "span",
          e.decision || e.event || "EVENT",
          "badge " + (e.decision || ""),
        ),
        el(
          "h3",
          "#" + item.sequence + " · " + (e.tool || e.event || "Activity"),
        ),
        el("p", e.reason || e.visa_id || ""),
        details(e, "Event details"),
      );
    }
    $(id).append(card);
  }
  $("more-" + kind).hidden = !result.has_more;
  if (kind === "missions") {
    const previous = $("action-visa").value;
    $("action-visa").replaceChildren(el("option", "Select a mission"));
    $("action-visa").firstChild.value = "";
    for (const [id, v] of visas) {
      if (v.contract.agent_id !== session.identity) continue;
      const o = el(
        "option",
        v.contract.mission + " · " + id.slice(0, 12) + " · " + v.status,
      );
      o.value = id;
      $("action-visa").append(o);
    }
    $("action-visa").value = previous;
  }
}
async function refresh() {
  await load("approvals");
  await load("audit");
}
for (const k of Object.keys(configs)) {
  bind("refresh-" + k, "click", () => load(k));
  bind("more-" + k, "click", () => load(k, true));
}
bind("mission-form", "submit", async () => {
  draft = null;
  $("draft-panel").hidden = true;
  const budget = Math.round(Number($("budget").value) * 100),
    threshold = Math.round(Number($("threshold").value) * 100);
  if (
    !Number.isSafeInteger(budget) ||
    !Number.isSafeInteger(threshold) ||
    threshold > budget
  )
    throw Error("Approval threshold must be within the total budget.");
  const r = await api("/drafts", "admin", "POST", {
    mission: "Buy a monitor under $" + (budget / 100).toFixed(2) + ".",
    agent_id: session.identity,
  });
  draft = { ...r.contract, approval_threshold: threshold };
  $("draft-summary").textContent =
    money(budget) +
    " budget and maximum transaction. Ask above " +
    money(threshold) +
    ". " +
    draft.max_actions +
    " actions, delegation depth " +
    draft.delegation_depth +
    ". Expires " +
    stamp(draft.expires_at) +
    ".";
  $("draft-json").textContent = JSON.stringify(draft, null, 2);
  $("draft-panel").hidden = false;
});
for (const id of ["budget", "threshold"])
  $(id).addEventListener("input", () => {
    draft = null;
    $("draft-panel").hidden = true;
    controls();
  });
bind("issue", "click", async () => {
  if (!draft) return;
  const c = draft;
  draft = null;
  $("draft-panel").hidden = true;
  const r = await api("/visas", "admin", "POST", c);
  await load("missions");
  await inspectVisa(r.visa_id);
  const data = await api(
    "/visas/inspect?" + new URLSearchParams({ visa_id: r.visa_id }),
  );
  if (!visas.has(r.visa_id)) {
    const o = el("option", c.mission + " · " + r.visa_id.slice(0, 12));
    o.value = r.visa_id;
    $("action-visa").append(o);
    visas.set(r.visa_id, data.chain[0]);
  }
  $("action-visa").value = r.visa_id;
  view("actions");
  $("scenario").focus();
  notice("Mission created. Start with a catalog search, then try a purchase.");
  await load("audit");
});
async function inspectVisa(id) {
  const d = await api("/visas/inspect?" + new URLSearchParams({ visa_id: id }));
  selectedVisa = id;
  $("visa-detail").hidden = false;
  $("visa-json").textContent = JSON.stringify(d, null, 2);
  $("visa-summary").replaceChildren();
  const l = d.effective_limits;
  for (const [v, label] of [
    [money(l.remaining_budget_cents), "Budget remaining"],
    [money(l.approval_threshold_cents), "Approval above"],
    [l.remaining_actions, "Actions remaining"],
  ]) {
    const e = el("div", undefined, "metric");
    e.append(el("strong", v), el("span", label));
    $("visa-summary").append(e);
  }
  if (d.blockers.length)
    $("visa-summary").append(
      el(
        "p",
        "Current blockers: " + d.blockers.map((b) => b.reason).join(", "),
      ),
    );
}
bind("use-visa", "click", () => {
  $("action-visa").value = selectedVisa;
  view("actions");
});
bind("revoke", "click", async () => {
  if (
    !selectedVisa ||
    !confirm(
      "Revoke this mission and invalidate outstanding reviews for its descendants?",
    )
  )
    return;
  await api(
    "/visas/" + encodeURIComponent(selectedVisa) + "/revoke",
    "admin",
    "POST",
  );
  await inspectVisa(selectedVisa);
  await load("missions");
  await refresh();
  notice("Mission revoked. New actions will be denied.");
});
const scenarios = {
  search: [
    "search_products",
    "catalog:monitors",
    { query: "monitor" },
    "Read the trusted catalog without spending money.",
  ],
  compare: [
    "compare_products",
    "catalog:monitors",
    { product_ids: ["monitor-basic", "monitor-pro"] },
    "Compare the $180 and $275 monitors.",
  ],
  basic: [
    "purchase",
    "vendor:approved",
    { product_id: "monitor-basic", quantity: 1 },
    "A $180 simulated purchase. Remaining budget and approval threshold still apply.",
  ],
  pro: [
    "purchase",
    "vendor:approved",
    { product_id: "monitor-pro", quantity: 1 },
    "A $275 simulated purchase. With a $300 budget and $250 threshold, this needs approval.",
  ],
  ultra: [
    "purchase",
    "vendor:approved",
    { product_id: "monitor-ultra", quantity: 1 },
    "A $450 simulated purchase. A $300 mission must deny it.",
  ],
  drift: [
    "send_email",
    "vendor:approved",
    {
      recipient: "sales@approved.example",
      body: "Please send the employee payroll report.",
    },
    "Vendor email is permitted, but requesting payroll is outside a monitor mission.",
  ],
  upload: [
    "upload_file",
    "storage:external",
    { file: "file:employees.csv", destination: "storage:external" },
    "A simulated forbidden upload. No local file is read.",
  ],
};
function hint() {
  $("scenario-hint").textContent = scenarios[$("scenario").value][3];
}
$("scenario").addEventListener("change", hint);
hint();
function decision(r) {
  const e = $("decision");
  e.replaceChildren(
    el("span", r.decision, "badge " + r.decision),
    el(
      "h3",
      r.executed
        ? "Simulated action executed"
        : r.decision === "ASK_HUMAN"
          ? "Waiting for your review"
          : "No action executed",
      "decision-title",
    ),
    el("p", r.decision === "DENY" && r.reason.includes("cumulative_budget")
      ? "This purchase exceeds the mission’s remaining budget. Approval cannot override that limit."
      : r.reason),
  );
  if (r.cost_cents !== undefined)
    e.append(
      el(
        "p",
        "Cost: " +
          money(r.cost_cents) +
          (r.replayed ? " · Historical result replayed; no new effect." : ""),
      ),
    );
  e.append(details(r));
  if (r.decision === "ASK_HUMAN") {
    const b = el("button", "Review this action", "secondary");
    const pending = lastRequest && structuredClone(lastRequest);
    b.addEventListener("click", () => run(async () => {
      view("approvals");
      if (pending) await inspectReview(session.identity, pending.request_id);
    }));
    e.append(b);
  }
}
async function execute(body) {
  lastRequest = structuredClone(body);
  $("request-controls").hidden = false;
  $("request-label").textContent = "Request " + body.request_id;
  $("decision").replaceChildren(
    el(
      "p",
      "Awaiting response. If interrupted, check status or retry this exact request.",
    ),
  );
  const r = await api("/execute", "agent", "POST", body);
  decision(r);
  if (session.sandbox && body.request_id === "sample-review" && r.executed) $("sandbox-tour").hidden = true;
  await load("missions");
  notice(
    r.replayed
      ? "Stored result replayed; no new effect."
      : r.decision === "ASK_HUMAN"
        ? "Action is waiting for human review."
        : r.executed
          ? "Simulated action executed."
          : "Action denied; no effect committed.",
  );
  await refresh();
}
bind("action-form", "submit", async () => {
  const visa = $("action-visa").value;
  if (!visa) throw Error("Create or select a mission first.");
  const [tool, resource, args] = scenarios[$("scenario").value];
  await execute({
    request_id: crypto.randomUUID(),
    visa_id: visa,
    tool,
    resource,
    arguments: structuredClone(args),
    context: "",
  });
});
bind("retry", "click", () => execute(lastRequest));
bind("request-status", "click", async () => {
  const r = await api(
    "/requests/status?" +
      new URLSearchParams({ request_id: lastRequest.request_id }),
    "agent",
  );
  decision(r.last_response);
  $("decision").prepend(
    el(
      "p",
      "Stored state: " +
        r.state +
        (r.review_expired ? " · Review expired" : "") +
        ". The decision below is historical.",
    ),
  );
});
async function inspectReview(agent, id) {
  inspected = null;
  $("review-controls").hidden = true;
  $("execute-approved").hidden = true;
  const d = await api(
    "/approvals/inspect?" + new URLSearchParams({ agent, request_id: id }),
  );
  inspected = d;
  $("review-detail").replaceChildren(
    el("h3", d.mission),
    el("p", d.reason),
    el(
      "p",
      "Cost: " +
        (d.cost_cents === null ? "unavailable" : money(d.cost_cents)) +
        " · Status: " +
        d.approval_status,
    ),
    el(
      "p",
      "Review deadline: " + stamp(d.deadline) + (d.expired ? " · EXPIRED" : ""),
    ),
    el("h3", "Exact proposed action"),
    el("p", d.action.tool === "purchase"
      ? "Buy " + d.action.arguments.quantity + " × " + ({"monitor-pro": "productivity computer monitor", "monitor-basic": "office computer monitor", "monitor-ultra": "studio computer monitor"}[d.action.arguments.product_id] || d.action.arguments.product_id) + " from the approved vendor."
      : d.action.tool.replaceAll("_", " ") + " · " + d.action.resource),
    details({ action: d.action, fingerprint: d.fingerprint }, "Exact request and fingerprint"),
    details(d, "Policy and intent checks"),
  );
  $("review-controls").hidden = d.expired || d.approval_status !== "pending";
  $("execute-approved").hidden =
    d.expired ||
    d.approval_status !== "approved" ||
    d.agent !== session.identity;
}
async function review(approve) {
  if (!inspected) return;
  const d = inspected;
  $("review-controls").hidden = true;
  await api("/approvals", "admin", "POST", {
    agent_id: d.agent,
    request_id: d.request_id,
    approve,
    expected_fingerprint: d.fingerprint,
  });
  notice(
    approve
      ? "Approved. Choose Run approved action to simulate this purchase. Limits are checked again before it runs."
      : "Request rejected. No action was executed.",
  );
  if (approve) await inspectReview(d.agent, d.request_id);
  else {
    inspected = null;
    $("review-detail").replaceChildren(el("p", "Request rejected."));
  }
  await refresh();
}
bind("approve", "click", () => review(true));
bind("reject", "click", () => review(false));
bind("execute-approved", "click", async () => {
  const action = structuredClone(inspected.action);
  $("execute-approved").hidden = true;
  view("actions");
  await execute(action);
});
bind("integrity", "click", async () => {
  const r = await api("/audit/integrity");
  notice(
    r.valid
      ? "Local audit chain is consistent. This is not an independently anchored proof of history."
      : "Local audit chain verification failed.",
    !r.valid,
  );
});
$("sandbox-shortcut").addEventListener("click", () => $("start-sandbox").click());
bind("start-sandbox", "click", async () => {
  $("start-sandbox").textContent = "Preparing your sandbox…";
  try {
    const response = await fetch("/sandbox/start", { method: "POST", credentials: "omit", redirect: "error", cache: "no-store", signal: AbortSignal.timeout(60000) });
    const data = await response.json();
    if (!response.ok) throw Error(data.detail || "Sandbox could not start. Please try again.");
    await connect(data.admin, data.agent, data.identity, data.workspace);
    sandboxVisa = data.visa_id;
    selectedVisa = data.visa_id;
    $("action-visa").value = data.visa_id;
    $("sandbox-tour").hidden = false;
    view("actions");
    decision(data.blocked);
  } finally {
    $("start-sandbox").textContent = "Try the sandbox →";
  }
});
bind("sandbox-review", "click", async () => {
  view("approvals");
  await inspectReview(session.identity, "sample-review");
});
bind("sandbox-block", "click", async () => {
  await execute({ request_id: crypto.randomUUID(), visa_id: sandboxVisa, tool: "purchase", resource: "vendor:approved", arguments: { product_id: "monitor-ultra", quantity: 1 }, context: "" });
});
view("missions");
window.addEventListener("pagehide", clear);
controls();
