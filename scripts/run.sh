
Write-Host 'Starting Le Shop Master Class...' -ForegroundColor Cyan
$jobs = @()
try {
    Write-Host '1. Starting Tailwind v4 Watcher...' -ForegroundColor Yellow
    # Fix: Passing arguments as a comma-separated list
    $bunProcess = Start-Process bun -ArgumentList 'run', 'dev' -PassThru -NoNewWindow
    $jobs += $bunProcess

    Write-Host '2. Starting Django 6.0 Server...' -ForegroundColor Green
    python manage.py runserver
}
finally {
    Write-Host 'Shutting down...' -ForegroundColor Red
    # Only try to stop if the process exists
    if ($jobs) {
        Stop-Process -Id $jobs.Id -ErrorAction SilentlyContinue
    }
}
