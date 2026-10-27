#!/bin/bash
# Double-click to turn the links in links.txt into transcripts + screenshots.
cd "$(dirname "$0")" || exit 1
VENV="$HOME/.video-review"
if [ ! -x "$VENV/bin/python" ]; then
  echo "First run: setting things up. This takes a few minutes and only happens once."
  if ! python3 -m venv "$VENV"; then
    echo "Python 3 isn't set up yet. If macOS offers to install developer tools, click Install, then double-click this again."
    read -r -p "Press Return to close." _; exit 1
  fi
  "$VENV/bin/python" -m pip install --upgrade pip >/dev/null
  "$VENV/bin/python" -m pip install yt-dlp mlx-whisper imageio-ffmpeg || { echo "Setup failed. Copy this window and ask Claude what went wrong."; read -r -p "Press Return to close." _; exit 1; }
fi
# TikTok and Instagram change often, so keep the downloader current
"$VENV/bin/python" -m pip install -q --upgrade yt-dlp >/dev/null 2>&1
FF=$("$VENV/bin/python" -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')
ln -sf "$FF" "$VENV/bin/ffmpeg"
export PATH="$VENV/bin:$PATH"
"$VENV/bin/python" review_videos.py
read -r -p "Press Return to close." _
