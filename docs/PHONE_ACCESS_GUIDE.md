# 📱 How to Access System from Your Phone

## Complete Step-by-Step Guide

---

## 🎉 Your Test Supplier Account

```
╔═══════════════════════════════════════════════╗
║     TEST SUPPLIER CREDENTIALS                 ║
╠═══════════════════════════════════════════════╣
║                                               ║
║  Company:  Test Supplier Co.                  ║
║                                               ║
║  Username: test_supplier                      ║
║  Password: supplier123                        ║
║                                               ║
║  Login at: /supplier/login/                   ║
║                                               ║
╚═══════════════════════════════════════════════╝
```

**This account is ready to use RIGHT NOW!**

---

## 📱 Access from Your Phone - 3 Steps

### STEP 1: Get Your Computer's IP Address

#### On Windows (Your System):

**Method 1: Quick Command**
```powershell
# Open PowerShell or Command Prompt
ipconfig

# Look for "IPv4 Address" under your active network
# Example output:
#   IPv4 Address. . . . . . . . : 192.168.1.100
#                                  ↑ This is your IP
```

**Method 2: Settings**
```
1. Open Settings
2. Network & Internet
3. Wi-Fi (if using Wi-Fi) or Ethernet
4. Click your network name
5. Look for "IPv4 address"
```

**Common IP formats:**
- `192.168.1.xxx` (home networks)
- `192.168.0.xxx` (some routers)
- `10.0.0.xxx` (some networks)

**Write down your IP!** Example: `192.168.1.100`

---

### STEP 2: Run Server on Network

#### Stop current server (if running):
```powershell
# Press Ctrl + C to stop
```

#### Run server accessible from network:
```powershell
python manage.py runserver 0.0.0.0:8000
```

**What this does:**
- `0.0.0.0` = Listen on ALL network interfaces
- `:8000` = Port number
- Makes server accessible from your phone!

**You should see:**
```
Starting development server at http://0.0.0.0:8000/
Quit the server with CTRL-BREAK.
```

**✅ Server is now accessible from your phone!**

---

### STEP 3: Access from Your Phone

#### Requirements:
- ✅ Phone on **same Wi-Fi network** as computer
- ✅ Server running (from Step 2)
- ✅ You know your computer's IP (from Step 1)

#### On Your Phone:

```
1. Open browser (Chrome, Safari, etc.)

2. Type in address bar:
   http://YOUR-IP:8000/supplier/login/
   
   Example if IP is 192.168.1.100:
   http://192.168.1.100:8000/supplier/login/

3. You should see the purple Supplier Login page!

4. Login with:
   Username: test_supplier
   Password: supplier123

5. ✅ You're in the Supplier Portal!
```

---

## 🎯 Complete Example

### Full Workflow

```
STEP 1: Get IP Address (on your computer)
──────────────────────────────────────────
Open PowerShell:
> ipconfig

Output:
   IPv4 Address. . . : 192.168.1.100
                        ↑ Your IP

STEP 2: Run Server (on your computer)
──────────────────────────────────────────
> python manage.py runserver 0.0.0.0:8000

Output:
   Starting development server at http://0.0.0.0:8000/
   ✅ Server running!

STEP 3: Access from Phone
──────────────────────────────────────────
Phone browser:
http://192.168.1.100:8000/supplier/login/
        ↑ Your IP

Login:
├─ Username: test_supplier
└─ Password: supplier123

✅ Supplier portal opens on phone!

STEP 4: Test Camera Scanning
──────────────────────────────────────────
On phone:
1. Create a test purchase order (on computer)
2. On phone, navigate to orders
3. Approve the order
4. Mark as shipped
5. On computer, go to Scan & Receive
6. Click [📷 Scan] button
7. Point computer camera at phone screen showing QR
   (Or vice versa - phone camera scanning printed QR)

✅ Complete mobile workflow!
```

---

## 🔧 Troubleshooting

### Issue: Can't find IP address

**Solution**:
```powershell
# Try this command:
ipconfig | findstr IPv4

# Shows only IPv4 addresses
# Look for the one starting with 192.168
```

### Issue: Phone can't connect

**Check**:
1. ✅ Phone on **same Wi-Fi** as computer?
2. ✅ Server running with `0.0.0.0:8000`?
3. ✅ Using correct IP address?
4. ✅ Firewall not blocking port 8000?

**Try**:
- Disable Windows Firewall temporarily
- Make sure both devices on same network
- Try different port: `python manage.py runserver 0.0.0.0:8080`

### Issue: Firewall blocking connection

**Windows Firewall Rule**:
```powershell
# Run as Administrator:
netsh advfirewall firewall add rule name="Django Dev Server" dir=in action=allow protocol=TCP localport=8000
```

Or temporarily disable firewall for testing.

---

## 📱 URLs to Access from Phone

### Using Your IP (Example: 192.168.1.100)

```
Replace 192.168.1.100 with YOUR actual IP:

Supplier Login:
http://192.168.1.100:8000/supplier/login/

Supplier Dashboard:
http://192.168.1.100:8000/supplier/dashboard/

Staff Login:
http://192.168.1.100:8000/login/

Admin Panel:
http://192.168.1.100:8000/admin/

Purchase Orders:
http://192.168.1.100:8000/purchase-orders/

Scan & Receive:
http://192.168.1.100:8000/purchase-orders/scan/receive/
```

---

## 🎯 Testing Camera Scanning on Phone

### Best Method:

1. **Create PO on computer**
2. **Print QR code or display on screen**
3. **Open Scan & Receive on phone**
4. **Click [📷 Scan] button on phone**
5. **Phone camera opens**
6. **Point at QR code**
7. **Auto-detects and receives!**

### Why Phone is Great for Scanning:

✅ Built-in camera (front & back)  
✅ Mobile and portable  
✅ Can walk around warehouse  
✅ Perfect for receiving deliveries  
✅ Camera quality usually good  

---

## 🖥️ Computer Commands

### Quick Commands to Copy & Paste

```powershell
# 1. Find your IP address
ipconfig | findstr IPv4

# 2. Run server on network
python manage.py runserver 0.0.0.0:8000

# 3. Create test supplier (already done!)
python create_test_supplier.py

# 4. Stop server
# Press Ctrl + C
```

---

## 📋 Complete Testing Checklist

### From Computer

```
[ ] Get computer's IP address
[ ] Run server: python manage.py runserver 0.0.0.0:8000
[ ] Login as admin: http://localhost:8000/login/
[ ] Create purchase order
[ ] View order detail
[ ] Note the QR code
```

### From Phone

```
[ ] Connect phone to same Wi-Fi
[ ] Open browser on phone
[ ] Go to: http://YOUR-IP:8000/supplier/login/
[ ] Login: test_supplier / supplier123
[ ] See supplier dashboard
[ ] View purchase orders
[ ] Click on pending order
[ ] Approve with pricing
[ ] Mark as shipped
[ ] Go to Scan & Receive page
[ ] Click [📷 Scan] button
[ ] Camera opens on phone
[ ] Point at QR code
[ ] QR detected automatically
[ ] Order received!
```

---

## 🌐 Network Setup

### Requirements

```
Computer:
├─ Connected to Wi-Fi/Network
├─ Django server running on 0.0.0.0:8000
└─ Firewall allows port 8000

Phone:
├─ Connected to SAME Wi-Fi network
├─ Browser installed (Chrome, Safari)
└─ Camera permission granted
```

### Network Diagram

```
         Your Home Wi-Fi Network
┌─────────────────────────────────────┐
│                                     │
│  🖥️  Computer                       │
│  IP: 192.168.1.100                  │
│  Running: Django Server :8000       │
│                                     │
│  📱 Your Phone                      │
│  IP: 192.168.1.150                  │
│  Accessing: http://192.168.1.100:8000/│
│                                     │
└─────────────────────────────────────┘
        Both on same network!
```

---

## 🎓 Step-by-Step Visual Guide

### On Your Computer

```
1. Open PowerShell
   ┌──────────────────────────────────┐
   │ PS C:\...\bitmngmnt>             │
   └──────────────────────────────────┘

2. Get IP Address
   ┌──────────────────────────────────┐
   │ PS> ipconfig | findstr IPv4      │
   │                                  │
   │ IPv4 Address: 192.168.1.100      │
   │               ↑ Write this down! │
   └──────────────────────────────────┘

3. Run Server
   ┌──────────────────────────────────┐
   │ PS> python manage.py runserver   │
   │     0.0.0.0:8000                 │
   │                                  │
   │ Starting server at               │
   │ http://0.0.0.0:8000/             │
   │ ✅ Server running!               │
   └──────────────────────────────────┘
```

### On Your Phone

```
1. Open Browser
   ┌──────────────────────────────────┐
   │  📱 Chrome / Safari              │
   └──────────────────────────────────┘

2. Enter URL (using your IP)
   ┌──────────────────────────────────┐
   │ http://192.168.1.100:8000/       │
   │ supplier/login/                  │
   │               ↑ Your IP here     │
   └──────────────────────────────────┘

3. Supplier Login Page Loads
   ┌──────────────────────────────────┐
   │  🚚 Supplier Portal              │
   │  Username: test_supplier         │
   │  Password: supplier123           │
   │  [Login]                         │
   └──────────────────────────────────┘

4. Dashboard Opens
   ┌──────────────────────────────────┐
   │  Welcome, Test Supplier Co.!     │
   │  📊 Statistics...                │
   │  📋 Recent Orders...             │
   └──────────────────────────────────┘

✅ You're in!
```

---

## 🎥 Testing Camera Feature

### Best Way to Test

```
1. On Computer:
   ├─ Login as admin
   ├─ Create purchase order
   ├─ Open order detail
   └─ Keep QR code displayed on screen

2. On Phone:
   ├─ Login as supplier
   ├─ Approve the order with pricing
   └─> QR code now visible

3. Back to Computer:
   ├─ Go to Scan & Receive
   ├─ Click [📷 Scan] button
   ├─ Point camera at phone screen
   └─> Camera detects QR code!
       └─> Auto-receives order!

Or reverse:
- Print QR code from computer
- Use phone camera to scan
```

---

## 🚀 Quick Start Commands

### Copy & Paste These

```powershell
# Get your IP address
ipconfig | findstr IPv4

# Run server accessible from phone
python manage.py runserver 0.0.0.0:8000

# If you need to stop and restart
# Press Ctrl + C, then run above command again
```

---

## 📞 What's Your IP?

### Quick IP Finder

Run this in PowerShell:
```powershell
ipconfig | findstr IPv4
```

Look for:
```
IPv4 Address. . . . . . . . : 192.168.1.100
                                ↑ This is it!
```

Common patterns:
- `192.168.1.xxx` (most common)
- `192.168.0.xxx` (common)
- `10.0.0.xxx` (some networks)
- `172.16.x.xxx` (some networks)

---

## 🔐 Security Notes

### For Testing Only

⚠️ **This setup is for LOCAL TESTING only**

**Safe for:**
- Testing on your home network
- Development purposes
- Phone testing
- Demo purposes

**NOT for:**
- ❌ Production use
- ❌ Public internet
- ❌ Untrusted networks
- ❌ Long-term deployment

**For production:**
- Use proper hosting (Heroku, AWS, etc.)
- Enable HTTPS
- Use production settings
- Proper firewall rules

---

## 🎊 Complete Test Scenario

### End-to-End Test on Phone

```
1. COMPUTER: Run Server
   PS> python manage.py runserver 0.0.0.0:8000

2. COMPUTER: Get IP (example: 192.168.1.100)
   PS> ipconfig | findstr IPv4

3. PHONE: Open browser
   http://192.168.1.100:8000/supplier/login/

4. PHONE: Login
   ├─ Username: test_supplier
   └─ Password: supplier123

5. PHONE: See Dashboard ✅
   ├─ Statistics cards
   ├─ Recent orders
   └─ Quick actions

6. COMPUTER: Create Purchase Order
   ├─ Login as admin
   ├─ Purchase Orders → Create
   ├─ Select "Test Supplier Co."
   ├─ Add items: Flour × 10
   └─ Submit

7. PHONE: Refresh supplier dashboard
   └─> Should see: "Pending Orders: 1" ✅

8. PHONE: Approve Order
   ├─ Click on pending order
   ├─ Click "Approve Order"
   ├─ Enter prices
   ├─ Set delivery date
   └─ Submit

9. PHONE: Mark as Shipped
   ├─ Open approved order
   ├─ View QR code
   └─ Click "Mark as Shipped"

10. COMPUTER: Scan & Receive
    ├─ Go to Scan & Receive page
    ├─ Click [📷 Scan]
    ├─ Point camera at phone QR
    └─> ✅ Order received!

COMPLETE! ✅
```

---

## 🎯 Alternative: Use Phone for Everything

You can also use phone for staff functions:

```
PHONE: Access as Admin
http://192.168.1.100:8000/login/
├─ Login as admin
├─ Navigate Purchase Orders
├─ Create order
├─ Use camera to scan QR
└─> All works on phone too!

Mobile-responsive design! ✅
```

---

## 📋 Quick Reference

### Your Test Credentials

```
===========================================
SUPPLIER ACCOUNT
===========================================
Company:  Test Supplier Co.
URL:      http://YOUR-IP:8000/supplier/login/
Username: test_supplier
Password: supplier123

===========================================
ADMIN ACCOUNT (Your existing)
===========================================
URL:      http://YOUR-IP:8000/login/
Username: (your admin username)
Password: (your admin password)

===========================================
COMMANDS
===========================================
Get IP:   ipconfig | findstr IPv4
Run:      python manage.py runserver 0.0.0.0:8000
Stop:     Ctrl + C
```

---

## 🎥 Features to Test on Phone

### Camera Scanning (Best on Phone!)

```
1. Go to Scan & Receive page
2. Click [📷 Scan] button
3. Phone camera activates
4. Point at QR code
5. Auto-detects!
6. Auto-receives!

Perfect for warehouse use! ✅
```

### Supplier Portal (Mobile-Friendly!)

```
1. Responsive design
2. Touch-friendly buttons
3. Easy navigation
4. All features work
5. Professional on mobile

Great for suppliers on the go! ✅
```

---

## 💡 Pro Tips

### For Best Results

1. **Same Network**: Ensure both devices on same Wi-Fi
2. **Note IP**: Write down your IP, it might change
3. **Keep Server Running**: Don't close PowerShell window
4. **Refresh**: If changes don't show, refresh browser
5. **Test Camera**: Works better on phone than laptop

### For Warehouse Use

1. **Use phone/tablet for scanning**
2. **Keep computer running server**
3. **Multiple devices can connect**
4. **Fast and efficient**

---

## 🎊 Summary

### What You Can Do Now

✅ **Access from phone**: Using your network IP  
✅ **Test supplier login**: test_supplier / supplier123  
✅ **Use camera scanning**: On mobile device  
✅ **Complete workflow**: From phone  
✅ **Mobile-responsive**: All features work  

### Commands

```powershell
# Get IP
ipconfig | findstr IPv4

# Run server for phone access
python manage.py runserver 0.0.0.0:8000

# Access from phone
http://YOUR-IP:8000/supplier/login/
```

### Login

```
Username: test_supplier
Password: supplier123
```

---

**🎉 You're ready to test on your phone!** 🎉

**Start the server and try it out!** 📱

---

**Guide Version**: 1.0  
**Last Updated**: October 17, 2025  
**Status**: ✅ Ready to Use

