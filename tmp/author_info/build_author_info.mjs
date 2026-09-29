import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const sourcePath = new URL("./Author_Information_Form.xlsx", import.meta.url).pathname;
const previewDir = new URL("./preview", import.meta.url).pathname;
const outputDir = new URL("../../outputs/euspn_camera_ready", import.meta.url).pathname;

const input = await FileBlob.load(sourcePath);
const workbook = await SpreadsheetFile.importXlsx(input);

const sheet = workbook.worksheets.getItem("MS Tracking Form");
sheet.getRange("A4:J4").values = [[
  37,
  "Continuous Behavioral Authentication for Mobile Devices Using an Adaptive LSTM-Based Intelligent Agent",
  null,
  "Madi Gali",
  "Vassiliy Serbin",
  "Gali.M@stud.satbayev.university",
  null,
  null,
  "Department of Cybersecurity, Institute of Automation and Information Technologies, Satbayev University, Almaty 050013, Kazakhstan",
  6,
]];
sheet.getRange("A4:J4").format = {
  verticalAlignment: "center",
  wrapText: true,
};
sheet.getRange("A4:J4").format.rowHeight = 112;

await fs.mkdir(previewDir, { recursive: true });
console.log((await workbook.inspect({
  kind: "workbook,sheet",
  include: "id,name",
  maxChars: 6000,
})).ndjson);
console.log(JSON.stringify({ values: sheet.getRange("A3:J4").values }, null, 2));
console.log((await workbook.inspect({
  kind: "match",
  sheetId: sheet.name,
  range: "A1:J4",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 50 },
  maxChars: 4000,
})).ndjson);

const preview = await workbook.render({
  sheetName: sheet.name,
  autoCrop: "all",
  scale: 1.5,
  format: "png",
});
await fs.writeFile(`${previewDir}/final_MS_Tracking_Form.png`, new Uint8Array(await preview.arrayBuffer()));

await fs.mkdir(outputDir, { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(`${outputDir}/EUSPN_37.xlsx`);
