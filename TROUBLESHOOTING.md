# Troubleshooting Guide for Rental Management System

## Common Issues and Solutions

### 1. Python Not Found Error

**Error:** `Python was not found; run without arguments to install from the Microsoft Store`

**Solutions:**
- **Option A:** Install Python from python.org
  - Download Python 3.11+ from https://python.org
  - During installation, check "Add Python to PATH"
  - Restart your terminal

- **Option B:** Use Python from Microsoft Store
  - Open Microsoft Store
  - Search for "Python 3.11"
  - Install and restart terminal

- **Option C:** Use py launcher
  - Try using `py` instead of `python`
  - Example: `py manage.py migrate`

### 2. Migration Issues

**Error:** `No migrations found` or migration errors

**Solution:** I've created the migration files manually. The migrations are now in `core/migrations/` folder.

### 3. Node.js Not Found

**Error:** `npm: command not found`

**Solution:**
- Install Node.js from https://nodejs.org
- Download LTS version (18.x or higher)
- Restart terminal after installation

### 4. Database Issues

**Error:** Database connection errors

**Solution:**
- For development, SQLite is used by default
- Make sure you have write permissions in the project directory
- The database file `db.sqlite3` will be created automatically

### 5. CSS Build Issues

**Error:** Tailwind CSS build fails

**Solution:**
- Make sure Node.js is installed
- Run `npm install` first
- Then run `npm run build-css-prod`

## Quick Setup Instructions

### Method 1: Automated Setup (Recommended)

**For Windows Command Prompt:**
```cmd
setup.bat
```

**For PowerShell:**
```powershell
.\setup.ps1
```

### Method 2: Manual Setup

1. **Install Python 3.11+**
2. **Install Node.js 18+**
3. **Run these commands:**
   ```cmd
   pip install -r requirements.txt
   npm install
   npm run build-css-prod
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py seed_demo
   python manage.py runserver
   ```

### Method 3: Using Make (if available)

```cmd
make setup
```

## Verification Steps

After setup, verify everything works:

1. **Start the server:**
   ```cmd
   python manage.py runserver
   ```

2. **Open browser:** http://localhost:8000

3. **Login with:**
   - Username: `admin`
   - Password: `admin123`

4. **Check features:**
   - Dashboard loads
   - Room map works
   - Settings page accessible
   - Can add tenants and leases

## Getting Help

If you still have issues:

1. **Check Python version:**
   ```cmd
   python --version
   ```

2. **Check Node.js version:**
   ```cmd
   node --version
   npm --version
   ```

3. **Check if all files are present:**
   - `manage.py`
   - `requirements.txt`
   - `package.json`
   - `core/migrations/` folder

4. **Try running individual commands:**
   ```cmd
   python manage.py check
   python manage.py migrate --dry-run
   ```

## Alternative: Use Docker (Advanced)

If you have Docker installed:

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN npm install && npm run build-css-prod

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

```cmd
docker build -t rental-manager .
docker run -p 8000:8000 rental-manager
```
