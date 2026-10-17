# Harshpreet Hand — making-of video

A 65-second Remotion video (1920×1080, 30 fps) about how the font was built.
Every visual is real pipeline output: the notebook pages, the ink separation,
the transcribed words, the letter samples and picks, the g being retraced, and
the finished font. The pen animations draw the font's own stroke centrelines.

The cost scene reads `src/data/session_stats.json`. That file is produced by
`pipeline/session_stats.py`, which totals the Claude Code session log and
prices it at Claude Opus 5.5 API rates.

```bash
npm i
npx remotion studio                    # preview and edit
npx remotion render HandwritingFont out/harshpreet-hand-making-of.mp4 --crf=18
# show your portfolio URL at the end:
npx remotion render HandwritingFont out/with-url.mp4 --props='{"portfolioUrl":"yourdomain.com"}'
```

Scenes live in `src/scenes/` (one file each) and can be opened individually in the Studio's "Scenes" folder.
