import { ChangeEvent, useMemo, useState } from "react";
import type { InspectaReport } from "./types";

function formatScore(score?: number): string {
  if (typeof score !== "number") return "N/A";
  return `${score}/100`;
}

export default function App() {
  const [report, setReport] = useState(null as InspectaReport | null);
  const [error, setError] = useState("");

  const scoreEntries = useMemo(
    () => Object.entries(report?.scores ?? {}).sort(([a], [b]) => a.localeCompare(b)),
    [report]
  ) as Array<[string, number]>;

  const onFileSelected = async (event: ChangeEvent<HTMLInputElement>) => {
    setError("");
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const parsed = JSON.parse(text) as InspectaReport;
      setReport(parsed);
    } catch {
      setReport(null);
      setError("Invalid report.json file. Please select a valid inspecta JSON report.");
    }
  };

  return (
    <main className="container">
      <header className="card">
        <h1>inspecta report viewer</h1>
        <p>Load a local <code>report.json</code> file to inspect summary, scores, tests, and raw JSON.</p>
        <input type="file" accept=".json,application/json" onChange={onFileSelected} />
        {error ? <p className="error">{error}</p> : null}
      </header>

      {report ? (
        <>
          <section className="grid">
            <article className="card">
              <h2>Device</h2>
              <p><strong>Vendor:</strong> {report.device?.vendor ?? "Unknown"}</p>
              <p><strong>Model:</strong> {report.device?.model ?? "Unknown"}</p>
              <p><strong>Serial:</strong> {report.device?.serial ?? "N/A"}</p>
              <p><strong>BIOS:</strong> {report.device?.bios_version ?? "N/A"}</p>
            </article>

            <article className="card">
              <h2>Summary</h2>
              <p><strong>Score:</strong> {formatScore(report.summary?.overall_score)}</p>
              <p><strong>Grade:</strong> {report.summary?.grade ?? "N/A"}</p>
              <p><strong>Recommendation:</strong> {report.summary?.recommendation ?? "N/A"}</p>
              <p><strong>Mode:</strong> {report.mode ?? "N/A"}</p>
              <p><strong>Profile:</strong> {report.profile ?? "N/A"}</p>
            </article>
          </section>

          <section className="card">
            <h2>Component scores</h2>
            <table>
              <thead>
                <tr><th>Component</th><th>Score</th></tr>
              </thead>
              <tbody>
                {scoreEntries.map(([name, score]: [string, number]) => (
                  <tr key={name}>
                    <td>{name.split("_").join(" ")}</td>
                    <td>{formatScore(score)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="card">
            <h2>Tests</h2>
            <table>
              <thead>
                <tr><th>Name</th><th>Status</th><th>Detail</th><th>Error</th></tr>
              </thead>
              <tbody>
                {(report.tests ?? []).map(
                  (
                    test: { name?: string; status?: string; status_detail?: string; error?: string },
                    idx: number
                  ) => (
                  <tr key={`${test.name ?? "test"}-${idx}`}>
                    <td>{test.name ?? "unknown"}</td>
                    <td>{(test.status ?? "unknown").toUpperCase()}</td>
                    <td>{test.status_detail ?? ""}</td>
                    <td>{test.error ?? ""}</td>
                  </tr>
                  )
                )}
              </tbody>
            </table>
          </section>

          <section className="card">
            <h2>Raw JSON</h2>
            <pre>{JSON.stringify(report, null, 2)}</pre>
          </section>
        </>
      ) : null}
    </main>
  );
}
