@echo off
echo Setting up Rental Management System with Anaconda...
echo.

echo Step 1: Installing Python dependencies...
C:\Users\snike\anaconda3\python.exe -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install Python dependencies
    pause
    exit /b 1
)

echo.
echo Step 2: Installing Node.js dependencies...
npm install
if %errorlevel% neq 0 (
    echo Error: Failed to install Node.js dependencies
    echo Please make sure Node.js is installed
    pause
    exit /b 1
)

echo.
echo Step 3: Building CSS...
npm run build-css-prod
if %errorlevel% neq 0 (
    echo Warning: Failed to build CSS, continuing anyway...
)

echo.
echo Step 4: Running database migrations...
C:\Users\snike\anaconda3\python.exe manage.py migrate
if %errorlevel% neq 0 (
    echo Error: Failed to run migrations
    pause
    exit /b 1
)

echo.
echo Step 5: Creating superuser...
echo Creating admin user with username 'admin' and password 'admin123'
echo from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin123') if not User.objects.filter(username='admin').exists() else None | C:\Users\snike\anaconda3\python.exe manage.py shell

echo.
echo Step 6: Seeding demo data...
C:\Users\snike\anaconda3\python.exe manage.py seed_demo
if %errorlevel% neq 0 (
    echo Warning: Failed to seed demo data, continuing anyway...
)

echo.
echo Setup complete!
echo.
echo You can now start the development server with:
echo   C:\Users\snike\anaconda3\python.exe manage.py runserver
echo.
echo Login credentials:
echo   Username: admin
echo   Password: admin123
echo.
pause
