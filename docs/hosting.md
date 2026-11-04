# Free Render deployment

The Render Blueprint (`render.yaml`) runs the dashboard and Python API on one free web-service instance, with Python 3.14.8 and one Uvicorn worker. It has no paid disk. Automatic deploys are disabled; releases require manual deployment.

Connect the AgentVisa repository in Render and deploy `main` using the free plan. Build with `python -m pip install . -c requirements.lock`. Start with `python -m uvicorn agentvisa.hosted:create_hosted_app --factory --host 0.0.0.0 --port $PORT --workers 1 --no-access-log`. Set the health check to `/health`.

Set `PYTHON_VERSION=3.14.8`, `AGENTVISA_DB=/tmp/agentvisa.db`, and separate random `AGENTVISA_ADMIN_TOKEN` and `AGENTVISA_AGENT_TOKEN` secrets of at least 32 characters each. The Blueprint can generate these secrets. Do not upload laptop credentials or databases.

Open the Render HTTPS URL, choose **Connect with credentials instead**, and use the hosted secrets from Render environment settings with agent identity `procurement`. The dashboard shell is public; mission data and operations require credentials. Keep secrets out of source control, URLs, screenshots, and messages. Give an autonomous agent only its agent credential.

Free hosting has ephemeral storage. Missions, budgets, approvals, and audit history can disappear on restart or redeployment. The dashboard displays this limitation. Free instances also spin down during inactivity, so opening the site can take longer. Use sample data only; this deployment is unsuitable for durable spending enforcement or audit retention.

Verify `/health`, unauthenticated denial on `/visas`, mission creation, and the human-review flow after deployment. This remains a single-administrator simulation prototype, without real purchases or multi-user identity.

Provider references: [Blueprint configuration](https://render.com/docs/blueprint-spec), [persistent disks](https://render.com/docs/disks), [free services](https://render.com/docs/free).
