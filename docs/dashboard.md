# Local dashboard

Start the server from the repository with your environment activated:

```sh
python -m agentvisa serve
```

Open **http://127.0.0.1:8000/**. If an older server is already running, stop it with Control+C in its terminal, then run the command again. If the default port is busy, use `python -m agentvisa serve --port 8002` and open `http://127.0.0.1:8002/`.

The dashboard is included in both source and wheel installations. The API reference remains at `/docs`.

## Connect

Choose `.agentvisa.local.json` from your AgentVisa folder. On macOS, Command+Shift+. reveals hidden files in the file picker. The page reads the configuration locally, selects the configured agent (or lets you choose among several), and sends only the appropriate bearer credential to existing same-origin API endpoints. You can instead enter separate administrator and agent tokens manually.

This is a trusted human operator console: it can hold both roles for demonstration. Do not give its configuration to an autonomous agent. No credential-loading server endpoint, cookie login, or relaxed authorization was added. Credentials and displayed records are cleared on disconnect or page reload; the dashboard does not use local/session storage. Browser extensions or an untrusted browser can still access sensitive page data. Use a trusted local browser.

## Walk through a purchase

1. In **Missions**, keep a $300 budget and $250 approval threshold. Choose **Preview mission**, inspect the full contract, and choose **Issue this mission**. Issuance grants temporary authority; previewing does not.
2. Choose **Try an action with this mission**. Submit the search scenario to see ALLOW without spending money.
3. Select **Buy a productivity monitor · $275**, then **Submit new action**. The result is ASK_HUMAN if the remaining budget permits it.
4. Open **Human review**, choose **Inspect request**, review the exact action, cost, deadline, checks and fingerprint, then choose **Approve exact action** or **Reject request**.
5. After approval, choose **Retry inspected action as agent**. The gateway rechecks the current policy and commits a simulated purchase. Approval itself does not execute anything.
6. **Retry exact request** returns the previous result without a duplicate effect. **Check request status** reads historical state without executing.
7. Submit the $450 studio-monitor scenario to see a hard denial. Payroll and file-upload scenarios demonstrate mission and resource boundaries. No real files are read and no purchases/emails are sent.
8. Use **Activity** to inspect events and verify the local hash chain. In **Missions**, inspect remaining allowances or revoke a mission.

Each new proposal gets a new request ID. After an uncertain response, preserve the shown request ID and use status/retry before creating a new proposal. The exact retry payload is held only while the page remains open; after reload use the operator/API status workflow with the saved ID. Pending/approved requests can be inspected again from Human review. Expired or invalidated reviews cannot authorize execution. Creating another action after a successful purchase may exceed the remaining budget.

Lists are bounded, oldest first, with **Load more** for subsequent pages and **Refresh** to capture current state. Refreshing a list restarts its page traversal. Mission limits are snapshots, not reservations. Review controls reflect the last inspection; the server remains authoritative if a deadline or policy changes afterward. Network failures never trigger automatic mutation retries.

The dashboard is local-only and uses the existing monitor-procurement baseline. It adds no public hosting, arbitrary mission interpreter, real-provider adapter, or production identity service.
