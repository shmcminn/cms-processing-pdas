# Pro Data Analysis Pipeline

This pipeline turns a finished Pro Data Analysis PDF into the CMS handoff files your team usually makes by hand.

## What it generates

- Canonical PDF copy named `YYYYMMDD-slug-lastname.pdf`
- Main JPEG named `YYYYMMDD-slug-lastname.jpg`
- Email JPEG named `EMAIL-YYYYMMDD-slug-lastname.jpg`
- PowerPoint working PDF named `PPT-YYYYMMDD-slug-lastname.pdf`
- Illustrator-compatible working file named `PPT-YYYYMMDD-slug-lastname.ai`
- PowerPoint deck named `YYYYMMDD-slug-lastname.pptx`
- PowerPoint slide asset folder named `PPT-YYYYMMDD-slug-lastname-assets/`
- Slide segmentation manifest named `PPT-YYYYMMDD-slug-lastname.segments.json`

## Run it

Install JavaScript dependencies once:

```bash
npm install
```

Run the pipeline on one PDF:

```bash
uv run pro-data-analysis test_cases/where-the-dhs-shutdown-hit-hardest.pdf
```

The working PowerPoint PDF and Illustrator-compatible `.ai` copy are generated from the same slide payload as the `.pptx`, so they do not depend on Acrobat or Illustrator automation.

## Adjusting slide splits

If the automatic PowerPoint slide splits are close but not perfect, edit `PPT-...segments.json` and rerun the command. The pipeline reuses that file on the next run, and it keeps the cropped slide images in `PPT-...-assets/` so the deck is easier to tweak by hand.

## Install the Finder Quick Action

Run:

```bash
./scripts/install_quick_action.sh
```

That writes a Quick Action into `~/Library/Services` so you can right-click a PDF in Finder.
