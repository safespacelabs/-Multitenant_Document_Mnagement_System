# E-Signature Button Debug Guide

## 🔍 Where to Find the E-Signature Button

The green "Sign Document" button should appear in the **Documents** section for system admins. Here's how to find it:

### Step 1: Navigate to Documents
1. Login as system admin (`admin2@system.local`)
2. Go to **Documents** section (not E-signature management)
3. Look for the document list

### Step 2: Check for Buttons
For each document in the list, you should see **action buttons on the right side**:
- 🔵 **Blue "Send for Signature" button** (create formal request)
- 🟢 **Green "Sign Document" button** (direct sign) ← **This is what you're looking for!**
- 🔴 **Red trash button** (delete)

### Step 3: Debug Steps

#### A. Check Browser Console
1. Open browser Developer Tools (F12)
2. Go to Console tab
3. Refresh the Documents page
4. Look for these debug messages:
   ```
   🔍 DocumentESignatureIntegration render: {
     userRole: "system_admin",
     canSignDirectly: true,
     ...
   }
   ```

#### B. Check User Role
In the console, you should see:
```javascript
🔍 canSignDirectly check: {
  userRole: "system_admin",
  isSystemAdmin: true,
  canSign: true
}
```

If you see `userRole: "system_admin"` and `canSign: true`, the button should appear.

#### C. Common Issues & Solutions

**Issue 1: No buttons at all**
- **Cause**: User not logged in or wrong role
- **Solution**: Ensure you're logged in as `admin2@system.local`

**Issue 2: Only blue button, no green button**
- **Cause**: User role is not `system_admin`
- **Solution**: Check login credentials and user role

**Issue 3: No documents visible**
- **Cause**: No documents uploaded yet
- **Solution**: Upload a document first, then check for buttons

**Issue 4: Button not clickable**
- **Cause**: JavaScript errors or authentication issues
- **Solution**: Check browser console for errors

### Step 4: Test the Button
1. Click the **green "Sign Document" button**
2. A modal should open with:
   - Document information
   - Signature text input field
   - Green "Sign Document" button
3. Enter your signature and click to complete

### Step 5: Verify Success
After signing:
- Success message should appear
- Modal should close
- Document should now show as signed in e-signature management

## 🚨 Troubleshooting

### If you still can't see the button:

1. **Check Network Tab**: Look for API calls to `/api/esignature/`
2. **Check Authentication**: Ensure you're logged in as system admin
3. **Check Browser Cache**: Try hard refresh (Ctrl+F5)
4. **Check for Errors**: Look for JavaScript errors in console

### Expected Console Output:
```
🔍 DocumentESignatureIntegration render: {
  userRole: "system_admin",
  userId: "sysuser_c6805be0",
  canCreateSignatureRequest: false,
  canSignDirectly: true,
  documentId: "doc_12345678",
  documentName: "example.pdf"
}
```

If you see `canSignDirectly: true`, the green button should be visible!

## 📍 Exact Location

The button appears in:
- **Page**: Documents
- **Section**: Document list
- **Position**: Right side of each document row
- **Color**: Green
- **Text**: "Sign Document"
- **Icon**: Pen tool icon

## 🔧 Still Need Help?

If you're still having issues, please:
1. Share the console output from the debug messages
2. Take a screenshot of the Documents page
3. Confirm your login credentials and role 