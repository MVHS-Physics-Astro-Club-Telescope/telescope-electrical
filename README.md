# MV Telescope electrical

The KiCad project for the MV Astronomy autonomous telescope. It covers the Raspberry Pi HAT (the PCB) and the
off-board power wiring, in one project with one sheet file per owner.

**Latest schematic, every sheet:**
[mv-telescope-electrical.pdf](https://github.com/MVHS-Physics-Astro-Club-Telescope/telescope-electrical/releases/download/latest-schematic/mv-telescope-electrical.pdf)
(CI rebuilds it after every merge to main.)

## Who owns what

| Sheet | File | Owner | What goes on it |
|---|---|---|---|
| Root (sheet map) | `mv-telescope-hat.kicad_sch` | Eeshan | The three blocks and the wires between them |
| Pi header | `pi_header.kicad_sch` | Eeshan | J1 (40-pin header) and the pin map. Done, v1 |
| HAT signals | `hat_signals.kicad_sch` | Ibrahim | 74ACT244 buffer, driver / limit-switch / encoder connectors, pull-ups, caps |
| Power and drivers | `power.kicad_sch` | Eeshan for now, open to a new member | Battery, fuses, kill switch, PPBA, 24 V supply, DM542T drivers (off the PCB) |
| Project and PCB | `.kicad_pro`, `.kicad_pcb` | Eeshan | |

All of these live in `mv-telescope-hat/`. The pin map, with every pin and the reasons, is in
[`mv-telescope-hat/README.md`](mv-telescope-hat/README.md).

## How we stay out of each other's way

1. **One file per owner.** Only edit your own sheet. Two people never change the same file, so nothing collides.
2. **The root page is the contract.** Each wire on the root sheet map is an agreed connection between two sheets.
   Inside your sheet, those connections are the hierarchical labels already placed for you. Don't rename or delete
   them. If you need a new signal between sheets, ask Eeshan. He adds it on the root page and in both sheets.
3. **Power symbols are global.** +5V, +3V3 and GND join across every sheet without a wire. GND means the Pi's ground.
4. **Annotate only your sheet.** Use Tools > Annotate Schematic, scope "Current sheet only", numbering "First free
   after sheet number × 100". HAT signals parts get 300s (U301, R301, J301...) and power parts get 400s (F401...).
   So two sheets can never pick the same reference.
5. **The power sheet is excluded from the board.** Its block on the root page is marked "Exclude from board", so
   nothing drawn there ends up on the HAT PCB. This was tested on KiCad 10.0.7.
6. **Use KiCad 10.** These files are saved in KiCad 10 format, and KiCad 9 can't open them.

## Making a change (GitHub Desktop)

1. Install [KiCad 10](https://www.kicad.org/download/) and [GitHub Desktop](https://desktop.github.com/), then clone
   this repo.
2. Make a branch: Branch > New branch, named like `ibrahim/buffer`.
3. In KiCad, open `mv-telescope-hat/mv-telescope-hat.kicad_pro`, double-click your block, draw, and save.
   **Always go through the `.kicad_pro`.** If you open your `.kicad_sch` file on its own, KiCad treats that one sheet as
   a whole separate project: every hierarchical label errors with "cannot be connected to non-existent parent sheet",
   and Annotate numbers your parts from 1, so your J1 collides with the Pi header's J1. The check below fails both.
4. Run Inspect > Electrical Rules Checker and get to 0 errors. Warnings are fine while the sheet is unfinished.
5. In GitHub Desktop, look at the changed-files list. If anything besides your sheet changed and you didn't mean it
   to (KiCad sometimes rewrites the project file or a sheet you only looked at), right-click it > Discard changes.
6. Commit, then Publish branch, then Create Pull Request.
7. The `erc` check runs by itself in a minute or two. Click Details > Summary > `schematic` to download that PR's PDF
   and full ERC report. Eeshan reviews and merges.

`main` is protected. Every change goes through a pull request, the `erc` check must pass, and a code owner must
approve (see `.github/CODEOWNERS`).

## Seeing what a pull request changed

KiCad files are text, so a pull request's **Files changed** tab shows them like code. That's fine for a renamed part,
but you can't see a drawing that way. There are three better ways to look:

1. **The picture comment.** On every pull request, CI posts one comment with a picture of each sheet that changed.
   Red is only in the old version, blue is only in the new one, black is unchanged, and yellow marks every spot that
   changed. Click a picture to download it full size, or use the `before` and `after` links to download each version in colour.
   The comment updates itself after every new commit.
2. **The PDF.** The `erc` check's Details > Summary > `schematic` has the pull request's PDF of every sheet.
3. **In KiCad on your computer.** In GitHub Desktop, click Current branch > Pull requests and pick the pull request
   (or in a terminal, run `gh pr checkout <number>`). Then open `mv-telescope-hat/mv-telescope-hat.kicad_pro` as usual.
   Switch back to your own branch before you edit anything.

## The check

`.github/workflows/kicad.yml` runs KiCad 10's own ERC on the whole hierarchy in the official `kicad/kicad:10.0`
container:

- **Any ERC error fails the check.** If a sheet file won't load, its labels go missing and the root page shows
  "Sheet pin has no matching hierarchical label" errors, so a broken file fails too.
- **Warnings don't fail it.** They're placeholders: "Label connected to only one pin" (a signal whose other end isn't
  drawn yet) and "Unconnected wire endpoint" (the short wires on the labels waiting for parts). They clear as the
  sheets get drawn.
- **Every reference must be unique, and every sheet must be saved by this project.** kicad-cli's ERC skips KiCad's
  annotation check, so a second step exports the netlist and fails on a reference used twice (two J1s) or on a sheet
  whose parts were saved by some other project (the sign it was opened on its own).
- Every run uploads the PDF of every sheet and the full ERC report as the `schematic` artifact.
- On pull requests, two more jobs (`draw`, then `schematic-diff`) make the picture comment described above. They never
  block a merge. The pictures are stored on the `pr-previews` pre-release, and each pull request keeps only its
  newest set. A pull request from a fork gets no comment, because GitHub doesn't let CI write to it; use the PDF.

Questions go in #electrical on Slack.
