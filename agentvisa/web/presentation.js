"use strict";
// Presentation only: authorization decisions and budget snapshots come from the gateway.
const presentation = (() => {
  const money = (c) => new Intl.NumberFormat("en-US", {style:"currency", currency:"USD"}).format(c / 100);
  function explanation(r, action = r.action) {
    if (r.replayed) return "Duplicate request ignored. No new purchase or charge was made.";
    if (r.decision === "ALLOW") return r.human_intervention
      ? "You approved this action. Its limits were checked again before it ran."
      : "This action fits the mission and its limits.";
    if (r.decision === "ASK_HUMAN") return "This action needs your approval before it can run. Approval does not override the budget or other limits.";
    const failed = new Set((r.policy_checks || []).filter(c => !c.passed).map(c => c.check));
    const messages = [];
    if (failed.has("active")) messages.push("This mission has been revoked or is no longer active.");
    if (failed.has("unexpired") || failed.has("unexpired_after_evaluation")) messages.push("This mission has expired. Create a new mission to continue.");
    if (failed.has("cumulative_budget")) messages.push("Over the mission’s budget. Approval cannot override that limit.");
    else if (failed.has("transaction_limit")) messages.push("Over the mission’s budget for a single transaction.");
    if (["operation_allowed", "resources_allowed", "resources_not_forbidden", "tool_allowed"].some(x => failed.has(x)))
      messages.push(action?.tool === "upload_file" ? "This mission doesn’t allow that action. File uploads to this destination are not permitted." : "This mission doesn’t allow that action or resource access.");
    if (failed.has("action_limit")) messages.push("This mission has used all of its allowed actions.");
    if (failed.has("delegation_depth")) messages.push("This mission exceeds the permitted number of delegation steps.");
    if (messages.length) return messages.join(" ");
    if ((r.reason || "").includes("different action")) return "This request was already used for a different action. Submit a new action instead.";
    if (/expired|deadline/i.test(r.reason || "")) return "This approval or mission has expired. Submit a new request under an active mission.";
    if (/rejected|invalidated/i.test(r.reason || "")) return "This approval was rejected or is no longer valid. Submit a new request if you want it reviewed again.";
    if (r.reason === "Message content is unrelated to procurement" || r.intent?.recommended_decision === "DENY") return /payroll/i.test(action?.arguments?.body || "")
      ? "Payroll data is outside this mission’s scope. This mission only authorizes buying computer monitors."
      : "This action is outside the mission’s purpose of buying computer monitors.";
    return "This action could not be authorized under the mission’s limits. No action was performed. See Technical details for the recorded checks.";
  }
  function budget(r) {
    if (!Number.isSafeInteger(r.remaining_budget_cents)) return Number.isSafeInteger(r.cost_cents) ? "This action costs " + money(r.cost_cents) + "." : "Cost unavailable.";
    const label = r.replayed ? "At the time of this recorded decision: " : "";
    return label + money(r.remaining_budget_cents) + " remaining" + (Number.isSafeInteger(r.cost_cents) ? "; this action " + (r.executed ? "cost " : "costs ") + money(r.cost_cents) : "") + ".";
  }
  function eventTitle(e) {
    const labels = {visa_issued:"Mission created", visa_revoked:"Mission revoked", visa_modified:"Mission limits updated", delegation_denied:"Delegation blocked", idempotent_replay:"Duplicate request ignored — no charge", replay_conflict:"Changed duplicate request blocked"};
    if (e.event === "human_review") return "You reviewed a request";
    if (e.event === "authorization") return {ALLOW:"Allowed", DENY:"Blocked", ASK_HUMAN:"Asked for approval"}[e.decision] || "Action checked";
    return labels[e.event] || "Activity recorded";
  }
  function countdown(deadline, now) {
    const seconds = Math.max(0, Math.ceil((deadline - now) / 1000));
    return seconds ? Math.floor(seconds / 60) + ":" + String(seconds % 60).padStart(2, "0") + " left" : "Expired";
  }
  return {explanation, budget, eventTitle, countdown};
})();
