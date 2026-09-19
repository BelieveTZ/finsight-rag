import http.client
import json
import threading

import pytest

from scripts.app import Workspace, make_server


@pytest.fixture
def server():
    instance = make_server(0)
    thread = threading.Thread(target=instance.serve_forever, daemon=True)
    thread.start()
    yield instance
    instance.shutdown()
    instance.server_close()
    thread.join()


def request(server, method, path, body=None, origin=True):
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=10)
    headers = {"Content-Type": "application/json"}
    if origin:
        headers["Origin"] = f"http://127.0.0.1:{server.server_port}"
    connection.request(method, path, None if body is None else json.dumps(body), headers)
    response = connection.getresponse()
    status, data = response.status, response.read()
    connection.close()
    return status, data


def test_default_app_cannot_start_gpu(server):
    status, data = request(server, "GET", "/api/state")
    assert status == 200 and not json.loads(data)["allow_gpu"]
    status, data = request(
        server,
        "POST",
        "/api/question",
        {"document_id": "3M_2018_10K", "question": "3M revenue 2018?"},
    )
    assert status == 403 and b"disabled" in data


def test_cross_origin_and_missing_origin_requests_rejected(server):
    assert request(server, "POST", "/api/question", {}, origin=False)[0] == 403


def test_fact_mode_cannot_bypass_gpu_opt_in(server):
    body = {"document_id": "3M_2018_10K", "question": "3M 2018 business?", "answer_kind": "fact"}
    assert request(server, "POST", "/api/question", body)[0] == 403
    body["answer_kind"] = "unknown"
    assert request(server, "POST", "/api/question", body)[0] == 400


def test_path_traversal_and_unknown_routes_rejected(server):
    assert request(server, "GET", "/pdf/../../.env")[0] == 404
    assert request(server, "GET", "/api/jobs/not-a-job")[0] == 404
    assert request(server, "GET", "/.cache/private.json")[0] == 404


def test_saved_outputs_are_labeled_and_ui_is_available(server):
    status, data = request(server, "GET", "/api/saved")
    assert status == 200
    rows = json.loads(data)
    assert len(rows) == 6
    assert all("recording" in r and "document_id" in r for r in rows)
    assert sum(r["answer_kind"] == "fact" for r in rows) == 2
    assert sum(r["answer"]["status"] == "insufficient_evidence" for r in rows) == 2
    assert request(server, "GET", "/")[0] == 200


def test_only_pdf_can_be_embedded_by_same_origin(server, monkeypatch, tmp_path):
    from scripts import app

    pdf = tmp_path / "report.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    monkeypatch.setattr(app, "pdf_path", lambda doc_id: pdf)
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=10)
    for path, expected in (("/", "'none'"), ("/pdf/3M_2018_10K", "'self'")):
        connection.request("GET", path)
        response = connection.getresponse()
        assert response.status == 200
        assert f"frame-ancestors {expected}" in response.getheader("Content-Security-Policy")
        response.read()
    connection.close()


def test_service_error_is_not_converted_to_refusal(monkeypatch):
    from scripts import app
    from scripts.corpus import document

    def fail(*args):
        raise RuntimeError("Model connection failed")

    monkeypatch.setattr(app, "build_index", fail)
    monkeypatch.setattr(app, "api", lambda *args: {})
    workspace = Workspace(True)
    workspace.jobs["one"] = {"status": "preparing"}
    workspace.busy = True
    workspace.run("one", document("3M_2018_10K"), "3M 2018 revenue?")
    assert workspace.snapshot("one")["status"] == "error"
    assert "result" not in workspace.snapshot("one")
    assert not workspace.busy
