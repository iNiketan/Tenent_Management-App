Write-Host "Setting up Rental Management System..." -ForegroundColor Green
Write-Host ""

Write-Host "Step 1: Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to install Python dependencies" -ForegroundColor Red
    Write-Host "Please make sure Python is installed and pip is available" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Step 2: Installing Node.js dependencies..." -ForegroundColor Yellow
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to install Node.js dependencies" -ForegroundColor Red
    Write-Host "Please make sure Node.js is installed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Step 3: Building CSS..." -ForegroundColor Yellow
npm run build-css-prod
if ($LASTEXITCODE -ne 0) {
    Write-Host "Warning: Failed to build CSS, continuing anyway..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Step 4: Running database migrations..." -ForegroundColor Yellow
python manage.py migrate
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to run migrations" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Step 5: Creating superuser..." -ForegroundColor Yellow
Write-Host "Creating admin user with username 'admin' and password 'admin123'" -ForegroundColor Cyan
$createUserScript = @"
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
"@
echo $createUserScript | python manage.py shell

Write-Host ""
Write-Host "Step 6: Seeding demo data..." -ForegroundColor Yellow
python manage.py seed_demo
if ($LASTEXITCODE -ne 0) {
    Write-Host "Warning: Failed to seed demo data, continuing anyway..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "You can now start the development server with:" -ForegroundColor Cyan
Write-Host "  python manage.py runserver" -ForegroundColor White
Write-Host ""
Write-Host "Login credentials:" -ForegroundColor Cyan
Write-Host "  Username: admin" -ForegroundColor White
Write-Host "  Password: admin123" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"
