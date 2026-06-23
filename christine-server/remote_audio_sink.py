"""Minimal remote audio sink for temporary Broca output bypass.

Run this on the external Raspberry Pi that has working audio output hardware.
It accepts WAV bytes and plays them synchronously so Broca timing stays intact.
"""

import json
import logging
import os
import signal
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Single-file logging to keep troubleshooting simple.
os.makedirs("./logs", exist_ok=True)
logging.basicConfig(
    filename="./logs/remote_audio_sink.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

playback_lock = threading.Lock()
process_lock = threading.Lock()


class SinkState:
    """Shared mutable state for playback process tracking."""

    current_process = None


def clamp_volume(raw_value: str) -> int:
    """Parse and clamp volume to ALSA percentage range."""
    try:
        volume = int(raw_value)
    except (TypeError, ValueError):
        return 100
    return max(0, min(100, volume))


def set_alsa_volume(volume: int):
    """Set output volume using ALSA mixer without raising on failure."""
    subprocess.run(
        ["amixer", "-q", "cset", "numid=1", f"{volume}%"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


class AudioSinkHandler(BaseHTTPRequestHandler):
    """HTTP endpoints: GET /health, POST /play, POST /stop."""

    server_version = "ChristineRemoteAudio/1.0"

    def _send_json(self, status_code: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # pylint: disable=invalid-name
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
            return

        self._send_json(404, {"error": "not found"})

    def do_POST(self):  # pylint: disable=invalid-name
        if self.path == "/play":
            self._handle_play()
            return

        if self.path == "/stop":
            self._handle_stop()
            return

        self._send_json(404, {"error": "not found"})

    def _handle_play(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            self._send_json(400, {"error": "missing audio body"})
            return

        volume = clamp_volume(self.headers.get("X-Volume", "100"))
        audio_bytes = self.rfile.read(content_length)

        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_path = temp_file.name
        temp_file.close()

        try:
            with open(temp_path, "wb") as out_file:
                out_file.write(audio_bytes)

            with playback_lock:
                set_alsa_volume(volume)

                with process_lock:
                    SinkState.current_process = subprocess.Popen(
                        ["aplay", "-q", temp_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )

                return_code = SinkState.current_process.wait()

                with process_lock:
                    SinkState.current_process = None

                if return_code != 0:
                    logging.error("Playback failed with return code %s", return_code)
                    self._send_json(500, {"error": "playback failed", "return_code": return_code})
                    return

            self._send_json(200, {"status": "played"})

        except Exception as ex:  # pylint: disable=broad-exception-caught
            logging.exception("Error during playback: %s", ex)
            self._send_json(500, {"error": str(ex)})

        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    def _handle_stop(self):
        with process_lock:
            proc = SinkState.current_process

        if proc is None or proc.poll() is not None:
            self._send_json(200, {"status": "idle"})
            return

        try:
            proc.terminate()
            try:
                proc.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                proc.send_signal(signal.SIGKILL)

            with process_lock:
                SinkState.current_process = None

            self._send_json(200, {"status": "stopped"})

        except Exception as ex:  # pylint: disable=broad-exception-caught
            logging.exception("Error stopping playback: %s", ex)
            self._send_json(500, {"error": str(ex)})

if __name__ == "__main__":
    bind_host = os.getenv("CHRISTINE_REMOTE_AUDIO_BIND", "0.0.0.0")
    bind_port = int(os.getenv("CHRISTINE_REMOTE_AUDIO_PORT", "3002"))

    logging.info("Starting remote audio sink on %s:%s", bind_host, bind_port)
    server = ThreadingHTTPServer((bind_host, bind_port), AudioSinkHandler)
    server.serve_forever()
