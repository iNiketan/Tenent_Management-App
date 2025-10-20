# 🔒 GitHub Security Checklist for Rental Management App

This guide ensures your sensitive data stays protected when pushing to GitHub.

---

## ✅ What's Already Protected (in .gitignore)

### **Critical Files - NEVER COMMIT:**
- ✅ `.env` - Contains SECRET_KEY, database passwords, API keys
- ✅ `db.sqlite3` - Your actual database with tenant data
- ✅ `*.pdf` - Generated invoices with tenant information
- ✅ `ngrok.exe` - Ngrok executable
- ✅ `*.sqlite3`, `*.db` - Any database files
- ✅ `__pycache__/` - Python cache files
- ✅ `staticfiles/` - Collected static files
- ✅ `media/` - Uploaded files

### **Protected by .gitignore:**
- Environment files: `.env`, `.env.local`, `.env.production`
- Database files: `*.sqlite3`, `*.db`
- PDF invoices: `*.pdf`
- Excel/CSV data: `*.xlsx`, `*.xls`, `*.csv`
- Backup files: `*.backup`, `*.bak`
- Session data: `sessions/`
- Log files: `*.log`, `logs/`
- IDE files: `.vscode/`, `.idea/`
- Node modules: `node_modules/`
- Ngrok: `ngrok.exe`, `ngrok.yml`

---

## 🚨 IMMEDIATE ACTIONS REQUIRED

### **Step 1: Check What's Currently in Git**

Run this to see if sensitive files are tracked:
```bash
git ls-files | findstr /I ".env"
git ls-files | findstr /I ".sqlite3"
git ls-files | findstr /I ".pdf"
```

If any files show up, **they need to be removed!**

---

### **Step 2: Remove Sensitive Files from Git**

#### **Option A: Files Not Yet Committed**
```bash
git rm --cached .env
git rm --cached db.sqlite3
git rm --cached *.pdf
git add .gitignore
git commit -m "Remove sensitive files and update .gitignore"
```

#### **Option B: Files Already Pushed to GitHub**
**⚠️ WARNING: This rewrites Git history!**

Only do this if:
- You're the only one using the repo, OR
- The repo is private and you can coordinate with others

```bash
# Remove .env from all commits
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Remove database from all commits
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch db.sqlite3" \
  --prune-empty --tag-name-filter cat -- --all

# Force push
git push origin --force --all
```

**OR use the automated script:**
```bash
cleanup_git_sensitive.bat
```

---

## 🔐 Additional Security Measures

### **1. Change Your SECRET_KEY**

If you already pushed your `.env` or `settings.py` with a SECRET_KEY:

1. **Generate a new key:**
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

2. **Update `.env`:**
   ```
   SECRET_KEY=your-new-secret-key-here
   ```

3. **Never commit the real key!**

---

### **2. Use Environment Variables on GitHub**

If you deploy from GitHub, use **GitHub Secrets**:

1. Go to your repo → Settings → Secrets → Actions
2. Add secrets:
   - `SECRET_KEY`
   - `DATABASE_URL`
   - Any API keys

---

### **3. Make Repository Private (Recommended)**

For a tenant management app with sensitive data:

1. Go to your repo → Settings
2. Scroll to "Danger Zone"
3. Click "Change repository visibility"
4. Select "Private"

**Free GitHub accounts get unlimited private repos!**

---

## 📝 What's SAFE to Commit

These files are fine to push to GitHub:

✅ **Source Code:**
- `*.py` (Python files)
- `*.html` (Templates)
- `*.css`, `*.js` (Frontend)
- `requirements.txt`
- `manage.py`

✅ **Documentation:**
- `README.md`
- `*.md` (documentation)
- `Rental_Management_Free_Setup_Plan.docx` (public info)

✅ **Configuration Templates:**
- `env.example` (without real values!)
- `.gitignore`
- `requirements.txt`

✅ **Static Assets:**
- Images (logos, icons)
- CSS frameworks (Tailwind)
- JavaScript libraries

---

## 🎯 Before Each Git Push - Checklist

Before running `git push`, always check:

```bash
# 1. Check what you're about to commit
git status

# 2. Review the actual changes
git diff

# 3. Make sure no sensitive files are staged
git ls-files --stage | findstr /I ".env"

# 4. If all clear, push!
git push origin main
```

---

## 🚨 Emergency: I Already Pushed Sensitive Data!

### **If you pushed database, .env, or passwords:**

1. **Change all passwords IMMEDIATELY**
2. **Generate new SECRET_KEY**
3. **Remove from Git history** (see Step 2 above)
4. **Make repo private**
5. **Consider the data exposed** - if it contains real tenant data, you may need to:
   - Notify affected parties
   - Create new database
   - Reset all credentials

---

## 📦 Example .env (Safe to Share)

Create an `env.example` file that shows structure but no real values:

```bash
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here-change-this

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Allowed Hosts
ALLOWED_HOSTS=localhost,127.0.0.1

# Optional: External Services
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@example.com
EMAIL_PASSWORD=your-password-here
```

This helps others set up the project without exposing your real credentials!

---

## 🛡️ GitHub Security Features to Enable

1. **Dependabot Alerts**
   - Settings → Security → Dependabot alerts (Enable)
   - Gets alerts for vulnerable dependencies

2. **Secret Scanning** (Public repos only)
   - Automatically scans for exposed secrets
   - GitHub notifies you if secrets are found

3. **Code Scanning** (Optional)
   - Settings → Security → Code scanning
   - Finds security vulnerabilities in code

---

## ✅ Final Security Checklist

Before making your repo public or sharing:

- [ ] `.gitignore` is properly configured
- [ ] No `.env` files in Git
- [ ] No `db.sqlite3` in Git
- [ ] No PDF invoices in Git
- [ ] No sensitive data in commit history
- [ ] `SECRET_KEY` is not hardcoded in settings.py
- [ ] All passwords/keys are in environment variables
- [ ] `env.example` provided (without real values)
- [ ] README doesn't contain sensitive info
- [ ] Database is fresh/demo data only (if public)

---

## 📚 Good Practices Going Forward

1. **Always use `.env` for secrets** - Never hardcode
2. **Review before committing** - Use `git status` and `git diff`
3. **Keep repo private** - For production apps with real data
4. **Use demo data** - If repo needs to be public
5. **Regular security audits** - Check what's in Git periodically

---

## 🆘 Need Help?

If you've exposed sensitive data and need help:
1. Make repo private immediately
2. Change all passwords/keys
3. Use `git filter-branch` to remove from history
4. Contact GitHub support if needed

---

**Remember: It's easier to prevent exposure than to clean it up later!** 🔒

Stay safe and happy coding! 🚀

