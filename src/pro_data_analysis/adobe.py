from __future__ import annotations

import fcntl
import json
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

from .models import Metadata

REPO_ROOT = Path(__file__).resolve().parents[2]
TMP_ROOT = REPO_ROOT / "tmp" / "automation"
TEMPLATE_PATH = REPO_ROOT / "052025-data-analysis-PPT-template.ait"
ADOBE_LOCK_PATH = TMP_ROOT / "adobe-automation.lock"
ADOBE_LOCK_TIMEOUT_SECONDS = 30
ILLUSTRATOR_TIMEOUT_SECONDS = 180
ACROBAT_TIMEOUT_SECONDS = 300


class AdobeAutomationError(RuntimeError):
    """Raised when Illustrator or Acrobat automation fails."""


def prepare_ppt_ai(metadata: Metadata, source_pdf: Path, output_ai: Path) -> None:
    output_ai.parent.mkdir(parents=True, exist_ok=True)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    payload = {
        "template_path": str(TEMPLATE_PATH.resolve()),
        "source_pdf": str(source_pdf.resolve()),
        "output_ai": str(output_ai.resolve()),
        "title": metadata.title,
        "byline": metadata.byline.upper(),
        "date": metadata.date_mmddyyyy,
        "dek": metadata.dek,
        "note": metadata.note,
        "source": metadata.source,
    }
    script = _prepare_script(payload)
    with _adobe_automation_lock():
        _run_illustrator_javascript(
            script,
            operation="prepare the working Illustrator deck",
            timeout_seconds=ILLUSTRATOR_TIMEOUT_SECONDS,
        )
        _wait_for_output(output_ai, operation="write the working Illustrator deck")


def export_ai_to_pdf_and_pptx(input_ai: Path, output_pdf: Path, output_pptx: Path) -> None:
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    illustrator_script = _export_pdf_script({"input_ai": str(input_ai.resolve()), "output_pdf": str(output_pdf.resolve())})
    with _adobe_automation_lock():
        _run_illustrator_javascript(
            illustrator_script,
            operation="export the Illustrator deck to PDF",
            timeout_seconds=ILLUSTRATOR_TIMEOUT_SECONDS,
        )
        _wait_for_output(output_pdf, operation="finish the Illustrator PDF export")

        if output_pptx.exists():
            output_pptx.unlink()
        acrobat_script = _export_pptx_script({"input_pdf": str(output_pdf.resolve()), "output_pptx": str(output_pptx.resolve())})
        _run_acrobat_javascript(
            acrobat_script,
            operation="convert the PDF deck to PowerPoint in Acrobat",
            timeout_seconds=ACROBAT_TIMEOUT_SECONDS,
        )
        _wait_for_output(output_pptx, operation="finish the Acrobat PowerPoint export", timeout_seconds=30)


@contextmanager
def _adobe_automation_lock():
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    with ADOBE_LOCK_PATH.open("w") as lock_file:
        deadline = time.monotonic() + ADOBE_LOCK_TIMEOUT_SECONDS
        while True:
            try:
                fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError as exc:
                if time.monotonic() >= deadline:
                    raise AdobeAutomationError(
                        "Another Pro Data Analysis Adobe automation run is already in progress. "
                        "Wait for it to finish, then rerun this command."
                    ) from exc
                time.sleep(0.5)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def _run_illustrator_javascript(script: str, operation: str, timeout_seconds: int) -> None:
    script_path = TMP_ROOT / "illustrator-current.jsx"
    script_path.write_text(script)
    applescript = f'''
set jsSource to do shell script "cat {script_path}"
with timeout of {timeout_seconds} seconds
  tell application "Adobe Illustrator"
    activate
    return do javascript jsSource
  end tell
end timeout
'''
    _run_applescript(
        applescript=applescript,
        app_name="Adobe Illustrator",
        operation=operation,
        timeout_seconds=timeout_seconds + 15,
    )


def _run_acrobat_javascript(script: str, operation: str, timeout_seconds: int) -> None:
    script_path = TMP_ROOT / "acrobat-current.js"
    script_path.write_text(script)
    applescript = f'''
set jsSource to do shell script "cat {script_path}"
with timeout of {timeout_seconds} seconds
  tell application "Adobe Acrobat"
    activate
    return do script jsSource
  end tell
end timeout
'''
    _run_applescript(
        applescript=applescript,
        app_name="Adobe Acrobat",
        operation=operation,
        timeout_seconds=timeout_seconds + 15,
    )


def _run_applescript(applescript: str, app_name: str, operation: str, timeout_seconds: int) -> None:
    script_lines = [line for line in applescript.splitlines() if line.strip()]
    command = ["osascript"]
    for line in script_lines:
        command.extend(["-e", line])
    try:
        subprocess.run(
            command,
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise AdobeAutomationError(
            f"{app_name} took too long to {operation}. "
            f"Check {app_name} for modal dialogs or stalled conversion windows, then rerun the command."
        ) from exc
    except subprocess.CalledProcessError as exc:
        details = " ".join(
            part.strip()
            for part in [exc.stdout or "", exc.stderr or ""]
            if part and part.strip()
        )
        if not details:
            details = f"{app_name} returned exit code {exc.returncode}."
        raise AdobeAutomationError(f"{app_name} could not {operation}. {details}") from exc


def _wait_for_output(output_path: Path, operation: str, timeout_seconds: int = 15) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if output_path.exists() and output_path.stat().st_size > 0:
            return
        time.sleep(0.5)
    raise AdobeAutomationError(
        f"Adobe finished running but did not {operation}. "
        f"Expected output file: {output_path}"
    )


def _prepare_script(payload: dict[str, str]) -> str:
    return f"""
var payload = {json.dumps(payload)};
function findFont() {{
  var candidates = ["ArialMT", "Arial"];
  for (var i = 0; i < candidates.length; i++) {{
    try {{
      return app.textFonts.getByName(candidates[i]);
    }} catch (e) {{}}
  }}
  throw new Error("Arial is not available in Illustrator.");
}}
function replaceFrameContents(doc, marker, replacement, fontSize) {{
  for (var i = 0; i < doc.textFrames.length; i++) {{
    var tf = doc.textFrames[i];
    if ((tf.contents || "").indexOf(marker) !== -1) {{
      tf.contents = replacement;
      if (fontSize) {{
        tf.textRange.characterAttributes.size = fontSize;
      }}
      return tf;
    }}
  }}
  return null;
}}
function fitPointTextFrame(tf, maxRight, minSize) {{
  if (!tf) return;
  while (tf.visibleBounds[2] > maxRight && tf.textRange.characterAttributes.size > minSize) {{
    tf.textRange.characterAttributes.size = tf.textRange.characterAttributes.size - 1;
  }}
}}
function fitAreaTextFrame(tf, maxRight, maxBottom, minSize) {{
  if (!tf) return;
  while ((tf.visibleBounds[2] > maxRight || tf.visibleBounds[3] < maxBottom) && tf.textRange.characterAttributes.size > minSize) {{
    tf.textRange.characterAttributes.size = tf.textRange.characterAttributes.size - 1;
  }}
}}
function moveFrameTop(tf, targetTop) {{
  if (!tf) return;
  tf.translate(0, targetTop - tf.geometricBounds[1]);
}}
function buildSourceText(note, source) {{
  var notePart = "";
  var sourcePart = "";
  if (note) {{
    var cleanedNote = note.replace(/\\s+/g, " ").replace(/\\s+$/, "");
    if (cleanedNote && !/[.!?]$/.test(cleanedNote)) {{
      cleanedNote = cleanedNote + ".";
    }}
    notePart = "Note: " + cleanedNote;
  }}
  if (source) {{
    sourcePart = "Source: " + source.replace(/\\s+/g, " ").replace(/^\\s+|\\s+$/g, "");
  }}
  if (notePart && sourcePart) {{
    return notePart + "\\r" + sourcePart;
  }}
  return notePart || sourcePart;
}}
function removePlaceholderFrames(doc) {{
  var markers = [
    "All headlines, subheads and graphics should be top left aligned to the 1-inch margin.",
    "BY YOUR NAME ALL CAPS | MM/DD/20YY",
    "4 PX",
    "Sentence case description Arial regular 14 pt",
    "Sentence case small subhed Arial Bold 16 pt",
    "16 pt Arial regular, 21 pt line height.",
    "Sentence case subhed Arial Bold 20 pt",
    "If you need a two-line headline",
    "18 pt Arial regular body copy, 24 pt line height."
  ];
  for (var i = doc.textFrames.length - 1; i >= 0; i--) {{
    var text = doc.textFrames[i].contents || "";
    for (var j = 0; j < markers.length; j++) {{
      if (text.indexOf(markers[j]) !== -1) {{
        doc.textFrames[i].remove();
        break;
      }}
    }}
  }}
}}
function applyArial(item, arial) {{
  if (!item) return;
  if (item.typename === "TextFrame") {{
    try {{
      item.textRange.characterAttributes.textFont = arial;
    }} catch (e) {{}}
  }}
  if (item.pageItems && item.pageItems.length) {{
    for (var i = 0; i < item.pageItems.length; i++) {{
      applyArial(item.pageItems[i], arial);
    }}
  }}
}}
var templateDoc = app.open(new File(payload.template_path));
var saveOptions = new IllustratorSaveOptions();
saveOptions.pdfCompatible = true;
saveOptions.embedICCProfile = false;
var headlineSize = payload.title.length > 110 ? 24 : (payload.title.length > 80 ? 26 : (payload.title.length > 60 ? 28 : 30));
var titleFrame = replaceFrameContents(templateDoc, "Single-line headline goes here 30 pt", payload.title, headlineSize);
var longTitleFrame = null;
if (payload.title.length > 60) {{
  longTitleFrame = replaceFrameContents(templateDoc, "If you need a two-line headline", payload.title, headlineSize);
  if (longTitleFrame && titleFrame) {{
    var titleBounds = titleFrame.geometricBounds;
    var longBounds = longTitleFrame.geometricBounds;
    longTitleFrame.translate(titleBounds[0] - longBounds[0], titleBounds[1] - longBounds[1]);
    titleFrame.remove();
    titleFrame = longTitleFrame;
  }}
}}
var dekFrame = replaceFrameContents(templateDoc, "18 pt Arial regular body copy. This is where you copy and paste your intro.", payload.dek, payload.dek.length > 420 ? 16 : 18);
var sourceText = buildSourceText(payload.note, payload.source);
var sourceFrame = replaceFrameContents(templateDoc, "Note: If needed.", sourceText, sourceText.length > 180 ? 9 : 10);
var bylineFrame = replaceFrameContents(templateDoc, "BY YOUR NAME ALL CAPS | MM/DD/20YY", "BY " + payload.byline + " | " + payload.date, 11.5);
var firstArtboardRight = templateDoc.artboards[0].artboardRect[2] - 72;
if (titleFrame && titleFrame.kind == TextType.POINTTEXT) {{
  fitPointTextFrame(titleFrame, firstArtboardRight, 22);
}} else {{
  fitAreaTextFrame(titleFrame, firstArtboardRight, -225, 22);
}}

if (titleFrame && bylineFrame) {{
  moveFrameTop(bylineFrame, titleFrame.visibleBounds[3] - 14);
}}
fitPointTextFrame(bylineFrame, firstArtboardRight, 10);

if (bylineFrame && dekFrame) {{
  moveFrameTop(dekFrame, bylineFrame.visibleBounds[3] - 18);
}}
if (dekFrame && sourceFrame) {{
  fitAreaTextFrame(dekFrame, firstArtboardRight, sourceFrame.geometricBounds[1] + 18, 14);
}}
removePlaceholderFrames(templateDoc);

var sourceDoc = app.open(new File(payload.source_pdf));
app.activeDocument = sourceDoc;
app.executeMenuCommand("selectall");
app.copy();
app.activeDocument = templateDoc;
app.paste();
app.executeMenuCommand("group");
var stagedGroup = templateDoc.selection[0];
stagedGroup.name = "SOURCE PDF CONTENT";
var stagedLayer = templateDoc.layers.add();
stagedLayer.name = "SOURCE PDF CONTENT";
stagedGroup.move(stagedLayer, ElementPlacement.PLACEATBEGINNING);

var rightMost = templateDoc.artboards[templateDoc.artboards.length - 1].artboardRect[2];
var topEdge = templateDoc.artboards[0].artboardRect[1];
var bounds = stagedGroup.visibleBounds;
stagedGroup.translate((rightMost + 144) - bounds[0], (topEdge - 72) - bounds[1]);

var arial = findFont();
applyArial(stagedGroup, arial);

sourceDoc.close(SaveOptions.DONOTSAVECHANGES);
templateDoc.saveAs(new File(payload.output_ai), saveOptions);
templateDoc.close(SaveOptions.DONOTSAVECHANGES);
"ok";
"""


def _export_pdf_script(payload: dict[str, str]) -> str:
    return f"""
var payload = {json.dumps(payload)};
var doc = app.open(new File(payload.input_ai));
var opts = new PDFSaveOptions();
try {{
  opts.artboardRange = "1-" + doc.artboards.length;
}} catch (e) {{}}
doc.saveAs(new File(payload.output_pdf), opts);
doc.close(SaveOptions.DONOTSAVECHANGES);
"ok";
"""


def _export_pptx_script(payload: dict[str, str]) -> str:
    return f"""
var payload = {json.dumps(payload)};
var doc = app.openDoc(payload.input_pdf);
doc.saveAs(payload.output_pptx, "com.adobe.acrobat.pptx");
doc.closeDoc(true);
"ok";
"""
