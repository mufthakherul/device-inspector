# inspecta upload API (opt-in)

This is a minimal TypeScript/Express upload API scaffold for Sprint 5 roadmap tasks.

## Features

- `POST /reports` (Bearer token required)
- `GET /reports/:id` metadata endpoint
- `GET /reports/:id/pdf` serve uploaded PDF if present
- Local file storage in `server/data/reports/<id>/`

## Quick start

1. Install dependencies:
   - `npm install`
2. Start dev server:
   - `npm run dev`
3. Set token (recommended):
   - PowerShell: `$env:UPLOAD_TOKEN="your-token"`
   - Bash: `export UPLOAD_TOKEN="your-token"`

Health check:
- `GET /health`

Use with CLI:
- `inspecta run --mode quick --output ./out --upload http://localhost:8787 --token your-token`
