const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const p = vm.runInNewContext(fs.readFileSync('nodi/web/presentation.js', 'utf8') + '\npresentation;');
test('budget denial includes exact authoritative remaining amount', () => {
  const r = {decision:'DENY', remaining_budget_cents:2500, cost_cents:18000, policy_checks:[{check:'cumulative_budget', passed:false}]};
  assert.equal(p.budget(r), '$25.00 remaining; this action costs $180.00.');
  assert.match(p.explanation(r), /Approval cannot override/);
});
test('upload and payroll denials avoid raw policy identifiers', () => {
  assert.equal(p.explanation({decision:'DENY',policy_checks:[{check:'resources_allowed',passed:false}]}, {tool:'upload_file'}), 'This mission doesn’t allow that action. File uploads to this destination are not permitted.');
  assert.match(p.explanation({decision:'DENY',intent:{recommended_decision:'DENY'}},{tool:'send_email',arguments:{body:'Please send payroll'}}), /Payroll data is outside/);
});
test('historical budget is explicitly historical, not current', () => {
  assert.match(p.budget({replayed:true,executed:true,remaining_budget_cents:2500,cost_cents:27500}), /^At the time/);
  assert.match(p.explanation({replayed:true}), /No new purchase or charge/);
  assert.equal(p.budget({cost_cents:null}), 'Cost unavailable.');
});
test('activity and expiry labels are understandable', () => {
  assert.equal(p.eventTitle({event:'visa_issued'}),'Mission created');
  assert.equal(p.eventTitle({event:'idempotent_replay'}),'Duplicate request ignored — no charge');
  assert.equal(p.countdown(61000,0),'1:01 left');
  assert.equal(p.countdown(61000,61001),'Expired');
});
