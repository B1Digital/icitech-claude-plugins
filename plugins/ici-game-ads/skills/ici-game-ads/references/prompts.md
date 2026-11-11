# Prompt patterns

What worked and what failed when producing game ad creatives with an image-edit
model for frames and an image-to-video model for motion.

## The start + end frame technique

Image-to-video models drift when asked to invent an outcome. Give them both ends:

1. **Start frame**: generated from a real screenshot and the mascot art.
2. **End frame**: an *edit of the start frame* ("same camera, same composition;
   changes: ..."), with any reward object passed as an extra reference.
3. **Video**: start frame, end frame, and a motion prompt with second ranges.

This is what makes a reward object match the game's real art and guarantees the
board ends in the intended state. Use it for every video whose last second matters.

## Start frame prompt

Structure, in this order:

1. Format: "Create a single vertical 9:16 still frame."
2. Role of each reference: "Image 1 is a screenshot of the game: use it as the
   reference for the board, the pieces and the setting. Image 2 is the mascot: keep
   its exact design (list 3-5 identifying features)."
3. Setting, one sentence.
4. Board and pieces, with exact counts, colours and positions ("exactly four ...").
5. Camera: angle and how much of the frame the board fills.
6. Character: where it stands, pose, expression.

Keep the shared look in the plan's `style` field so every frame matches.

## Motion prompt

- One continuous shot. Ask for "no cuts, no camera shake" and at most a slow push-in.
- Beats with second ranges: "0-2 s: ... 2-5 s: ...". Three to five beats in 10 s.
- One object moves per beat. Simultaneous moves get merged or dropped.
- Name what must stay still: other pieces, board, background.
- End on the character's reaction; it gives the cut to the end card a natural beat.

## Known failures and fixes

| Symptom | Fix |
|---|---|
| Pieces stand upright or float above the board in a low-angle wide shot | State the camera looks steeply down (about 60 degrees) and that pieces "lie completely flat on the surface like bracelets dropped on a table; not standing, not leaning, not floating" |
| Arrows, score counters or labels copied from the screenshot | Add "no arrow markings, no user interface"; crop UI out of the reference first |
| Character's face changes in the last seconds | Use an end frame; keep the character's final pose simple (arms up, smile) |
| A piece dissolves in place where it should travel | Accept if the game's own effect is a dissolve; otherwise give that move its own beat and say which direction it slides |
| Gems or decorations at the frame edge are cut | Say "all four gems fully inside the frame" and how much of the frame the board fills |
| Invented inlays or extra objects on the board in the reward frame | Say the board is "completely empty" before the reward appears; regenerate rather than keep |
| Landscape image loses the subject when cropped to 1.91:1 | Use the `land` shape hint: content in the central band, calm top and bottom |
| Image endpoint ignores references and invents a different character | The provider did not receive the images. Use its edit endpoint, not text-to-image |
| Gateway timeout on high-quality images | The script retries, then drops to medium quality |
| Straight, grid-like pieces come out curvy or coiled | Say they are "made only of straight segments joined by sharp right-angle corners, like pipes laid on a square grid: no curves, no waves, no loops", and lower the piece count (four reads better than six) |
| Pieces morph or change colour during a chain of moves | Fewer pieces, one move per beat, and "keeping its shape" on every beat |
| A second copy of the character appears | Add "exactly one <character> in the image" |
| Seams or patterns appear on a plain board | Describe the surface: "a plain smooth white surface with no lines, seams or patterns" |

The image model does not obey these every time. Generate, look, and drop or redo the
ones that miss; expect to keep roughly two out of three.

## Concept library for puzzle games

| Concept | Opening | Why it works |
|---|---|---|
| Core mechanic | The first move happens within 2-3 s | Viewers know what the game is |
| Challenge | A wrong move bounces back, the character frowns, then the right move | Near-fail framing draws the viewer in |
| Payoff | The last piece clears, the board cracks open, the reward rises | Shows what progress looks like |
| Second world | Same mechanic in a different theme | Variety for the asset pool, shows depth |

For images, an unsolved board with a puzzled character beats a solved one.

## Costs to quote

Prices change; check the provider's page before quoting. As a rough guide from one
production run: about 0.03 USD per generated second at 768p for the video model, so
a 10 s clip is about 0.30 USD, plus two image generations per video for the frames.
A set of six videos and nine images stays in the low single-digit dollars, before
retries.
