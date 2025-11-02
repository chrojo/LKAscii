import os, re, time, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

ANIMS_DIR = "anims"
DEFAULT_FPS = 15
DEFAULT_LOOPS = 50

ALT_SCREEN_ON  = b"\x1b[?1049h"
ALT_SCREEN_OFF = b"\x1b[?1049l"
HIDE_CURSOR    = b"\x1b[?25l"
SHOW_CURSOR    = b"\x1b[?25h"
HOME           = b"\x1b[H"
CLEAR_ONCE     = b"\x1b[2J"

def natural_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

def load_and_normalize_frames(folder):
    # Read all .txt frames in natural order
    names = [f for f in os.listdir(folder) if f.endswith(".txt")]
    if not names:
        raise FileNotFoundError(f"No .txt frames in {folder}")
    names.sort(key=natural_key)

    raw = []
    for name in names:
        with open(os.path.join(folder, name), "r", encoding="utf-8") as fh:
            raw.append(fh.read().rstrip("\n"))

    # Normalize to same width/height (pad with spaces)
    split = [r.splitlines() for r in raw]
    max_h = max(len(lines) for lines in split)
    max_w = max(max((len(line) for line in lines), default=0) for lines in split)

    norm = []
    for lines in split:
        lines = [line.ljust(max_w) for line in lines]
        if len(lines) < max_h:
            lines += [" " * max_w] * (max_h - len(lines))
        norm.append("\n".join(lines))

    return norm, max_w, max_h

# Cache: {name: (frames, w, h)}
CACHE = {}

def list_anims():
    if not os.path.isdir(ANIMS_DIR):
        return []
    return sorted(
        [d for d in os.listdir(ANIMS_DIR) if os.path.isdir(os.path.join(ANIMS_DIR, d))],
        key=natural_key
    )

class AsciiHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.strip("/")
        qs = urllib.parse.parse_qs(parsed.query)

        if path == "":  # index
            anims = list_anims()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            if not anims:
                self.wfile.write(f"No animations found.\nCreate folders in ./{ANIMS_DIR}/ like 'panda', 'cowy', each with .txt frames.\n".encode())
                return
            listing = "Available animations:\n" + "\n".join(f"  /{name}" for name in anims) + \
                      "\n\nExample: curl --no-buffer http://localhost:8080/panda?fps=15&loops=30\n"
            self.wfile.write(listing.encode())
            return

        # Only letters, numbers, -, _
        if not re.fullmatch(r"[A-Za-z0-9_\-]+", path):
            self.send_response(400); self.end_headers(); self.wfile.write(b"Invalid animation name"); return

        # Load from cache or disk
        try:
            if path not in CACHE:
                folder = os.path.join(ANIMS_DIR, path)
                frames, w, h = load_and_normalize_frames(folder)
                CACHE[path] = (frames, w, h)
        except FileNotFoundError:
            self.send_response(404); self.end_headers(); self.wfile.write(b"Animation not found"); return

        frames, w, h = CACHE[path]
        # Query overrides
        try:
            fps = max(1, int(qs.get("fps", [DEFAULT_FPS])[0]))
        except ValueError:
            fps = DEFAULT_FPS
        try:
            loops = max(1, int(qs.get("loops", [DEFAULT_LOOPS])[0]))
        except ValueError:
            loops = DEFAULT_LOOPS

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

        delay = 1.0 / fps
        try:
            # Alternate screen, hide cursor, clear once
            self.wfile.write(ALT_SCREEN_ON + HIDE_CURSOR + CLEAR_ONCE + HOME)
            self.wfile.flush()

            for _ in range(loops):
                for frame in frames:
                    # No full clear each frame; just move cursor home and overwrite
                    out = HOME + frame.encode("utf-8") + b"\n"
                    self.wfile.write(out)
                    self.wfile.flush()
                    time.sleep(delay)
        finally:
            try:
                self.wfile.write(SHOW_CURSOR + ALT_SCREEN_OFF)
                self.wfile.flush()
            except Exception:
                pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print(f"🎥 ASCII server running on 0.0.0.0:{port}")
    HTTPServer(("0.0.0.0", port), AsciiHandler).serve_forever()