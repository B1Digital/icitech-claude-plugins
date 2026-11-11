# Plan file

One JSON file per game, kept in the game repository (for example
`marketing/ad_creatives/plan.json`). All paths are relative to the directory the
script is run from, which should be the repository root. The plan holds no secrets.

## Fields

| Field | Required | Meaning |
|---|---|---|
| `game.name` | yes | Store name, shown on the end card |
| `game.slug` | no | Prefix for output file names |
| `game.tagline` | no | One short line under the name |
| `game.cta` | no | Default `PLAY FREE`. Must not contain "Download" or "Install" |
| `game.icon` | no | App icon, ideally 1024x1024 |
| `game.mascot_image` | no | Transparent PNG placed on the end card |
| `game.font` | no | Brand font file (otf/ttf) for the end card |
| `game.colors` | no | `bg_inner`, `bg_mid`, `bg_outer`, `title`, `stroke` (hex) |
| `out_dir` | yes | Where `work/`, `videos/` and `images/` are written |
| `refs` | yes | Name to path of real game images used as references |
| `style` | no | Appended to every image prompt |
| `video_style` | no | Appended to every video prompt |
| `negative` | no | Appended to every prompt; defaults to a no-text/no-UI/no-hands line |
| `shape_hints` | no | Per image shape (`land`, `sq`, `port`) composition sentence |
| `audio.music` | no | Game music; replaces the generated sound. Looped if short |
| `audio.music_volume` | no | Default 0.55 |
| `image_provider` | no | `fal` (default) or `codefast` for image ads |
| `frame_provider` | no | Provider for video frames, default `fal` |
| `fal_image_model` | no | Default `fal-ai/nano-banana-pro/edit` |
| `video_model` | no | Default `minimax/h3-max-turbo/image-to-video` |
| `video_resolution` | no | Default `768P`; upscaled to 1080p on assemble |
| `videos[]` | no | See below |
| `images[]` | no | See below |

### `videos[]`

| Field | Meaning |
|---|---|
| `id` | Short id, used in file names |
| `aspect` | `9:16`, `16:9` or `1:1` |
| `duration` | Seconds of generated footage, default 10 |
| `start.prompt`, `start.refs` | Start frame: scene description and reference names |
| `end.prompt`, `end.refs` | Optional end frame. The start frame is always passed as the first reference, so phrase it as an edit: "Edit image 1 into the final frame of the same scene..." |
| `motion` | What happens, with second ranges |
| `sfx[]` | `{file, at, volume}`: sound effects placed at `at` seconds |

### `images[]`

| Field | Meaning |
|---|---|
| `id` | Short id |
| `prompt`, `refs` | Scene description and reference names |
| `shapes` | Optional. Keys `land`, `sq`, `port`; each may set `y` (0-100), the vertical crop focus. Default: all three at 50 |

## Example

A fictional match game, to show the shape of a plan.

```json
{
  "game": {
    "name": "Gem Garden",
    "slug": "GemGarden",
    "tagline": "Match. Bloom. Relax.",
    "cta": "PLAY FREE",
    "icon": "ios/Runner/Assets.xcassets/AppIcon.appiconset/icon-1024.png",
    "mascot_image": "assets/mascot/bee_cheer.png",
    "font": "assets/fonts/Brand-Bold.otf",
    "colors": {"bg_inner": "#7be08a", "bg_mid": "#2fa84f", "bg_outer": "#156b33", "title": "#fff3a6", "stroke": "#0e4a22"}
  },
  "out_dir": "marketing/ad_creatives",
  "refs": {
    "board": "marketing/refs/gameplay_level12.png",
    "bee": "assets/mascot/bee_greet.png",
    "flower": "assets/objects/golden_flower.png"
  },
  "style": "Style: premium stylized 3D animated film, soft rounded shapes, glossy materials, warm light, shallow depth of field, saturated clean colors.",
  "video_style": "Stylized 3D animated film, smooth motion, no camera shake, no cuts, one continuous shot. Objects never bend, merge or change color. The board and background stay unchanged.",
  "shape_hints": {
    "land": "Wide composition: all important content sits in the central horizontal band; the top and bottom 20% are calm background.",
    "sq": "Square composition, subject centered.",
    "port": "Vertical composition, subject centered, calm background at the top."
  },
  "audio": {"music": "assets/audio/music_garden.wav"},
  "videos": [
    {
      "id": "v1",
      "aspect": "9:16",
      "duration": 10,
      "start": {
        "prompt": "Create a single vertical still frame. Image 1 is a screenshot of the game: use it as the reference for the board and gems. Image 2 is the mascot bee: keep its exact design. Scene: a sunny garden, a wooden board filling the lower two thirds with a 5x5 grid of gems; three red gems sit in a row except one that is one step away. The bee hovers above the board, looking at that gem.",
        "refs": ["board", "bee"]
      },
      "end": {
        "prompt": "Edit image 1 into the final frame of the same scene, same camera and style. Changes: the row of red gems is gone and a golden flower from image 2 blooms in its place; the bee cheers with both arms up.",
        "refs": ["flower"]
      },
      "motion": "0-3 s: the bee points at the stray red gem. 3-5 s: the gem slides one step into the row. 5-7 s: the three red gems flash and burst into sparkles. 7-10 s: a golden flower blooms where they were and the bee cheers.",
      "sfx": [
        {"file": "assets/audio/swap.wav", "at": 3.2},
        {"file": "assets/audio/match.wav", "at": 5.4},
        {"file": "assets/audio/bloom.wav", "at": 7.2, "volume": 0.9}
      ]
    }
  ],
  "images": [
    {
      "id": "one_move",
      "prompt": "Recreate this scene as a new composition: the garden board with one red gem a single step away from completing a row, the bee beside it with a puzzled, thinking face. It should feel like an unsolved puzzle one move from done.",
      "refs": ["board", "bee"],
      "shapes": {"land": {}, "sq": {}, "port": {"y": 70}}
    }
  ]
}
```

## Outputs

| Path | Content |
|---|---|
| `<out_dir>/work/<id>_start.png`, `_end.png` | Frames to review before rendering |
| `<out_dir>/work/<id>_raw.mp4`, `_sheet.jpg` | Generated footage and its contact sheet |
| `<out_dir>/videos/<slug>_<id>_<aspect>.mp4` | Final 1080p video with end card |
| `<out_dir>/images/<slug>_<shape>_<id>.jpg` | Final image ads |

`work/` is large and reproducible; keep it out of version control.
