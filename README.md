# Pro Data Analysis Pipeline

This tool takes a finished Pro Data Analysis PDF and builds the handoff files your team usually makes by hand.

It is designed around a two-step PowerPoint workflow:

1. The first run creates the JPEG exports and a working Illustrator file.
2. A human lays out the chart content on the slide artboards in Illustrator.
3. The second run exports the finished PowerPoint PDF and `.pptx`.

## Requirements

- macOS
- `uv`
- Adobe Illustrator
- Adobe Acrobat

The PowerPoint step depends on Illustrator and Acrobat automation. If either app is showing a modal dialog, recovery window, missing-font prompt, or menu state that blocks scripting, the run can fail until that is cleared.

## Clone The Repo

Clone the repo and move into the project folder:

```bash
git clone <repo-url>
cd cms-processing
```

## Quick Action Install

Install the Finder Quick Action from the repo root:

```bash
zsh scripts/install_quick_action.sh
killall Finder
```

This creates:

- a debug runner script at `scripts/run_quick_action.sh`
- a Finder Quick Action at `~/Library/Services/Pro Data Analysis.workflow`
- a Quick Action registration file at `~/Library/Services/Pro Data Analysis.workflow/Contents/Info.plist`

After running the installer, open System Settings and search for `Quick Actions` or `Extensions`. Confirm `Pro Data Analysis` is enabled for Finder Quick Actions or Services. The exact settings label varies by macOS version.

### Reinstall Or Update The Quick Action

Reinstall after any of these changes:

- you moved the repo
- you pulled a newer version of this repo
- Finder shows an old error after the installer changed

```bash
zsh scripts/install_quick_action.sh
killall Finder
```

## Quick Action Use

After installation:

1. In Finder, right-click a PDF file.
2. Choose `Quick Actions`.
3. Choose `Pro Data Analysis`.

Use a real Finder file selection. Do not run it from a browser download row, Preview sidebar item, or another app's file list.

Behavior:

- On the first run, it creates the working Illustrator file and reveals it in Finder.
- After you finish the manual layout and save the AI, run the Quick Action again on the original PDF.
- On the second run, it exports the final PowerPoint files and reveals the finished output.

If the first run creates JPG, AI, and workflow JSON files but still shows a macOS alert, treat the generated files as the source of truth. If the AI file exists, open it, complete the manual layout, save it, and run the Quick Action again on the original PDF.

## Quick Action Troubleshooting

Most Quick Action problems are fixed by reinstalling from the current repo and restarting Finder:

```bash
zsh scripts/install_quick_action.sh
killall Finder
```

Then confirm `Pro Data Analysis` is enabled in System Settings under Quick Actions, Extensions, or Services.

### Quick Action Still Does Not Appear

Check these items in order:

1. Confirm the workflow exists.

```bash
ls -la "$HOME/Library/Services/Pro Data Analysis.workflow/Contents"
```

You should see both `document.wflow` and `Info.plist`.

2. Confirm the workflow files are valid.

```bash
plutil -lint "$HOME/Library/Services/Pro Data Analysis.workflow/Contents/document.wflow" \
  "$HOME/Library/Services/Pro Data Analysis.workflow/Contents/Info.plist"
```

Both files should report `OK`.

3. Make sure you are right-clicking a PDF file in Finder.

### Quick Action Shows A macOS Error

If macOS says the service is not configured correctly, cannot open `run_quick_action.sh`, or cannot read `PPT-...workflow.json`, the installed workflow is stale. Reinstall:

```bash
zsh scripts/install_quick_action.sh
killall Finder
```

If the first-run output files already exist, do not delete them. Open the generated `PPT-...ai`, finish the manual layout, save it, and run the Quick Action again on the original PDF.

## What The Tool Generates

On the first run:

- `YYYYMMDD-slug-lastname.pdf`
- `YYYYMMDD-slug-lastname.jpg`
- `EMAIL-YYYYMMDD-slug-lastname.jpg`
- `PPT-YYYYMMDD-slug-lastname.ai`
- `PPT-YYYYMMDD-slug-lastname.workflow.json`

If the PDF text does not include a date, the tool looks for a leading date in the original filename, such as `20260128-file-name.pdf` or `2026-01-28-file-name.pdf`. If neither the PDF text nor the filename has a date, the output filenames start with `undated` and the deck date field is filled with `DATE TK`.

On the second run, after the AI file has been edited and saved:

- `PPT-YYYYMMDD-slug-lastname.pdf`
- `YYYYMMDD-slug-lastname.pptx`

## How It Works

### First Run

Run the tool on a finished PDF:

```bash
uv run pro-data-analysis "/full/path/to/file.pdf"
```

Or write the outputs to a specific folder:

```bash
uv run pro-data-analysis "/full/path/to/file.pdf" --output-dir tmp/test-run
```

On that first run, the pipeline:

- reads the first page of the PDF
- extracts the title, byline, date, dek, note, and source
- creates the canonical output filename
- writes the main JPG and email JPG
- creates `PPT-...ai` from the Illustrator template
- fills slide 1 automatically
- places the source PDF content off-artboard in the AI file
- forces the staged source content fonts to Arial
- writes a workflow JSON file that records the current phase

### Manual Illustrator Step

Open the generated `PPT-...ai` and do the slide layout work:

1. Move the staged source content from off-artboard onto the slide artboards.
2. Adjust layout as needed.
3. Save the AI file.

Slide 1 is already filled in. The manual step is mainly for chart placement and slide composition.

### Second Run

Rerun the exact same command on the original PDF:

```bash
uv run pro-data-analysis "/full/path/to/file.pdf" --output-dir tmp/test-run
```

On the second run, the pipeline:

- checks that the AI file was saved after creation
- checks that the content slides actually changed from the untouched template
- exports `PPT-...pdf` from Illustrator
- converts that PDF to `.pptx` through Acrobat

If the AI file was only touched or resaved without real slide changes, the export is blocked.

## Workflow JSON

Each run writes a file named `PPT-YYYYMMDD-slug-lastname.workflow.json`.

This file records:

- the current phase
- source and output paths
- the AI modification time
- content-slide fingerprints used for the resume guard
- any automation error message from Illustrator or Acrobat

Typical phases:

- `awaiting_manual_layout`
- `exported`
- `failed_initial_build`
- `failed_export`

## Common Failure Cases

### Illustrator Or Acrobat Is Blocked

If you see an Adobe automation error:

- bring Illustrator or Acrobat to the front
- close any prompts, alerts, recovery windows, or open menus
- rerun the same command

### AI Was Saved But Not Actually Updated

If you see a message saying the content slides still match the untouched template, the tool detected that the slide artboards were not meaningfully changed yet.

Open the AI file, move content onto the slide artboards, save it again, and rerun.

### First Run Failed But JPGs Exist

The image exports happen before the Illustrator step. If Illustrator fails, you may still see the canonical PDF and JPG outputs even though the AI and workflow files were not finished.

Check the terminal error and rerun after clearing Illustrator.

## Testing

A basic local test looks like this:

```bash
mkdir -p tmp/test-run
uv run pro-data-analysis "test_cases/electricity-costs-set-to-rise-as-obbba-cuts-deter-clean-energy-investments.pdf" --output-dir tmp/test-run
```

Then:

1. Open `PPT-...ai`
2. Move staged content onto the slide artboards
3. Save the AI
4. Rerun the same command


## Notes

- The tool assumes the Illustrator template file is present in the repo root.
- The PowerPoint output is a V1 workflow. It avoids automatic chart slicing and instead uses Illustrator for the manual deck layout step.
