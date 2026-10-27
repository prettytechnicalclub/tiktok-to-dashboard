/*
  Collect links from a TikTok profile's "Liked" tab into links.txt.

  How to use (no login needed):
  1. In the TikTok app: Settings > Privacy > Liked videos > Everyone (you can switch it back after).
  2. On a computer, open a browser window where you are NOT logged in to TikTok
     (a private/incognito window works) and go to https://www.tiktok.com/@yourhandle
  3. Click the "Liked" tab.
  4. Open the browser console (Chrome: View > Developer > JavaScript Console),
     paste this whole file, press Enter.
  5. It scrolls until it has MAX links (or runs out), then downloads links.txt.
     Each line is "link | caption", ready for video-review/links.txt.

  Only use this on your own account. It reads what TikTok already shows to any visitor.
*/
(async () => {
  const MAX = 300;          // how many liked videos to collect
  const PAUSE_MS = 1500;    // wait between scrolls so the page can load more
  const seen = new Map();
  let still = 0;

  const grab = () => {
    for (const a of document.querySelectorAll('a[href*="/video/"]')) {
      const url = a.href.split('?')[0];
      if (seen.has(url)) continue;
      const caption = (a.querySelector('img')?.alt || '')
        .replace(/\s+created by .*$/i, '')   // TikTok appends "created by … with … original sound"
        .replace(/\s+/g, ' ')
        .trim()
        .slice(0, 140);
      seen.set(url, caption);
    }
  };

  while (seen.size < MAX && still < 4) {
    const before = seen.size;
    grab();
    window.scrollTo(0, document.body.scrollHeight);
    await new Promise(r => setTimeout(r, PAUSE_MS));
    still = seen.size === before ? still + 1 : 0;
    console.log(`Collected ${seen.size} links…`);
  }

  const lines = [...seen].slice(0, MAX).map(([url, cap]) => cap ? `${url} | ${cap}` : url);
  const blob = new Blob([lines.join('\n') + '\n'], {type: 'text/plain'});
  const link = Object.assign(document.createElement('a'), {href: URL.createObjectURL(blob), download: 'links.txt'});
  document.body.appendChild(link); link.click(); link.remove();
  console.log(`Done: ${lines.length} links saved to links.txt`);
})();
