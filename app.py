from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, render_template_string, request


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "corpus.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-only-secret"


def todo_response(feature: str):
	return jsonify(
		{
			"status": "todo",
			"feature": feature,
			"message": "This project scaffold is intentionally unresolved.",
		}
	), 501


def init_db() -> None:
	raise NotImplementedError("TODO: create the corpus.db schema on startup.")


def ingest_upload() -> None:
	raise NotImplementedError("TODO: extract uploaded content and persist it.")


def delete_document(document_id: int) -> None:
	raise NotImplementedError("TODO: delete a stored document.")


def toggle_document(document_id: int) -> None:
	raise NotImplementedError("TODO: toggle whether a document is active.")


def run_chat() -> None:
	raise NotImplementedError("TODO: generate a chat response from active corpus data.")


def generate_artifact(artifact_type: str) -> None:
	raise NotImplementedError(f"TODO: generate {artifact_type} output.")


def list_artifacts() -> None:
	raise NotImplementedError("TODO: return stored artifacts as JSON.")


def get_stats() -> None:
	raise NotImplementedError("TODO: report token usage totals.")


def save_settings() -> None:
	raise NotImplementedError("TODO: store prompt steering settings in the session.")


@app.get("/")
def index():
	return render_template_string(
		"""
		<!doctype html>
		<html lang="en">
		  <head>
			<meta charset="utf-8">
			<meta name="viewport" content="width=device-width, initial-scale=1">
			<title>Corpus Forge</title>
		  </head>
		  <body>
			<main>
			  <h1>Corpus Forge</h1>
			  <p>Project scaffold loaded. The app routes are intentionally unresolved.</p>
			</main>
		  </body>
		</html>
		"""
	)


@app.post("/upload")
def upload():
	return todo_response("upload")


@app.post("/documents/<int:document_id>/delete")
def document_delete(document_id: int):
	return todo_response(f"delete document {document_id}")


@app.post("/documents/<int:document_id>/toggle")
def document_toggle(document_id: int):
	return todo_response(f"toggle document {document_id}")


@app.post("/chat")
def chat():
	return todo_response("chat")


@app.post("/generate/<artifact_type>")
def generate(artifact_type: str):
	return todo_response(f"generate {artifact_type}")


@app.get("/artifacts")
def artifacts():
	return todo_response("artifacts")


@app.get("/stats")
def stats():
	return todo_response("stats")


@app.post("/settings")
def settings():
	return todo_response("settings")


if __name__ == "__main__":
	app.run(debug=True)

