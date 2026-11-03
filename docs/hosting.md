# Render deployment

The Render Blueprint (`render.yaml`) runs the complete dashboard and Python API on one paid web-service instance with a 1 GB persistent disk, Python 3.14.8 and one Uvicorn worker. Review Render's displayed price before creating it. The configuration file alone does not deploy or incur charges.

Connect this private GitHub repository in Render, create a Blueprint from `main`, review the resource plan, and deploy after approving its cost. Automatic deploys are disabled; subsequent releases require deliberate manual deployment.

Render generates separate `AGENTVISA_ADMIN_TOKEN` and `AGENTVISA_AGENT_TOKEN` environment secrets. The agent identity is `procurement`. The database path is `/var/data/agentvisa.db` on the mounted disk. Do not reuse or upload the laptop's private configuration, credentials, or database. The hosted workspace starts empty.

Open the Render HTTPS URL and choose **Connect with credentials instead**. Use the two hosted secrets from Render's environment settings, with agent identity `procurement`. Keep these secrets private; the dashboard shell is public, but mission data and operations require credentials. Never place secrets in source control, URLs, screenshots or messages. An autonomous agent receives only its agent credential.

Verify `/health`, unauthenticated denial on `/visas`, mission creation and the human-review flow after deployment. Verify the same mission survives a service restart. Disk attachment must be present: an absolute path alone does not establish persistent storage. Do not use free ephemeral storage for durable budgets or audit history.

This remains a single-administrator simulation prototype. Hosting does not add multi-user identity, real purchases or independent audit anchoring. Keep deployment access limited to trusted operators, monitor storage usage, and export audit checkpoints separately. Deleting the service or disk can lose stored state; review Render's retention policies before deletion.

Provider references: [Blueprint configuration](https://render.com/docs/blueprint-spec), [persistent disks](https://render.com/docs/disks), [Python versions](https://render.com/docs/python-version).
