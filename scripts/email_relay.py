import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


HOST = os.getenv("EMAIL_RELAY_HOST", "0.0.0.0")
PORT = int(os.getenv("EMAIL_RELAY_PORT", "8800"))
RELAY_TOKEN = os.getenv("EMAIL_RELAY_TOKEN", "renalwatch-demo-relay")


class RelayHandler(BaseHTTPRequestHandler):
    def _json_response(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path != "/send":
            self._json_response(404, {"error": "not_found"})
            return

        if self.headers.get("X-Relay-Token") != RELAY_TOKEN:
            self._json_response(401, {"error": "unauthorized"})
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(content_length) or b"{}")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = payload["subject"]
        msg["From"] = payload["smtp_email"]
        msg["To"] = payload["to"]
        msg.attach(MIMEText(payload["body"], "plain"))

        body_html = payload.get("body_html")
        if body_html:
            msg.attach(MIMEText(body_html, "html"))

        smtp_server = payload["smtp_server"]
        smtp_port = int(payload["smtp_port"])
        smtp_timeout = int(payload.get("smtp_timeout", 15))

        if payload.get("smtp_use_ssl", True):
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=smtp_timeout)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=smtp_timeout)
            server.starttls()

        with server:
            server.login(payload["smtp_email"], payload["smtp_password"])
            server.send_message(msg)

        self._json_response(200, {"status": "sent"})

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), RelayHandler)
    print(f"RenalWatch email relay listening on http://{HOST}:{PORT}")
    server.serve_forever()
