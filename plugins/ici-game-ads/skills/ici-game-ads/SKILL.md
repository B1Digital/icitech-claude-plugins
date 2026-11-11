---
name: ici-game-ads
description: Produce Google App campaign ad creatives for a mobile game - cinematic 10 s videos (portrait, landscape, square) with an end card, and text-free image ads in the three Google sizes - from the game's own art, using AI image and image-to-video models. Use when the user wants video or image ads for a game's Google Ads / UAC / App campaign, says "reklam videosu", "oyun reklamı üret", "Google Ads için video lazım", "reklam görselleri", "ad creatives", "ad strength is low", or wants to repeat the ad-creative workflow for another game. Not for App Store / Play Store listing screenshots or preview videos (use the screenshot and app-preview skills), and not for campaign setup or bidding.
argument-hint: "[game repo path] [--videos N] [--images N] [--only videos|images]"
---

# ici-game-ads

Turns a game's real art into ad creatives for Google App campaigns:

- **Videos**: stylised cinematic scenes that show the real core mechanic, 10 s of
  generated footage plus a 2.5 s end card (icon, name, tagline, "PLAY FREE").
- **Images**: text-free key moments in 1200x628, 1200x1200 and 1200x1500.

`<skill>` below means the directory holding this file. The work is driven by one
script, `<skill>/scripts/gameads.py`, and one plan file per game.

Write chat output in the user's language. Prompts sent to the models are in English.

## Hard rules

- **Show only what the game really does.** A stylised 3D or painted look is fine. A
  mechanic, mode, character or reward that is not in the game is not: it breaks
  Google's misrepresentation policy and brings installs that churn.
- **Every generated image starts from real game assets** (screenshot, mascot, icon,
  key objects). The script refuses to generate without a reference.
- **No text, UI, phone frame or hands inside generated footage.** Models garble text
  and hands. Text belongs on the end card, rendered deterministically.
- **Image ads are text-free.** Google recommends images without overlaid text, asks
  that overlays stay under 20% of the image, and disapproves images with "Download"
  or "Install" superimposed.
- **Videos are at least 10 s.** That is the App campaign minimum; 10-30 s is the
  recommended range. The script warns below 10 s.
- **Keys never go into the repo, the plan, the chat or the logs.** They live in
  `~/.config/ici-game-ads/keys.env` (mode 600) or in the environment. Do not print
  that file. If a key is missing, ask the user to add it there themselves.
- **Look at every result before delivering it.** Read the contact sheet of each
  video and each image. Regenerate what is wrong; do not ship it with a caveat.
- **Generation costs money.** Say roughly what a run will cost before a batch larger
  than the plan the user already agreed to.

## Requirements

| Need | Notes |
|---|---|
| Python 3.9+ | Standard library only |
| ffmpeg, ffprobe | On PATH |
| Google Chrome or Chromium | Renders the end card; set `CHROME_PATH` if not found |
| `FAL_KEY` | fal.ai key: start/end frames and image-to-video |
| `CODEFAST_KEY` | Optional: image ads through a GPT Image gateway when `image_provider` is `codefast` |

Run `python3 <skill>/scripts/gameads.py check` first. It reports tools and whether
each key is set, without showing values.

Keys file format:

```
FAL_KEY=...
CODEFAST_KEY=...
```

## Workflow

### 1. Learn the game

From the game repository, find and look at:

- 2-4 real gameplay screenshots (store screenshots are fine; crop off caption bands),
- the mascot or main character art, the app icon, key reward objects,
- the brand font, music and sound effects if the repo has them,
- the store name, tagline and the one-sentence core mechanic.

Write the mechanic down as a sequence of things that visibly happen ("a gem slides
one step, three in a row flash and burst, a flower blooms where they were"). Every
prompt is built from this sequence.

If the campaign already exists, read its current assets (a Google Ads MCP or the
user's screenshot) so you know which formats are missing.

### 2. Write the plan

Create `marketing/ad_creatives/plan.json` in the game repository. Schema and a full
example: `<skill>/references/plan.md`. Prompt patterns that worked and failed:
`<skill>/references/prompts.md`.

Default set, which gives two videos per orientation:

| Video | Aspect | Concept |
|---|---|---|
| v1 | 9:16 | Core mechanic, step by step |
| v2 | 16:9 | Payoff: the reward moment |
| v3 | 1:1 | Challenge: a blocked move, then the right one |
| v4 | 9:16 | Payoff in a second world or theme |
| v5 | 16:9 | Challenge in the first world |
| v6 | 1:1 | Core mechanic in the second world |

Images: three concepts (challenge, payoff, second world), each in `land`, `sq` and
`port`. An unsolved-puzzle image with a puzzled character is the closest match to
what performs for puzzle games; a finished, tidy board is the weakest.

Show the user the concept table before generating. Start with one video if they
have not seen the style yet.

### 3. Generate

Run from the game repository root:

```
python3 <skill>/scripts/gameads.py frames   marketing/ad_creatives/plan.json [ids]
python3 <skill>/scripts/gameads.py render   marketing/ad_creatives/plan.json [ids]
python3 <skill>/scripts/gameads.py assemble marketing/ad_creatives/plan.json [ids]
python3 <skill>/scripts/gameads.py images   marketing/ad_creatives/plan.json [ids]
```

- `frames` makes a start frame per video and, when the plan has an `end` block, an
  end frame edited from the start frame. **Read both frames before `render`**: a
  bad start frame wastes the video generation.
- `render` runs image-to-video between the two frames and writes
  `work/<id>_sheet.jpg`. Read every sheet.
- `assemble` scales to 1080p, cross-fades into the end card and lays the game's own
  music and sound effects over the footage. Set each `sfx` time from the sheet
  (frames are 0.83 s apart).
- `images` generates each concept per shape and crops to the exact Google sizes.
  Check them with `gameads.py sheet <images dir>`.

Outputs land in `<out_dir>/videos` and `<out_dir>/images`; intermediates in
`<out_dir>/work`.

### 4. Review checklist

For each video sheet:

- Objects keep their shape, colour and count; nothing morphs or merges.
- Pieces lie the way they do in the game (flat on the board, not upright or floating).
- The character keeps its design through the last frames.
- The action reads in the first 2-3 seconds.
- No stray text, arrows or UI copied from the reference screenshot.

For each image: subject not cut by the crop, no text, no invented objects.

Fix by editing the prompt for that id and re-running only that id. Typical fixes are
in `references/prompts.md`.

### 5. Hand over

The script does not upload. Tell the user:

1. Google Ads > Tools > Shared library > Asset library > Upload. For videos choose
   the YouTube-created video ad storage channel; they stay unlisted.
2. In each campaign's ad: add the videos; replace weak images with the new ones
   (20 images and 20 videos per ad group at most).
3. Keep good existing key art; remove cropped store screenshots and images whose
   caption band covers more than a fifth of the frame.

If a read-capable Google Ads connector is available, verify afterwards that every
campaign has the videos and images, and report anything missing. Ad strength is a
completeness meter, not a performance metric; do not chase "Excellent" before the
first week of data.

Report: files produced, what was regenerated and why, known flaws, approximate cost,
and that audio could not be listened to (ask the user to watch once with sound).
