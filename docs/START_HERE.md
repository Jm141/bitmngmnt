# 🚀 START HERE - Quick Guide

## Your Test Supplier Account is Ready!

---

## 🎉 TEST ACCOUNT CREDENTIALS

```
╔═══════════════════════════════════════════════╗
║                                               ║
║  Company:  Test Supplier Co.                  ║
║                                               ║
║  Username: test_supplier                      ║
║  Password: supplier123                        ║
║                                               ║
╚═══════════════════════════════════════════════╝
```

---

## 🖥️ Step 1: Run Server (On Computer)

### Open PowerShell in your project folder:

```powershell
# Get your computer's IP address (write it down!)
ipconfig | findstr IPv4

# You'll see something like:
# IPv4 Address. . . : 192.168.1.100
#                     ↑ This is YOUR IP

# Run the server so phone can access it
python manage.py runserver 0.0.0.0:8000

# You should see:
# Starting development server at http://0.0.0.0:8000/
# ✅ Server is running!
```

**Keep this window open!** Don't close it.

---

## 📱 Step 2: Access from Phone

### On your phone browser:

Replace `192.168.1.100` with YOUR IP from Step 1:

```
http://192.168.1.100:8000/supplier/login/
         ↑ Your IP here
```

### Login with:
- Username: `test_supplier`
- Password: `supplier123`

**You should see the Supplier Dashboard!** 🎉

---

## 🧪 Step 3: Test the System

### On Computer (as Admin):

```
1. Open browser: http://localhost:8000/login/
2. Login with your admin credentials
3. Click "Purchase Orders" in menu
4. Click "Create Purchase Order"
5. Select "Test Supplier Co."
6. Click "Add Item" (should work now!)
7. Add: Flour × 10
8. Submit order
```

### On Phone (as Supplier):

```
1. Refresh supplier dashboard
2. Should see: "Pending Orders: 1"
3. Click on the pending order
4. Click "Approve Order"
5. Enter prices:
   - Flour: 800
6. Set delivery date: tomorrow
7. Click "Approve Order with Pricing"
8. ✅ Order approved!
9. Click "Mark as Shipped"
10. ✅ Order shipped!
```

### Back on Computer (Receive):

```
1. Go to "Scan & Receive"
2. Click [📷 Scan] button
3. Camera opens
4. Point at phone screen (showing QR code)
   Or use manual entry
5. ✅ Order received!
6. Check inventory - items added!
```

---

## 🎯 Quick Commands

### All Commands You Need:

```powershell
# 1. Find your IP
ipconfig | findstr IPv4

# 2. Run server for phone access
python manage.py runserver 0.0.0.0:8000

# 3. Stop server (when done)
Ctrl + C
```

---

## 📱 Phone Access URLs

Replace `192.168.1.100` with YOUR IP:

```
Supplier Login:
http://192.168.1.100:8000/supplier/login/

Staff Login:  
http://192.168.1.100:8000/login/

Admin Panel:
http://192.168.1.100:8000/admin/
```

---

## ⚠️ Important Notes

1. **Same Wi-Fi**: Phone and computer must be on same network
2. **Server Running**: Keep PowerShell window open
3. **Your IP**: Use YOUR actual IP, not the example
4. **Port 8000**: Make sure it's not blocked by firewall

---

## 🎊 That's It!

### You Now Have:

✅ Test supplier account ready  
✅ Commands to run server  
✅ Know how to access from phone  
✅ Can test camera scanning  

### Next Steps:

1. Run server with command above
2. Access from phone
3. Test the complete workflow
4. Create real supplier accounts when ready

---

**🎉 Everything is ready - start testing!** 🎉

**For detailed help, see: PHONE_ACCESS_GUIDE.md**

