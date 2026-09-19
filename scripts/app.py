"""Loopback-only local evidence workspace. Inference is off unless explicitly enabled."""

import argparse
import json
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from pypdf import PdfReader

from scripts.corpus import ROOT, document, documents, pdf_path
from scripts.local_smoke import MODEL, api
from scripts.page_preview import render_page
from scripts.rag import answer_profile, answer_question
from scripts.retrieval_check import build_index


class Workspace:
    def __init__(self, allow_gpu=False):
        self.allow_gpu = allow_gpu
        self.jobs = {}
        self.indexes = {}
        self.lock = threading.Lock()
        self.busy = False

    def submit(self, doc_id, question, answer_kind="numeric"):
        doc = document(doc_id)
        answer_profile(answer_kind)
        if not isinstance(question, str) or not question.strip() or len(question) > 1200:
            raise ValueError("Enter a question of 1-1200 characters")
        if not self.allow_gpu:
            raise PermissionError("GPU inference is disabled for this session")
        with self.lock:
            if self.busy:
                raise RuntimeError("A question is already running")
            self.busy = True
            job_id = uuid.uuid4().hex
            if len(self.jobs) >= 20:
                self.jobs.pop(next(iter(self.jobs)))
            self.jobs[job_id] = {"status": "preparing", "document_id": doc_id}
        threading.Thread(
            target=self.run, args=(job_id, doc, question, answer_kind), daemon=True
        ).start()
        return job_id

    def run(self, job_id, doc, question, answer_kind="numeric"):
        started = time.perf_counter()
        outcome = {}
        try:
            doc_id = doc["document_id"]
            if doc_id not in self.indexes:
                self.indexes[doc_id] = build_index("table-v1", doc_id)
            retriever, tokenizer, _ = self.indexes[doc_id]
            with self.lock:
                self.jobs[job_id]["status"] = "running"
            result = answer_question(
                question,
                retriever,
                tokenizer,
                PdfReader(pdf_path(doc_id)),
                document=doc,
                answer_kind=answer_kind,
            )
            public = {k: v for k, v in result.items() if k not in ("messages", "raw_response")}
            public["wall_seconds"] = time.perf_counter() - started
            outcome = {"status": "complete", "result": public}
        except Exception as error:
            outcome = {"status": "error", "error": str(error)}
        finally:
            with self.lock:
                self.jobs[job_id]["status"] = "unloading"
            try:
                api("/api/generate", {"model": MODEL, "keep_alive": 0})
                loaded = api("/api/ps").get("models", [])
                if any(m.get("name") == MODEL or m.get("model") == MODEL for m in loaded):
                    raise RuntimeError("Local model is still loaded after cleanup")
            except Exception as error:
                outcome["cleanup_error"] = str(error)
            with self.lock:
                self.jobs[job_id].update(outcome)
                self.busy = False

    def snapshot(self, job_id):
        with self.lock:
            if job_id not in self.jobs:
                raise ValueError("Unknown or expired job")
            return dict(self.jobs[job_id])


def saved_examples():
    # Fixed real development run, explicitly labeled as saved rather than live output.
    path = ROOT / "artifacts/demo/20260919T065722467425Z-generation.json"
    if not path.exists():
        return []
    report = json.loads(path.read_text(encoding="utf-8"))
    return [
        {"recording": path.name, **row} for row in report["results"]
    ]


def make_server(port=8765, allow_gpu=False):
    workspace = Workspace(allow_gpu)

    class Handler(BaseHTTPRequestHandler):
        def permitted_host(self):
            return self.headers.get("Host") in (
                f"127.0.0.1:{self.server.server_port}",
                f"localhost:{self.server.server_port}",
            )

        def send_bytes(self, status, data, content_type):
            ancestors = "'self'" if content_type == "application/pdf" else "'none'"
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; frame-src 'self'; object-src 'self'; "
                f"frame-ancestors {ancestors}; base-uri 'none'; form-action 'self'",
            )
            self.end_headers()
            self.wfile.write(data)

        def json(self, status, payload):
            self.send_bytes(status, json.dumps(payload).encode(), "application/json; charset=utf-8")

        def do_GET(self):
            if not self.permitted_host():
                self.json(403, {"error": "Untrusted host"})
                return
            path = urlparse(self.path).path
            try:
                if path == "/api/state":
                    self.json(
                        200,
                        {
                            "documents": documents(),
                            "allow_gpu": workspace.allow_gpu,
                            "model": MODEL,
                        },
                    )
                elif path == "/api/saved":
                    self.json(200, saved_examples())
                elif path.startswith("/api/jobs/"):
                    self.json(200, workspace.snapshot(path.removeprefix("/api/jobs/")))
                elif path.startswith("/pdf/"):
                    doc_id = path.removeprefix("/pdf/")
                    self.send_bytes(200, pdf_path(doc_id).read_bytes(), "application/pdf")
                elif path.startswith("/page/"):
                    parts = path.removeprefix("/page/").split("/")
                    if len(parts) != 2:
                        raise ValueError("Expected document and PDF page")
                    self.send_bytes(200, render_page(parts[0], int(parts[1])), "image/png")
                elif path in ("/", "/app.js", "/style.css"):
                    name, mime = {
                        "/": ("index.html", "text/html"),
                        "/app.js": ("app.js", "text/javascript"),
                        "/style.css": ("style.css", "text/css"),
                    }[path]
                    self.send_bytes(
                        200, (ROOT / "web" / name).read_bytes(), mime + "; charset=utf-8"
                    )
                else:
                    self.json(404, {"error": "Not found"})
            except (ValueError, FileNotFoundError) as error:
                self.json(404, {"error": str(error)})

        def do_POST(self):
            origins = {
                f"http://127.0.0.1:{self.server.server_port}",
                f"http://localhost:{self.server.server_port}",
            }
            if not self.permitted_host() or self.headers.get("Origin") not in origins:
                self.json(403, {"error": "Same-origin request required"})
                return
            if self.path != "/api/question":
                self.json(404, {"error": "Not found"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 8192 or self.headers.get_content_type() != "application/json":
                    raise ValueError("Expected a bounded JSON request")
                body = json.loads(self.rfile.read(length))
                if (
                    not isinstance(body, dict)
                    or not {"document_id", "question"} <= set(body)
                    or set(body) - {"document_id", "question", "answer_kind"}
                ):
                    raise ValueError("Expected document_id and question")
                job_id = workspace.submit(
                    body["document_id"], body["question"], body.get("answer_kind", "numeric")
                )
                self.json(202, {"job_id": job_id})
            except (ValueError, TypeError) as error:
                self.json(400, {"error": str(error)})
            except PermissionError as error:
                self.json(403, {"error": str(error)})
            except RuntimeError as error:
                self.json(409, {"error": str(error)})

        def log_message(self, *_):
            pass

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--allow-gpu", action="store_true")
    args = parser.parse_args()
    with make_server(args.port, args.allow_gpu) as server:
        print(
            f"FinSight-RAG: http://127.0.0.1:{server.server_port} "
            f"(GPU inference {'enabled' if args.allow_gpu else 'disabled'})",
            flush=True,
        )
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
