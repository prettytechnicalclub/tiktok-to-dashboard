# TikTok to Dashboard

Part of [Pretty Technical](https://prettytechnicalclub.com). Turn the hundreds of videos you've liked into a plan: transcripts and screenshots of every video, on your own Mac, then Claude finds what the creators agree on and updates your dashboard.

Works with TikTok, Instagram, YouTube and X links. Pairs with [HQ](https://github.com/prettytechnicalclub/hq) and the [Wellness Dashboard](https://github.com/prettytechnicalclub/wellness-dashboard), but works with any notes app.

## How it works

```
1. Collect   scripts/collect-liked-links.js   your liked videos → links.txt
2. Review    video-review/Review Videos.command   each link → transcript + caption + screenshots
3. Apply     prompts/video-takeaways.md   Claude groups them, stars overlaps, proposes updates
```

### 1. Collect your likes (no login)

1. In TikTok: Settings → Privacy → Liked videos → Everyone (switch it back after).
2. In a private browser window, open `tiktok.com/@yourhandle` and click **Liked**.
3. Open the console (Chrome: View → Developer → JavaScript Console), paste `scripts/collect-liked-links.js`, press Enter.
4. It scrolls and downloads `links.txt`. Move it into `video-review/`.

Or skip this and paste links into `video-review/links.txt` yourself, one per line (`link | optional note`).

### 2. Review the videos

Needs a Mac with Apple silicon (M1 or newer) and Python 3.

1. Double-click `video-review/Review Videos.command`. If macOS blocks it: right-click → Open → Open.
2. The first run installs `yt-dlp`, `mlx-whisper` and ffmpeg into `~/.video-review` and downloads the speech model (about 1.6 GB). After that it's fast.
3. Results land in `video-review/reviews/`. Each video is deleted after it's transcribed. Run it again any time; it skips links it's done. `FRAMES=0` skips screenshots.

Everything runs on your computer. Nothing is uploaded.

### 3. Turn it into a plan

Give Claude the `reviews/` folder and paste `prompts/video-takeaways.md`. You get:

- everything grouped by theme (posture, skin, hair, business, AI tools…)
- ⭐ on any move, step or product that shows up in 3+ videos
- programs built from the starred moves, a daily version and a longer one
- a research list of every book, tool and person the videos mention
- flags on anything that looks unproven or needs a professional
- a numbered list of dashboard updates. Nothing changes until you say which ones.

## Be kind

Only collect your own likes, keep the reviews for yourself, and credit creators when you share what you learned. Nothing here is medical advice.

MIT licensed.
