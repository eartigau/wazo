#!/usr/bin/env python3
"""
Serveur local pour l'interface de curation des photos.

Lance un serveur HTTP qui sert admin_photos.html et expose une API
pour lire/écrire photo_curation.csv directement, sans passer par un
téléchargement manuel.

Usage:
    python serve_admin_photos.py [--port 8766] [--curation photo_curation.csv]
"""
from __future__ import annotations

import argparse
import csv
import json
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


VALID_STATUSES = {"best", "include", "reject"}


class AdminPhotosHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, directory: str, curation_path: Path, **kwargs: Any) -> None:
        self.curation_path = curation_path
        super().__init__(*args, directory=directory, **kwargs)

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def do_GET(self) -> None:
        if self.path == "/api/curation":
            self._handle_get_curation()
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path == "/api/curation":
            self._handle_post_curation()
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _handle_get_curation(self) -> None:
        data = self._read_curation_csv()
        self._send_json(HTTPStatus.OK, {"curation": data})

    def _handle_post_curation(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)
            body = json.loads(raw.decode("utf-8") or "{}")
        except (ValueError, json.JSONDecodeError):
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON payload")
            return

        curation = body.get("curation", {})
        if not isinstance(curation, dict):
            self.send_error(HTTPStatus.BAD_REQUEST, "'curation' must be an object")
            return

        # Valider les statuts
        normalized: dict[str, str] = {}
        for ml, status in curation.items():
            if not isinstance(ml, str) or not ml.strip():
                continue
            status = str(status).strip()
            if status not in VALID_STATUSES:
                self.send_error(HTTPStatus.BAD_REQUEST, f"Invalid status '{status}' for ml '{ml}'")
                return
            normalized[ml.strip()] = status

        self._write_curation_csv(normalized)
        self._send_json(HTTPStatus.OK, {"saved": len(normalized)})

    # ------------------------------------------------------------------
    # CSV helpers
    # ------------------------------------------------------------------

    def _read_curation_csv(self) -> dict[str, str]:
        if not self.curation_path.exists():
            return {}
        result: dict[str, str] = {}
        try:
            with self.curation_path.open(newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    ml = (row.get("ml_number") or "").strip()
                    status = (row.get("status") or "include").strip()
                    if ml:
                        result[ml] = status
        except Exception as exc:
            self.log_error("Erreur lecture curation: %s", exc)
        return result

    def _write_curation_csv(self, curation: dict[str, str]) -> None:
        with self.curation_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["ml_number", "status"])
            writer.writeheader()
            for ml, status in sorted(curation.items()):
                writer.writerow({"ml_number": ml, "status": status})

    # ------------------------------------------------------------------
    # JSON helper
    # ------------------------------------------------------------------

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, fmt: str, *args: Any) -> None:  # moins verbeux
        if "/api/" in (args[0] if args else ""):
            super().log_message(fmt, *args)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serveur local de curation des photos eBird.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Dossier racine à servir.",
    )
    parser.add_argument(
        "--curation",
        type=Path,
        default=Path("photo_curation.csv"),
        help="Fichier CSV de curation (relatif à --root par défaut).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    curation_path = args.curation if args.curation.is_absolute() else root / args.curation

    handler = partial(AdminPhotosHandler, directory=str(root), curation_path=curation_path)
    with ThreadingHTTPServer((args.host, args.port), handler) as server:
        url = f"http://{args.host}:{args.port}/admin_photos.html"
        print(f"Serveur actif sur {url}")
        print(f"Curation: {curation_path}")
        print("Ctrl+C pour arrêter.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServeur arrêté.")


if __name__ == "__main__":
    main()
