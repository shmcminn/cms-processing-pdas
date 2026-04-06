from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .models import Metadata

REPO_ROOT = Path(__file__).resolve().parents[2]
TMP_ROOT = REPO_ROOT / "tmp" / "automation"
TEMPLATE_PATH = REPO_ROOT / "052025-data-analysis-PPT-template.ait"


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
    _run_illustrator_javascript(script)


def export_ai_to_pdf_and_pptx(input_ai: Path, output_pdf: Path, output_pptx: Path) -> None:
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    illustrator_script = _export_pdf_script({"input_ai": str(input_ai.resolve()), "output_pdf": str(output_pdf.resolve())})
    _run_illustrator_javascript(illustrator_script)

    acrobat_script = _export_pptx_script({"input_pdf": str(output_pdf.resolve()), "output_pptx": str(output_pptx.resolve())})
    _run_acrobat_javascript(acrobat_script)


def _run_illustrator_javascript(script: str) -> None:
    script_path = TMP_ROOT / "illustrator-current.jsx"
    script_path.write_text(script)
    applescript = f'''
set jsSource to do shell script "cat {script_path}"
tell application "Adobe Illustrator"
  activate
  return do javascript jsSource
end tell
'''
    subprocess.run(
        ["osascript", "-e", applescript],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def _run_acrobat_javascript(script: str) -> None:
    script_path = TMP_ROOT / "acrobat-current.js"
    script_path.write_text(script)
    applescript = f'''
set jsSource to do shell script "cat {script_path}"
tell application "Adobe Acrobat"
  activate
  return do script jsSource
end tell
'''
    subprocess.run(
        ["osascript", "-e", applescript],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
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
  var parts = [];
  if (note) {{
    var cleanedNote = note.replace(/\\s+/g, " ").replace(/\\s+$/, "");
    if (cleanedNote && !/[.!?]$/.test(cleanedNote)) {{
      cleanedNote = cleanedNote + ".";
    }}
    parts.push("Note: " + cleanedNote);
  }}
  if (source) {{
    parts.push("Source: " + source.replace(/\\s+/g, " ").replace(/^\\s+|\\s+$/g, ""));
  }}
  return parts.join(" ");
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
templateDoc.saveAs(new File(payload.output_ai), saveOptions);
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
templateDoc.save();
templateDoc.close(SaveOptions.SAVECHANGES);
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
doc.close(SaveOptions.SAVECHANGES);
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
