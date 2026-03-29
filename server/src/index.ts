import cors from "cors";
import express from "express";
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import multer from "multer";

const app = express();
const port = Number(process.env.PORT ?? 8787);
const uploadToken = process.env.UPLOAD_TOKEN ?? "inspecta-dev-token";
const dataDir = process.env.DATA_DIR ?? path.resolve(process.cwd(), "data");
const reportsDir = path.join(dataDir, "reports");

fs.mkdirSync(reportsDir, { recursive: true });

app.use(cors());
app.use(express.json({ limit: "2mb" }));

function authMiddleware(
  req: express.Request,
  res: express.Response,
  next: express.NextFunction
) {
  const header = req.header("authorization") ?? "";
  const token = header.startsWith("Bearer ") ? header.slice(7) : "";
  if (!token || token !== uploadToken) {
    res.status(401).json({ error: "unauthorized" });
    return;
  }
  next();
}

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 25 * 1024 * 1024, files: 50 },
});

type StoredReport = {
  id: string;
  createdAt: string;
  metadata?: Record<string, unknown>;
  files: string[];
};

function getReportDir(id: string): string {
  return path.join(reportsDir, id);
}

app.get("/health", (_req, res) => {
  res.json({ ok: true, service: "inspecta-upload-api" });
});

app.post("/reports", authMiddleware, upload.any(), (req, res) => {
  const id = crypto.randomUUID();
  const reportDir = getReportDir(id);
  fs.mkdirSync(reportDir, { recursive: true });

  const files = (req.files as Express.Multer.File[] | undefined) ?? [];
  const storedFiles: string[] = [];

  for (const file of files) {
    const safeName = file.originalname.replace(/[^a-zA-Z0-9._-]/g, "_");
    const outPath = path.join(reportDir, safeName);
    fs.writeFileSync(outPath, file.buffer);
    storedFiles.push(safeName);
  }

  let metadata: Record<string, unknown> | undefined;
  const metadataField = req.body?.metadata;
  if (typeof metadataField === "string") {
    try {
      metadata = JSON.parse(metadataField) as Record<string, unknown>;
    } catch {
      metadata = { parse_error: "invalid metadata JSON" };
    }
  }

  const index: StoredReport = {
    id,
    createdAt: new Date().toISOString(),
    metadata,
    files: storedFiles,
  };

  fs.writeFileSync(
    path.join(reportDir, "index.json"),
    JSON.stringify(index, null, 2),
    "utf-8"
  );

  res.status(201).json({
    id,
    status: 201,
    reportUrl: `/reports/${id}`,
    pdfUrl: `/reports/${id}/pdf`,
    files: storedFiles,
  });
});

app.get("/reports/:id", authMiddleware, (req, res) => {
  const reportDir = getReportDir(req.params.id);
  const indexPath = path.join(reportDir, "index.json");

  if (!fs.existsSync(indexPath)) {
    res.status(404).json({ error: "report not found" });
    return;
  }

  const indexRaw = fs.readFileSync(indexPath, "utf-8");
  const index = JSON.parse(indexRaw) as StoredReport;
  res.json(index);
});

app.get("/reports/:id/pdf", authMiddleware, (req, res) => {
  const reportDir = getReportDir(req.params.id);
  const candidates = fs.existsSync(reportDir)
    ? fs.readdirSync(reportDir).filter((f) => f.toLowerCase().endsWith(".pdf"))
    : [];

  if (candidates.length === 0) {
    res.status(404).json({ error: "pdf not found" });
    return;
  }

  const pdfPath = path.join(reportDir, candidates[0]);
  res.sendFile(pdfPath);
});

app.listen(port, () => {
  // eslint-disable-next-line no-console
  console.log(`inspecta upload API listening on http://localhost:${port}`);
});
