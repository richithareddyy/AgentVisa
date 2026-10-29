"""Public static dashboard; all data and mutations use authenticated API routes."""
from importlib.resources import files
from fastapi import HTTPException
from fastapi.responses import Response

HEADERS = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
}


def install_dashboard(app):
    def asset(name, media_type):
        return Response(files("agentvisa").joinpath("web", name).read_bytes(),
                        media_type=media_type, headers=HEADERS)

    @app.get("/", include_in_schema=False)
    def dashboard():
        return asset("index.html", "text/html")

    @app.get("/dashboard/{name}", include_in_schema=False)
    def dashboard_asset(name: str):
        allowed = {"app.js": "text/javascript", "style.css": "text/css"}
        if name not in allowed:
            raise HTTPException(404, "asset not found")
        return asset(name, allowed[name])
