# Auto-LLM Frontend

This frontend is the active UI for the trimmed Auto-LLM project.

## Development

```bash
conda activate aist
npm install
npm run dev
```

By default, the frontend uses the real backend client.
If needed, set `VITE_API_BASE_URL` to point at a running backend.

## Validation

```bash
bash ./scripts/check_frontend_release.sh
```
