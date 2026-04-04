import fs from "fs";
import pptxgen from "pptxgenjs";

import textHelpers from "../assets/text.js";
import imageHelpers from "../assets/image.js";
import layoutHelpers from "../assets/layout.js";

const { autoFontSize } = textHelpers;
const { getImageDimensions } = imageHelpers;
const { warnIfSlideElementsOutOfBounds, warnIfSlideHasOverlaps } = layoutHelpers;

function addChrome(slide) {
  slide.addText([
    { text: "POLITICO", options: { color: "C32026", bold: true } },
    { text: "PRO", options: { color: "111111", bold: true } },
  ], {
    x: 4.35,
    y: 0.34,
    w: 1.8,
    h: 0.24,
    fontFace: "Arial",
    fontSize: 18,
    margin: 0,
    align: "center",
  });
  slide.addText("Analysis", {
    x: 4.45,
    y: 0.68,
    w: 1.6,
    h: 0.34,
    fontFace: "Arial Black",
    fontSize: 24,
    color: "111111",
    margin: 0,
    align: "center",
  });
  slide.addShape("line", {
    x: 0.98,
    y: 1.28,
    w: 8.98,
    h: 0,
    line: { color: "D9D9D9", pt: 1 },
  });
  slide.addShape("line", {
    x: 0.98,
    y: 7.28,
    w: 8.98,
    h: 0,
    line: { color: "E3E3E3", pt: 1 },
  });
  slide.addText("Data Analysis", {
    x: 1.0,
    y: 7.38,
    w: 1.6,
    h: 0.18,
    fontFace: "Arial",
    fontSize: 9.5,
    color: "B9C1CF",
    margin: 0,
  });
  slide.addText([
    { text: "POLITICO", options: { color: "C32026", bold: true } },
    { text: "PRO", options: { color: "111111", bold: true } },
  ], {
    x: 8.3,
    y: 7.32,
    w: 1.6,
    h: 0.24,
    fontFace: "Arial",
    fontSize: 16,
    margin: 0,
    align: "right",
  });
}

function addTitleSlide(pptx, payload) {
  const slide = pptx.addSlide();
  addChrome(slide);

  slide.addText(payload.title, autoFontSize(payload.title, "Arial Black", {
    x: 0.98,
    y: 1.72,
    w: 8.55,
    h: 1.45,
    fontSize: 30,
    minFontSize: 22,
    maxFontSize: 34,
    bold: true,
    color: "111111",
    margin: 0,
    valign: "top",
    breakLine: false,
    fit: "shrink",
  }));

  slide.addText(`${payload.byline} | ${payload.date}`, {
    x: 0.98,
    y: 3.34,
    w: 6.6,
    h: 0.26,
    fontFace: "Arial",
    fontSize: 11.5,
    bold: true,
    color: "4B4B4B",
    margin: 0,
  });

  slide.addText(payload.dek, autoFontSize(payload.dek, "Arial", {
    x: 0.98,
    y: 3.72,
    w: 8.65,
    h: 2.1,
    fontSize: 18,
    minFontSize: 13,
    maxFontSize: 20,
    color: "222222",
    margin: 0,
    valign: "top",
    fit: "shrink",
  }));

  if (payload.source) {
    slide.addText(`Source: ${payload.source}`, autoFontSize(`Source: ${payload.source}`, "Arial", {
      x: 0.98,
      y: 6.62,
      w: 8.5,
      h: 0.55,
      fontSize: 10,
      minFontSize: 8.5,
      maxFontSize: 10.5,
      color: "333333",
      margin: 0,
      valign: "top",
      fit: "shrink",
    }));
  }

  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

function addImageSlides(pptx, payload) {
  for (const slideSpec of payload.slide_specs) {
    const slide = pptx.addSlide();
    addChrome(slide);
    let imageTop = 1.24;
    if (slideSpec.title) {
      slide.addText(slideSpec.title, autoFontSize(slideSpec.title, "Arial Black", {
        x: 1.0,
        y: 1.18,
        w: 8.75,
        h: 0.42,
        fontSize: 18,
        minFontSize: 14,
        maxFontSize: 20,
        bold: true,
        color: "111111",
        margin: 0,
        valign: "top",
        fit: "shrink",
      }));
      imageTop = 1.82;
    }
    if (slideSpec.subtitle) {
      slide.addText(slideSpec.subtitle, autoFontSize(slideSpec.subtitle, "Arial", {
        x: 1.0,
        y: 1.68,
        w: 8.75,
        h: 0.24,
        fontSize: 10.5,
        minFontSize: 9.5,
        maxFontSize: 11.5,
        color: "444444",
        margin: 0,
        valign: "top",
        fit: "shrink",
      }));
      imageTop = 2.02;
    }
    const { aspectRatio } = getImageDimensions(slideSpec.image_path);
    const width = 9.0;
    const maxHeight = 7.12 - imageTop;
    const height = Math.min(maxHeight, width / aspectRatio);
    slide.addImage({
      path: slideSpec.image_path,
      x: 1.0,
      y: imageTop,
      w: width,
      h: height,
    });
    warnIfSlideHasOverlaps(slide, pptx);
    warnIfSlideElementsOutOfBounds(slide, pptx);
  }
}

function main() {
  const payloadPath = process.argv[2];
  if (!payloadPath) {
    throw new Error("Usage: node tools/build_pptx.mjs <payload.json>");
  }
  const payload = JSON.parse(fs.readFileSync(payloadPath, "utf8"));
  const pptx = new pptxgen();
  pptx.defineLayout({ name: "POLITICO_LETTER", width: 11, height: 8.5 });
  pptx.layout = "POLITICO_LETTER";
  pptx.author = "Codex";
  pptx.company = "POLITICO";
  pptx.subject = payload.title;
  pptx.title = payload.title;
  pptx.lang = "en-US";
  pptx.theme = {
    headFontFace: "Arial Black",
    bodyFontFace: "Arial",
    lang: "en-US",
  };

  addTitleSlide(pptx, payload);
  addImageSlides(pptx, payload);
  pptx.writeFile({ fileName: payload.output_path });
}

main();
