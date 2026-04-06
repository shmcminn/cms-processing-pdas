# Pro Data Analysis Pipeline

This pipeline turns a finished Pro Data Analysis PDF into the CMS handoff files your team usually makes by hand.

## What it generates

- Canonical PDF copy named `YYYYMMDD-slug-lastname.pdf`
- Main JPEG named `YYYYMMDD-slug-lastname.jpg`
- Email JPEG named `EMAIL-YYYYMMDD-slug-lastname.jpg`
- PowerPoint working Illustrator file named `PPT-YYYYMMDD-slug-lastname.ai`
- Workflow state file named `PPT-YYYYMMDD-slug-lastname.workflow.json`

After the manual layout step and rerun:

- PowerPoint working PDF named `PPT-YYYYMMDD-slug-lastname.pdf`
- Final PowerPoint named `YYYYMMDD-slug-lastname.pptx`

## Run it

Run the pipeline on one PDF:

```bash
uv run pro-data-analysis test_cases/where-the-dhs-shutdown-hit-hardest.pdf
```

On the first run, the script creates the working `PPT-...ai` from the Illustrator template, fills slide 1, and places the original PDF content off-artboard with fonts forced to Arial.

Then:

1. Open `PPT-...ai`
2. Move the staged chart/content from off-artboard onto the slide artboards
3. Save the AI file
4. Rerun the same command on the original source PDF

The rerun is blocked until the working AI file has a newer save time. The workflow JSON also records any Adobe automation failure so you can see whether the first pass failed in Illustrator or the export failed in Acrobat.

## Install the Finder Quick Action

Run:

```bash
./scripts/install_quick_action.sh
```

That writes a Quick Action into `~/Library/Services` so you can right-click a PDF in Finder.
