# Report JSON Schema (summary)

Top-level fields:
- report_version (string)
- generated_at (ISO8601)
- device { vendor, model, serial, bios }
- summary { overall_score, grade, issues_count, recommendation }
- scores { storage, battery, memory, cpu_thermal, gpu, network, security }
- tests { smart, memtest, cpu_benchmark, disk_benchmark, thermal_stress, battery }
- artifacts [ { type, path } ]
- raw_logs { filename: text }

A detailed JSON Schema file will be added in code (report-schema.json) during implementation.
