# Codex server bootstrap

Start both development servers from repository root:

```powershell
.\.codex\start-servers.ps1
```

Install/update dependencies first (optional):

```powershell
.\.codex\start-servers.ps1 -InstallDeps
```

Stop both servers:

```powershell
.\.codex\stop-servers.ps1
```

Environment loading:
- Backend: `backend/.env`, then `backend/.env.local` (override)
- Frontend: `frontend/.env`, then `frontend/.env.local` (override)

Logs and pid files are written to `.codex/run/`.
