#!/usr/bin/env python3
"""Video Review: turns links in links.txt into transcripts + screenshots.

Part of the Pretty Technical Club toolkit (prettytechnicalclub.com).
Run it with "Review Videos.command" (double-click). Everything runs on your Mac;
nothing is uploaded anywhere. Output goes to the "reviews" folder.
"""
import datetime
import json
import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
LINKS = HERE / "links.txt"
DONE = HERE / ".done.txt"
OUT = HERE / "reviews"
TMP = OUT / "_working"
MODEL = "mlx-community/whisper-large-v3-turbo"
FRAMES = int(os.environ.get("FRAMES", "6"))  # set FRAMES=0 to skip screenshots


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def mmss(sec):
    sec = int(sec or 0)
    return f"{sec // 60:02d}:{sec % 60:02d}"


def read_links():
    items = []
    if not LINKS.exists():
        return items
    for line in LINKS.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        url, _, note = s.partition(" | ")
        url = url.strip()
        if url.startswith("http"):
            items.append((url, note.strip()))
    return items


def download(url):
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True)
    if "/photo/" in url:
        return None, ["this is a TikTok photo slideshow, not a video. Screenshot it and drop it in the dashboard inbox instead."]
    # Prefer a file that has sound; otherwise merge the best video + audio
    base = ["yt-dlp", "--no-playlist", "--write-info-json",
            "-f", "b[vcodec^=h264][acodec!=none]/download/b[vcodec!=none][acodec!=none]/bv*+ba/b",
            "--merge-output-format", "mp4", "-o", str(TMP / "video.%(ext)s"), url]
    login = ["--cookies-from-browser", "chrome"]
    # Instagram almost always wants a login, so use your Chrome login straight away
    first = base[:-1] + login + [url] if "instagram.com" in url else base
    r = run(first)
    if r.returncode != 0 and first is base:
        print("   Retrying with your Chrome login (macOS may ask for your password once)…")
        r = run(base[:-1] + login + [url])
    if r.returncode != 0:
        msg = ((r.stderr or r.stdout).strip().splitlines() or ["unknown error"])[-1]
        if "instagram" in url and ("login" in msg.lower() or "cookie" in msg.lower()):
            msg = "Instagram wants a login. Open Chrome, make sure you're logged into Instagram, then run this again."
        elif "private" in msg.lower():
            msg = "the post is private or deleted."
        return None, [msg]
    vids = [p for p in TMP.iterdir() if p.suffix.lower() in (".mp4", ".mov", ".webm", ".mkv", ".m4v")]
    infos = list(TMP.glob("*.info.json"))
    if not vids:
        return None, ["no video file came down"]
    info = json.loads(infos[0].read_text(encoding="utf-8")) if infos else {}
    return (vids[0], info), None


def transcribe(video):
    import mlx_whisper  # installed by the launcher
    res = mlx_whisper.transcribe(str(video), path_or_hf_repo=MODEL)
    segs = res.get("segments") or []
    lines = [f"[{mmss(s.get('start'))}] {s.get('text', '').strip()}" for s in segs if s.get("text", "").strip()]
    return "\n".join(lines) or (res.get("text") or "").strip()


def frames(video, duration, folder):
    names = []
    dur = float(duration or 0)
    if dur <= 0:
        r = run(["ffmpeg", "-i", str(video)])
        for part in r.stderr.split("Duration:")[1:2]:
            h, m, s = part.split(",")[0].strip().split(":")
            dur = int(h) * 3600 + int(m) * 60 + float(s)
    dur = dur or 30
    for k in range(FRAMES):
        t = (k + 0.5) * dur / FRAMES
        name = f"frame-{k + 1:02d}-{mmss(t).replace(':', 'm')}s.jpg"
        r = run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(video),
                 "-frames:v", "1", "-vf", "scale=720:-2", "-q:v", "3", str(folder / name)])
        if r.returncode == 0:
            names.append(name)
    return names


def main():
    links = read_links()
    done = set(DONE.read_text().split()) if DONE.exists() else set()
    todo = [(u, n) for u, n in links if u not in done]
    if not todo:
        print("No new links in links.txt. Paste some in, save, and run again.")
        return
    OUT.mkdir(exist_ok=True)
    today = datetime.date.today().isoformat()
    batch = OUT / f"batch-{today}.md"
    new_batch = not batch.exists()
    with batch.open("a", encoding="utf-8") as b:
        if new_batch:
            b.write(f"# Video batch {today}\n\n")
        for i, (url, note) in enumerate(todo, 1):
            print(f"\n[{i}/{len(todo)}] {url}")
            got, err = download(url)
            if not got:
                print("   Couldn't download:", err[0])
                b.write(f"## Could not download\n{url}\nReason: {err[0]}\n\n")
                continue
            video, info = got
            vid = str(info.get("id") or i)
            site = (info.get("extractor_key") or "video").lower()
            folder = OUT / f"{today}-{site}-{vid}"
            folder.mkdir(exist_ok=True)
            print("   Transcribing…")
            ok = True
            try:
                text = transcribe(video)
            except Exception as e:  # keep going on one bad file
                ok = False
                msg = str(e)
                text = ("(no sound track came down with this video; it will retry next run)"
                        if "does not contain any stream" in msg else
                        "(transcription failed: " + msg.strip().splitlines()[0][:200] + ")")
            print("   Grabbing screenshots…")
            shots = frames(video, info.get("duration"), folder)
            up = info.get("upload_date") or ""
            posted = f"{up[:4]}-{up[4:6]}-{up[6:]}" if len(up) == 8 else ""
            stats = ", ".join(f"{k} {info[v]:,}" for k, v in (("views", "view_count"), ("likes", "like_count"), ("comments", "comment_count")) if isinstance(info.get(v), int))
            md = [f"## {info.get('title') or info.get('description', '')[:80] or url}",
                  f"- Link: {url}",
                  f"- Creator: {info.get('uploader') or info.get('channel') or ''} {('@' + info['uploader_id']) if info.get('uploader_id') else ''}".rstrip(),
                  f"- Posted: {posted}" if posted else None,
                  f"- Length: {mmss(info.get('duration'))}" if info.get("duration") else None,
                  f"- Stats: {stats}" if stats else None,
                  f"- Your note: {note}" if note else None,
                  f"- Screenshots: {folder.name}/ ({len(shots)})",
                  "", "**Caption**", "", (info.get("description") or "(none)").strip(),
                  "", "**Transcript**", "", text or "(no speech)", "", "---", ""]
            entry = "\n".join(x for x in md if x is not None)
            (folder / "review.md").write_text(entry, encoding="utf-8")
            b.write(entry + "\n")
            if ok:
                with DONE.open("a") as d:
                    d.write(url + "\n")
            print("   Done →", folder.name)
    if TMP.exists():
        shutil.rmtree(TMP)
    print(f"\nAll set. Everything is in: {batch}")
    print("Next: give the reviews folder to Claude with prompts/video-takeaways.md.")


if __name__ == "__main__":
    sys.exit(main())
