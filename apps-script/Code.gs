// =============================
// CONFIGURATION
// =============================

// Default template. The website sends the template it has saved; this is the fallback.
const TEMPLATE_PRESENTATION_ID = "1cTCMbZ-SCdSXUxcCqGF232v0jexcVUwDwxWmZIc9kIY";
const SHEET_TAB = "Students"; // tab the website writes to

// =============================
// MANUAL ENTRY POINT (unchanged way of working: run from the open Sheet)
// =============================

function generateIDCards() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const students = readStudents_(sheet, 0, Infinity);
  const presId = startRun_(TEMPLATE_PRESENTATION_ID);
  const errors = buildCards_(presId, TEMPLATE_PRESENTATION_ID, students);
  const out = finishRun_(presId, TEMPLATE_PRESENTATION_ID);
  Logger.log(out.slidesUrl);
  Logger.log(out.pdfUrl);
  if (errors.length) Logger.log(errors.join("\n"));
}

// =============================
// WEB APP ENTRY POINT (called by the website, in batches)
// =============================

function doPost(e) {
  try {
    const req = JSON.parse(e.postData.contents);
    const secret = PropertiesService.getScriptProperties().getProperty("API_SECRET");
    if (!secret || req.secret !== secret) return json_({ ok: false, error: "Unauthorized" });

    const templateId = req.templateId || TEMPLATE_PRESENTATION_ID;

    if (req.action === "start") {
      return json_({ ok: true, presentationId: startRun_(templateId) });
    }
    if (req.action === "batch") {
      const sheet = SpreadsheetApp.openById(req.sheetId).getSheetByName(SHEET_TAB);
      const students = readStudents_(sheet, req.from, req.to);
      const errors = buildCards_(req.presentationId, templateId, students);
      return json_({ ok: true, count: students.length, errors: errors });
    }
    if (req.action === "finish") {
      return json_(Object.assign({ ok: true }, finishRun_(req.presentationId, templateId)));
    }
    return json_({ ok: false, error: "Unknown action" });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

// =============================
// RUN STEPS (the original single function, split so it can run in batches)
// =============================

function readStudents_(sheet, from, to) {
  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  return data.slice(1 + from, 1 + Math.min(to, data.length - 1)).map(function (row) {
    const student = {};
    headers.forEach(function (header, index) { student[header] = row[index]; });
    return student;
  });
}

// Copy of the template; its original slides are removed in finishRun_.
function startRun_(templateId) {
  const stamp = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "dd-MM-yyyy HH:mm");
  return DriveApp.getFileById(templateId).makeCopy("Generated Hostel ID Cards " + stamp).getId();
}

function buildCards_(presId, templateId, students) {
  const newPresentation = SlidesApp.openById(presId);
  const templateSlides = SlidesApp.openById(templateId).getSlides();
  const frontTemplate = templateSlides[0];
  const backTemplate = templateSlides[1];
  const errors = [];

  students.forEach(function (student) {
    const label = student["Enrollment No."] + " " + student["Name"];

    // FRONT
    const front = frontTemplate.duplicate();
    try {
      replaceText(front, student);
      const photoErr = insertStudentPhoto(front, student["Student photo"]);
      if (photoErr) errors.push(label + ": photo - " + photoErr);
      const sigErr = insertStudentSignature(front, student["Student signature"]);
      if (sigErr) errors.push(label + ": signature - " + sigErr);
      newPresentation.appendSlide(front);
    } finally {
      front.remove(); // never leave stray duplicates in the template
    }

    // BACK
    const back = backTemplate.duplicate();
    try {
      replaceText(back, student);
      newPresentation.appendSlide(back);
    } finally {
      back.remove();
    }
  });

  newPresentation.saveAndClose();
  return errors;
}

// FIX 1: the copy still contains the template's own slides (with unfilled {{placeholders}}) - remove them.
// FIX 2: export a PDF so it can be downloaded from the website.
function finishRun_(presId, templateId) {
  const templateCount = SlidesApp.openById(templateId).getSlides().length;
  const pres = SlidesApp.openById(presId);
  const slides = pres.getSlides();
  if (slides.length > templateCount) {
    for (let i = templateCount - 1; i >= 0; i--) slides[i].remove();
  }
  pres.saveAndClose();

  const file = DriveApp.getFileById(presId);
  const pdf = DriveApp.createFile(file.getAs(MimeType.PDF)).setName(file.getName() + ".pdf");
  return { slidesUrl: file.getUrl(), pdfId: pdf.getId(), pdfUrl: pdf.getUrl() };
}

// =============================
// TEXT REPLACEMENT (original logic; values are converted to text so numbers/blank cells never break it)
// =============================

function txt_(v) {
  return (v === null || v === undefined) ? "" : String(v);
}

function replaceText(slide, student) {

  slide.replaceAllText("{{NAME}}", txt_(student["Name"]));
  slide.replaceAllText("{{D/O}}", txt_(student["D/O"]));
  slide.replaceAllText("{{ENROLLMENT NO.}}", txt_(student["Enrollment No."]));
  slide.replaceAllText("{{PROGRAM}}", txt_(student["Program"]));
  slide.replaceAllText("{{YEAR}}", txt_(student["Year"]));
  slide.replaceAllText("{{HOSTEL}}", txt_(student["Hostel"]));

  let dob = student["DOB"];
  if (dob instanceof Date) {
    dob = Utilities.formatDate(dob, Session.getScriptTimeZone(), "dd-MM-yyyy");
  }

  let validity = student["Validity"];
  if (validity instanceof Date) {
    validity = Utilities.formatDate(validity, Session.getScriptTimeZone(), "dd-MM-yyyy");
  }

  slide.replaceAllText("{{D.O.B.}}", txt_(dob));
  slide.replaceAllText("{{VALIDITY}}", txt_(validity));
  slide.replaceAllText("{{ADDRESS}}", txt_(student["Address"]));
  slide.replaceAllText("{{STUDENT PHONE}}", txt_(student["Student Phone"]));
  slide.replaceAllText("{{PARENT PHONE}}", txt_(student["Parent Phone"]));
}

// =============================
// PHOTO AND SIGNATURE (original logic; both functions now share one body and return
// null on success or a short reason, so the website can list the students with a problem)
// =============================

function insertStudentPhoto(slide, photoLink) {
  return insertImageAtPlaceholder_(slide, photoLink, "PHOTO");
}

function insertStudentSignature(slide, signatureLink) {
  return insertImageAtPlaceholder_(slide, signatureLink, "SIGNATURE");
}

function insertImageAtPlaceholder_(slide, link, placeholderText) {

  if (!link || link === "") return "link missing";

  try {
    // Extract Google Drive File ID
    const match = String(link).match(/[-\w]{25,}/);
    if (!match) return "invalid Drive link";

    const imageBlob = DriveApp.getFileById(match[0]).getBlob();
    const elements = slide.getPageElements();

    for (let i = 0; i < elements.length; i++) {
      const element = elements[i];
      if (element.getPageElementType() !== SlidesApp.PageElementType.SHAPE) continue;

      const text = element.asShape().getText().asString().trim();

      if (text === placeholderText) {
        const left = element.getLeft();
        const top = element.getTop();
        const width = element.getWidth();
        const height = element.getHeight();

        element.remove();
        slide.insertImage(imageBlob, left, top, width, height);
        return null;
      }
    }
    return "placeholder '" + placeholderText + "' not found on slide";

  } catch (err) {
    return String(err);
  }
}
