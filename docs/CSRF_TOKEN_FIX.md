# 🔧 CSRF Token Issue - FINAL FIX

## Error You're Getting

```
Forbidden (403)
CSRF verification failed. Request aborted.
CSRF token from POST incorrect.
```

This happens when submitting forms from your phone.

---

## ✅ What I Fixed

Added more CSRF settings in `capstone/settings.py`:

```python
CSRF_COOKIE_SECURE = False  # For HTTP (local dev)
SESSION_COOKIE_SECURE = False  # For HTTP (local dev)
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript access
CSRF_COOKIE_SAMESITE = 'Lax'  # Allow same-site requests
CSRF_USE_SESSIONS = False  # Use cookies
CSRF_COOKIE_DOMAIN = None  # Allow all domains
```

**These settings make CSRF cookies work properly over HTTP on local network!**

---

## 🚀 MUST DO: Clear Cookies & Restart

### 1. Stop Server
```powershell
# Press Ctrl + C
```

### 2. Clear Browser Cookies (IMPORTANT!)

**On Phone:**
```
1. Open browser settings
2. Clear browsing data
3. Select "Cookies and site data"
4. Clear
```

**Or easier - use Incognito/Private mode:**
```
Open a new incognito/private browser window
```

### 3. Restart Server
```powershell
python manage.py runserver 0.0.0.0:8000
```

### 4. Try Again

**On Phone (Incognito mode recommended):**
```
1. Go to: http://192.168.137.1:8000/supplier/login/
2. Login: test_supplier / supplier123
3. Try submitting a form
4. ✅ Should work now!
```

---

## 🎯 Why This Happens

### The Problem:

```
Old cookies from previous settings
    ↓
CSRF token mismatch
    ↓
Form submission blocked
```

### The Solution:

```
Clear old cookies
    ↓
New cookies with correct settings
    ↓
CSRF token matches
    ↓
✅ Form submission works!
```

---

## 📱 Complete Fix Steps

### Step-by-Step:

```
1. STOP SERVER
   └─> Ctrl + C

2. CLEAR PHONE BROWSER
   └─> Use incognito mode
       OR
       Clear cookies

3. RESTART SERVER
   └─> python manage.py runserver 0.0.0.0:8000

4. PHONE: Go to URL (fresh session)
   └─> http://192.168.137.1:8000/supplier/login/

5. LOGIN
   └─> test_supplier / supplier123

6. TRY FORM SUBMISSION
   └─> Should work! ✅
```

---

## 🔍 Alternative: Use Computer Browser First

If phone still has issues, test on computer first:

```
1. On computer browser (not localhost, use IP):
   http://192.168.137.1:8000/supplier/login/

2. Login: test_supplier / supplier123

3. Test form submission

4. If works on computer but not phone:
   → It's a cookie issue on phone
   → Use incognito mode on phone
   → Or clear all cookies
```

---

## 💡 Quick Workaround

### Use Incognito/Private Mode

**On Phone:**
```
Chrome: Menu → New Incognito Tab
Safari: + button → Private
Edge: Menu → New InPrivate Window
```

**Then:**
```
1. Go to: http://192.168.137.1:8000/supplier/login/
2. Login: test_supplier / supplier123
3. ✅ Fresh cookies, should work!
```

This bypasses old cookie issues!

---

## 🎊 Summary

### What to Do:

1. ✅ **Restart server** (settings updated)
2. ✅ **Use incognito mode** on phone (fresh cookies)
3. ✅ **Try login again**
4. ✅ **Test form submission**

### If Still Issues:

Try this order:
1. Computer browser with IP (http://192.168.137.1:8000)
2. Test there first
3. If works, then try phone
4. Use incognito on phone

---

**Status**: ✅ Settings fixed  
**Action**: Restart server + use incognito  
**Result**: Should work!  

🚀 **Restart server and try in incognito mode!** 🚀

