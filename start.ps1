# Inicia backend (FastAPI) y frontend (Vite) en ventanas separadas

$root = $PSScriptRoot

Write-Host "Iniciando backend en http://localhost:8000 ..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; py -3.11 -m uvicorn main:app --reload --port 8000"

Start-Sleep -Seconds 2

Write-Host "Iniciando frontend en http://localhost:5173 ..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm run dev"

Write-Host ""
Write-Host "Backend:  http://localhost:8000"
Write-Host "Frontend: http://localhost:5173"
Write-Host "API docs: http://localhost:8000/docs"
