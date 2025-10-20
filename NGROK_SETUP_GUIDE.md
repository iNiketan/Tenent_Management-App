# 🚀 Ngrok Setup Guide for Tenant Management App

This guide will help you access your Django app from anywhere using ngrok!

---

## 📥 Step 1: Download Ngrok

1. **Go to**: https://ngrok.com/download
2. **Download** the Windows version (ZIP file)
3. **Extract** `ngrok.exe` from the ZIP file
4. **Place** `ngrok.exe` in this project folder (`tenent_management-app`)

**OR** you can add ngrok to your PATH:
- Right-click "This PC" → Properties → Advanced System Settings
- Click "Environment Variables"
- Under "System Variables", find "Path" and click Edit
- Add the folder where you extracted ngrok.exe

---

## 🔑 Step 2: Sign Up for Ngrok (Optional but Recommended)

1. **Sign up** (free): https://dashboard.ngrok.com/signup
2. After signing up, you'll get an **Auth Token**
3. **Run this command** once (replace YOUR_TOKEN with your actual token):
   ```bash
   ngrok config add-authtoken YOUR_TOKEN
   ```

**Why sign up?**
- Free tier: More tunnels, longer sessions
- Without signup: 2-hour session limit, limited requests

---

## ▶️ Step 3: Start Your App with Ngrok

### **Option A: Use the Batch File (Easiest)**

1. **Double-click** `start_with_ngrok.bat`
2. Wait 5 seconds for Django to start
3. Ngrok will open and show you a URL like:
   ```
   Forwarding: https://abc123.ngrok-free.app → http://localhost:8000
   ```
4. **Copy the ngrok URL** (e.g., `https://abc123.ngrok-free.app`)
5. **Open it** in your browser or phone!

### **Option B: Manual Setup**

1. **Terminal 1** - Start Django:
   ```bash
   conda activate Ldjango
   python manage.py runserver 0.0.0.0:8000
   ```

2. **Terminal 2** - Start Ngrok:
   ```bash
   ngrok http 8000
   ```

---

## 📱 Step 4: Access from Your Phone

1. **Copy the ngrok URL** from the terminal (e.g., `https://abc123.ngrok-free.app`)
2. **Open your phone's browser**
3. **Paste the URL** and press Enter
4. **You're in!** 🎉

**Note**: The first time you visit, ngrok shows a warning page. Just click "Visit Site" to continue.

---

## 🌐 Step 5: Share with Others

- Share the ngrok URL with anyone
- They can access your app from anywhere in the world
- The URL changes each time you restart ngrok (unless you have a paid plan)

---

## 🛑 How to Stop

- **Press Ctrl+C** in the ngrok terminal to stop ngrok
- **Close** the Django terminal to stop Django
- **OR** just close both terminal windows

---

## 💡 Tips & Tricks

### **Keep the Same URL (Paid Feature)**
Ngrok paid plans offer reserved domains that don't change.
- **Basic Plan**: $8/month
- **Get it**: https://dashboard.ngrok.com/billing

### **Ngrok Alternative Commands**

**Custom subdomain** (requires paid plan):
```bash
ngrok http 8000 --subdomain=mytenantapp
```

**View requests in browser**:
Visit http://localhost:4040 while ngrok is running to see all HTTP requests!

### **Security Notes**

⚠️ **Important**:
- Your app is publicly accessible while ngrok is running
- Anyone with the URL can access it
- Use strong passwords for your admin account
- Don't leave it running unattended with sensitive data

---

## ❓ Troubleshooting

### **"ngrok is not recognized as a command"**
- Make sure `ngrok.exe` is in your project folder
- OR add ngrok to your PATH (see Step 1)

### **"Failed to listen on port 8000"**
- Another program is using port 8000
- Find and close it, or use a different port:
  ```bash
  python manage.py runserver 8001
  ngrok http 8001
  ```

### **"Invalid Host header"**
- This is already fixed in your Django settings!
- If you still see it, make sure DEBUG=True in your .env file

### **Ngrok shows "Session Expired"**
- Free tier has 2-hour sessions
- Sign up and add your auth token (see Step 2)
- OR just restart ngrok

### **Connection is slow**
- Ngrok adds some latency (100-300ms)
- This is normal for tunnel services
- For production, use proper hosting instead

---

## 🚀 Next Steps

Once you're satisfied with testing:

1. **For permanent hosting**: Consider Raspberry Pi or VPS
2. **Buy a domain**: Link it to your hosting
3. **Set up SSL**: Use Let's Encrypt (free)
4. **Harden security**: Disable DEBUG, use strong passwords

---

## 📞 Need Help?

If you run into any issues, check:
- https://ngrok.com/docs
- https://dashboard.ngrok.com/get-started/setup

**Enjoy your globally accessible tenant management app!** 🎉

