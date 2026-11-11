#!/usr/bin/env python3
"""ici-game-ads: produce Google App campaign video and image creatives from a plan file.

Standard library only. Needs ffmpeg/ffprobe on PATH and Google Chrome (or Chromium)
for the end card. API keys are read from the environment or from
~/.config/ici-game-ads/keys.env and are never printed.

Usage:
  gameads.py check
  gameads.py frames   <plan.json> [video ids...]   start (+ end) frames for videos
  gameads.py render   <plan.json> [video ids...]   image-to-video for each video
  gameads.py assemble <plan.json> [video ids...]   end card + audio -> final mp4
  gameads.py images   <plan.json> [image ids...]   text-free image ads in 3 sizes
  gameads.py sheet    <file> [out.jpg]             contact sheet of a video or image list

All paths inside the plan are relative to the current working directory
(run the script from the game's repository root).
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

KEYS_FILE = Path(os.path.expanduser("~/.config/ici-game-ads/keys.env"))
UA = "ici-game-ads/1.0"
VIDEO_SIZE = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080)}
IMAGE_SHAPES = {  # name: (request aspect, final width, final height)
    "land": ("16:9", 1200, 628),
    "sq": ("1:1", 1200, 1200),
    "port": ("4:5", 1200, 1500),
}
END_CARD_SECONDS = 2.8
XFADE = 0.3
LOUDNESS = "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000"  # even loudness across games with quiet or loud music


def die(msg: str) -> None:
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def key(name: str, required: bool = True) -> str | None:
    val = os.environ.get(name)
    if not val and KEYS_FILE.exists():
        for line in KEYS_FILE.read_text().splitlines():
            if line.startswith(name + "="):
                val = line.split("=", 1)[1].strip()
    if not val and required:
        die(f"{name} is not set. Put it in {KEYS_FILE} (chmod 600) or export it.")
    return val


def run(cmd: list[str]) -> None:
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        die("command failed: " + " ".join(cmd[:3]) + " ...\n" + res.stderr[-1500:])


def probe(path: Path, entries: str, stream: str | None = None) -> str:
    cmd = ["ffprobe", "-v", "error", "-show_entries", entries, "-of", "csv=p=0"]
    if stream:
        cmd += ["-select_streams", stream]
    return subprocess.run(cmd + [str(path)], capture_output=True, text=True).stdout.strip()


def data_uri(path: Path, max_side: int = 1920) -> str:
    """JPEG data URI of an image, downscaled so the longest side is at most max_side."""
    if not path.exists():
        die(f"reference image not found: {path}")
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "ref.jpg"
        scale = f"scale='if(gt(iw,ih),min(iw,{max_side}),-2)':'if(gt(iw,ih),-2,min(ih,{max_side}))'"
        run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-vf", scale + ",format=yuvj420p", "-q:v", "2", str(out)])
        return "data:image/jpeg;base64," + base64.b64encode(out.read_bytes()).decode()


def http_json(url: str, headers: dict, body: dict | None = None, timeout: int = 600) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={**headers, "Content-Type": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def download(url: str, out: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=600) as resp:
        out.write_bytes(resp.read())
    print("saved", out)


# ---------------------------------------------------------------- providers

def fal(endpoint: str, body: dict) -> dict:
    headers = {"Authorization": "Key " + key("FAL_KEY")}
    try:
        queued = http_json("https://queue.fal.run/" + endpoint, headers, body)
        while True:
            status = http_json(queued["status_url"], headers)
            if status["status"] == "COMPLETED":
                break
            time.sleep(4)
        return http_json(queued["response_url"], headers)
    except urllib.error.HTTPError as err:
        die(f"fal {endpoint}: HTTP {err.code} {err.read().decode()[:800]}")
    return {}


def gen_image_fal(prompt: str, refs: list[Path], aspect: str, out: Path, model: str) -> None:
    res = fal(model, {"prompt": prompt, "image_urls": [data_uri(p) for p in refs], "aspect_ratio": aspect,
                      "resolution": "2K", "output_format": "png", "num_images": 1})
    download(res["images"][0]["url"], out)


def gen_image_codefast(prompt: str, refs: list[Path], aspect: str, out: Path, model: str) -> None:
    base = os.environ.get("CODEFAST_BASE_URL", "https://api.codefast.app/gpt-image-2-api/v1")
    headers = {"Authorization": "Bearer " + key("CODEFAST_KEY")}
    images = [data_uri(p) for p in refs]
    last = ""
    for quality in ("high", "high", "medium"):  # the gateway times out on slow jobs: retry, then lower quality
        try:
            res = http_json(base + "/images/edits", headers,
                            {"model": model, "prompt": prompt, "aspect_ratio": aspect, "quality": quality, "images": images})
        except urllib.error.HTTPError as err:
            last = f"HTTP {err.code}"
            print(f"{out.name}: {last}, retrying", file=sys.stderr)
            continue
        item = (res.get("data") or [{}])[0]
        if item.get("b64_json"):
            out.write_bytes(base64.b64decode(item["b64_json"]))
            print("saved", out)
            return
        if item.get("url"):
            download(item["url"], out)
            return
        last = "unexpected response"
    die(f"codefast image generation failed for {out.name}: {last}")


def gen_image(plan: dict, prompt: str, refs: list[Path], aspect: str, out: Path, provider: str | None = None) -> None:
    if not refs:
        die(f"{out.name}: at least one reference image from the real game is required")
    provider = provider or plan.get("image_provider", "fal")
    if provider == "codefast":
        gen_image_codefast(prompt, refs, aspect, out, plan.get("codefast_model", "gpt-image-2"))
    else:
        gen_image_fal(prompt, refs, aspect, out, plan.get("fal_image_model", "fal-ai/nano-banana-pro/edit"))


# ---------------------------------------------------------------- plan helpers

def load_plan(path: str) -> dict:
    plan = json.loads(Path(path).read_text())
    for field in ("game", "out_dir"):
        if field not in plan:
            die(f"plan is missing '{field}'")
    return plan


def dirs(plan: dict) -> tuple[Path, Path, Path]:
    out = Path(plan["out_dir"])
    work, videos, images = out / "work", out / "videos", out / "images"
    for d in (work, videos, images):
        d.mkdir(parents=True, exist_ok=True)
    return work, videos, images


def ref_paths(plan: dict, names: list[str]) -> list[Path]:
    table = plan.get("refs", {})
    paths = []
    for name in names:
        if name not in table and not Path(name).exists():
            die(f"unknown reference '{name}' (not in plan.refs and not a file)")
        paths.append(Path(table.get(name, name)))
    return paths


def pick(items: list[dict], ids: list[str]) -> list[dict]:
    chosen = [i for i in items if not ids or i["id"] in ids]
    if ids and len(chosen) != len(set(ids)):
        die("unknown id(s): " + ", ".join(sorted(set(ids) - {i["id"] for i in items})))
    return chosen


def with_style(plan: dict, prompt: str, video: bool = False) -> str:
    style = plan.get("video_style" if video else "style", "")
    negative = plan.get("negative", "No text, no letters, no numbers, no logos, no user interface, no hands, no humans.")
    return "\n\n".join(p for p in (prompt, style, negative) if p)


# ---------------------------------------------------------------- commands

def cmd_check(_: list[str]) -> None:
    for tool in ("ffmpeg", "ffprobe"):
        print(f"{tool}: {'ok' if shutil.which(tool) else 'MISSING'}")
    print(f"chrome: {'ok' if chrome() else 'MISSING'}")
    print(f"keys file: {KEYS_FILE} ({'found' if KEYS_FILE.exists() else 'missing'})")
    for name in ("FAL_KEY", "CODEFAST_KEY"):
        print(f"{name}: {'set' if key(name, required=False) else 'not set'}")


def cmd_frames(args: list[str]) -> None:
    plan = load_plan(args[0])
    work, _, _ = dirs(plan)

    def one(video: dict) -> None:
        vid, aspect = video["id"], video["aspect"]
        start = work / f"{vid}_start.png"
        gen_image(plan, with_style(plan, video["start"]["prompt"]), ref_paths(plan, video["start"]["refs"]), aspect, start,
                  provider=plan.get("frame_provider", "fal"))
        if video.get("end"):
            refs = [start] + ref_paths(plan, video["end"].get("refs", []))
            gen_image(plan, with_style(plan, video["end"]["prompt"]), refs, aspect, work / f"{vid}_end.png",
                      provider=plan.get("frame_provider", "fal"))

    with ThreadPoolExecutor(4) as pool:
        list(pool.map(one, pick(plan.get("videos", []), args[1:])))


def cmd_render(args: list[str]) -> None:
    plan = load_plan(args[0])
    work, _, _ = dirs(plan)
    model = plan.get("video_model", "minimax/h3-max-turbo/image-to-video")

    def one(video: dict) -> None:
        vid = video["id"]
        start, end = work / f"{vid}_start.png", work / f"{vid}_end.png"
        if not start.exists():
            die(f"{start} missing: run 'frames' first")
        body = {"prompt": with_style(plan, video["motion"], video=True), "image_url": data_uri(start),
                "duration": video.get("duration", 10), "resolution": plan.get("video_resolution", "768P"),
                "prompt_expansion_mode": "balanced"}
        if end.exists():
            body["end_image_url"] = data_uri(end)
        res = fal(model, body)
        download(res["video"]["url"], work / f"{vid}_raw.mp4")
        sheet(work / f"{vid}_raw.mp4", work / f"{vid}_sheet.jpg")

    with ThreadPoolExecutor(4) as pool:
        list(pool.map(one, pick(plan.get("videos", []), args[1:])))


def chrome() -> str | None:
    for cand in (os.environ.get("CHROME_PATH"), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                 shutil.which("google-chrome"), shutil.which("chromium"), shutil.which("chromium-browser")):
        if cand and Path(cand).exists():
            return cand
    return None


def end_card(plan: dict, aspect: str, out: Path) -> None:
    game = plan["game"]
    width, height = VIDEO_SIZE[aspect]
    template = (Path(__file__).resolve().parent.parent / "assets" / "end_card.html").read_text()
    colors = {"bg_inner": "#4f9bff", "bg_mid": "#1f5fd6", "bg_outer": "#0f2f8f", "title": "#ffd23a", "stroke": "#0d2a7a",
              **game.get("colors", {})}

    def file_url(p: str | None) -> str:
        return "file://" + urllib.parse.quote(str(Path(p).resolve())) if p else ""

    params = {"name": game["name"], "tagline": game.get("tagline", ""), "cta": game.get("cta", "PLAY FREE"),
              "icon": file_url(game.get("icon")), "mascot": file_url(game.get("mascot_image")),
              "font": file_url(game.get("font")), "layout": {"9:16": "port", "16:9": "land", "1:1": "sq"}[aspect], **colors}
    if any(word in params["cta"].lower() for word in ("download", "install")):
        die("cta must not contain 'Download' or 'Install' (Google disapproves such overlays)")
    binary = chrome()
    if not binary:
        die("Google Chrome/Chromium not found (set CHROME_PATH)")
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "card.html"
        page.write_text(template.replace("__PARAMS__", json.dumps(params)))
        run([binary, "--headless=new", "--allow-file-access-from-files", "--hide-scrollbars", "--force-device-scale-factor=1",
             f"--window-size={width},{height}", "--virtual-time-budget=3000", f"--screenshot={out}", "file://" + str(page)])
    if not out.exists():
        die("end card render failed")


def cmd_assemble(args: list[str]) -> None:
    plan = load_plan(args[0])
    work, videos, _ = dirs(plan)
    slug = plan["game"].get("slug", "game")
    audio = plan.get("audio", {})
    for video in pick(plan.get("videos", []), args[1:]):
        vid, aspect = video["id"], video["aspect"]
        raw = work / f"{vid}_raw.mp4"
        if not raw.exists():
            die(f"{raw} missing: run 'render' first")
        width, height = VIDEO_SIZE[aspect]
        length = float(video.get("duration", 10))
        total = length + END_CARD_SECONDS - XFADE
        card = work / f"end_card_{aspect.replace(':', 'x')}.png"
        end_card(plan, aspect, card)

        inputs = ["-i", str(raw), "-loop", "1", "-t", str(END_CARD_SECONDS), "-i", str(card)]
        vf = (f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},fps=30,setsar=1,"
              f"trim=0:{length},setpts=PTS-STARTPTS,format=yuv420p[v0];"
              f"[1:v]fps=30,scale={width}:{height},setsar=1,format=yuv420p[e];"
              f"[v0][e]xfade=transition=fade:duration={XFADE}:offset={length - XFADE}[v]")
        maps = ["-map", "[v]"]
        if audio.get("music"):
            inputs += ["-stream_loop", "-1", "-i", audio["music"]]
            parts = [f"[2:a]volume={audio.get('music_volume', 0.55)},atrim=0:{total},afade=out:st={total - 0.8}:d=0.8[m]"]
            labels = ["[m]"]
            for n, fx in enumerate(video.get("sfx", [])):
                inputs += ["-i", fx["file"]]
                parts.append(f"[{3 + n}:a]adelay={int(fx['at'] * 1000)}:all=1,volume={fx.get('volume', 1.0)}[s{n}]")
                labels.append(f"[s{n}]")
            parts.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=first,{LOUDNESS}[a]")
            vf += ";" + ";".join(parts)
            maps += ["-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
        elif probe(raw, "stream=codec_type", "a"):
            vf += f";[0:a]atrim=0:{length},afade=out:st={length - 0.4}:d=0.4,apad=whole_dur={total},{LOUDNESS}[a]"
            maps += ["-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
        final = videos / f"{slug}_{vid}_{aspect.replace(':', 'x')}.mp4"
        run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", vf, *maps, "-c:v", "libx264", "-crf", "18",
             "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-t", str(total), str(final)])
        print("saved", final, f"({total:.1f}s, {width}x{height})")
        if total < 10:
            print(f"WARNING: {final.name} is shorter than 10 s, the Google App campaign minimum", file=sys.stderr)


def cmd_images(args: list[str]) -> None:
    plan = load_plan(args[0])
    work, _, images = dirs(plan)
    slug = plan["game"].get("slug", "game")
    jobs = []
    for image in pick(plan.get("images", []), args[1:]):
        for shape, opts in image.get("shapes", {"land": {}, "sq": {}, "port": {}}).items():
            if shape not in IMAGE_SHAPES:
                die(f"unknown shape '{shape}' (use land, sq, port)")
            jobs.append((image, shape, opts or {}))

    def one(job: tuple[dict, str, dict]) -> None:
        image, shape, opts = job
        aspect, width, height = IMAGE_SHAPES[shape]
        art = work / f"img_{image['id']}_{shape}.png"
        prompt = image["prompt"] + " " + plan.get("shape_hints", {}).get(shape, "")
        gen_image(plan, with_style(plan, prompt), ref_paths(plan, image["refs"]), aspect, art)
        focus = float(opts.get("y", 50)) / 100
        final = images / f"{slug}_{shape}_{image['id']}.jpg"
        run(["ffmpeg", "-v", "error", "-y", "-i", str(art), "-vf",
             f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}:(iw-{width})/2:(ih-{height})*{focus}",
             "-q:v", "2", str(final)])
        print("saved", final)

    with ThreadPoolExecutor(4) as pool:
        list(pool.map(one, jobs))


def sheet(src: Path, out: Path) -> None:
    """Contact sheet: 12 frames of a video, or a directory of images side by side."""
    if src.is_dir():
        files = sorted(p for p in src.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))[:12]
        if not files:
            die(f"no images in {src}")
        inputs, parts = [], []
        for n, f in enumerate(files):
            inputs += ["-i", str(f)]
            parts.append(f"[{n}]scale=320:320:force_original_aspect_ratio=decrease,pad=320:320:(ow-iw)/2:(oh-ih)/2:white[i{n}]")
        cols = min(6, len(files))
        layout = "|".join(f"{(n % cols) * 320}_{(n // cols) * 320}" for n in range(len(files)))
        graph = ";".join(parts) + ";" + "".join(f"[i{n}]" for n in range(len(files))) + f"xstack=inputs={len(files)}:layout={layout}:fill=white"
        run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph, "-frames:v", "1", str(out)])
    else:
        width = int(probe(src, "stream=width", "v:0") or 1)
        height = int(probe(src, "stream=height", "v:0") or 1)
        cell = "320:-2" if width >= height else "-2:320"
        run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", f"fps=1.2,scale={cell},tile=6x2", "-frames:v", "1", str(out)])
    print("saved", out)


def cmd_sheet(args: list[str]) -> None:
    src = Path(args[0])
    sheet(src, Path(args[1]) if len(args) > 1 else src.with_name(src.stem + "_sheet.jpg"))


COMMANDS = {"check": cmd_check, "frames": cmd_frames, "render": cmd_render, "assemble": cmd_assemble,
            "images": cmd_images, "sheet": cmd_sheet}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS or (sys.argv[1] != "check" and len(sys.argv) < 3):
        print(__doc__)
        sys.exit(2)
    COMMANDS[sys.argv[1]](sys.argv[2:])
