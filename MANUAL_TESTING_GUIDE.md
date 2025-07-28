# Manual Testing Guide - Multi-Tenant Document Management System

This guide explains how to test the new **domain-specific login system** and **user invitation functionality**.

## 🏢 Company-Specific Login & Registration Portal

### New Features Implemented:
1. **Separate login pages for each company** with company branding
2. **Company-specific registration/access request system**
3. **Enhanced user invitation functionality** for system admins
4. **Company portal links** in the admin interface

---

## 🚀 Testing Scenarios

### 1. System Admin Flow (Multi-Company Management)

#### **Step 1: System Admin Login**
```
URL: http://localhost:3000/login
Credentials: 
- Username: systemadmin
- Password: admin123
```

#### **Step 2: Company Management Dashboard**
- After login, you'll see the "Enterprise Organizations" page
- Three companies are available: Amazon, Microsoft, SafespaceLabs
- Each company now has a **"Portal" button** - this leads to company-specific login

#### **Step 3: User Management with Invite Functionality**
- Click "Users" button for any company (e.g., Microsoft)
- **NEW**: You should now see an **"Invite User"** button in the top-right
- The button appears because system admins can now invite users to any company
- Click "Invite User" to test the invitation modal

#### **Step 4: Invite New Users to Companies**
Use the invite functionality to create test users:

**For Microsoft (comp_d8be6904):**
```
HR Admin:
- Email: hradmin@microsoft.com
- Full Name: Microsoft HR Admin
- Role: HR Admin

Manager:
- Email: manager@microsoft.com  
- Full Name: Microsoft Manager
- Role: HR Manager

Employee:
- Email: employee@microsoft.com
- Full Name: Microsoft Employee
- Role: Employee
```

---

### 2. Company-Specific Portal Access

#### **Step 1: Access Microsoft Portal**
```
URL: http://localhost:3000/company/comp_d8be6904/login
```

**Features:**
- **Company Branding**: Blue theme with Microsoft branding
- **Company Information**: Shows company name, ID, and "Enterprise Portal" 
- **Secure Access**: Company ID is displayed for verification
- **Navigation**: Links to register or browse other companies

#### **Step 2: Access Amazon Portal**  
```
URL: http://localhost:3000/company/comp_3e6dab46/login
```

**Features:**
- **Orange Theme**: Amazon-specific color scheme
- **Company Context**: Shows Amazon branding and information

#### **Step 3: Access SafespaceLabs Portal**
```
URL: http://localhost:3000/company/comp_e610e365/login
```

**Features:**
- **Green Theme**: SafespaceLabs-specific color scheme
- **Company Branding**: Customized for SafespaceLabs

---

### 3. Company Registration & Access Requests

#### **Step 1: Request Access to Microsoft**
```
URL: http://localhost:3000/company/comp_d8be6904/register
```

**Test the form with:**
```
Full Name: John Doe
Email: john.doe@microsoft.com
Username: johndoe
Department: Engineering
Reason: Need access to company documents for project work
```

#### **Step 2: Verify Access Request Flow**
- After submitting, you should see a success page
- The page confirms the request was submitted to Microsoft
- Links are provided to sign in (if you have an account) or browse other companies

---

### 4. Role-Based User Creation Testing

#### **Create Users with Different Roles Across All Companies:**

**Microsoft Company (comp_d8be6904):**
```
1. HR Admin - hradmin@microsoft.com
2. HR Manager - manager@microsoft.com  
3. Employee - employee@microsoft.com
4. Customer - customer@microsoft.com
```

**Amazon Company (comp_3e6dab46):**
```
1. HR Admin - hradmin@amazon.com
2. HR Manager - manager@amazon.com
3. Employee - employee@amazon.com
4. Customer - customer@amazon.com
```

**SafespaceLabs Company (comp_e610e365):**
```
1. HR Admin - hradmin@safespacelabs.com
2. HR Manager - manager@safespacelabs.com
3. Employee - employee@safespacelabs.com
4. Customer - customer@safespacelabs.com
```

---

## 🎯 Key Improvements Tested

### ✅ Fixed Issues:
1. **User Invitation Button**: Now visible for system admins in user management
2. **Company-Specific Access**: Each company has its own branded login portal
3. **Role Hierarchy**: System admins can invite any company role
4. **Access Requests**: Users can request access to specific companies
5. **Navigation**: Easy switching between companies and portals

### ✅ New URLs Available:
- **System Login**: `/login` (traditional system access)
- **Company Login**: `/company/{companyId}/login` (company-specific)
- **Company Register**: `/company/{companyId}/register` (access requests)
- **Company List**: `/companies` (admin view of all companies)

### ✅ Company Branding:
- **Microsoft**: Blue/Cyan theme
- **Amazon**: Orange/Yellow theme  
- **SafespaceLabs**: Green/Emerald theme
- **Default**: Blue/Indigo theme for other companies

---

## 🔧 Testing Checklist

### System Admin Features:
- [ ] Can access all company user management interfaces
- [ ] "Invite User" button is visible and functional
- [ ] Can create users with different roles (hr_admin, hr_manager, employee, customer)
- [ ] Company portal links work from admin interface

### Company-Specific Features:
- [ ] Each company has a unique branded login page
- [ ] Company registration/access request system works
- [ ] Company information is correctly displayed
- [ ] Navigation between companies works

### User Role Testing:
- [ ] Create HR Admins for each company
- [ ] Create HR Managers for each company  
- [ ] Create Employees for each company
- [ ] Create Customers for each company
- [ ] Verify password setup emails are sent (check invite emails)

---

## 🎪 Demo Scenarios

### **Scenario 1: New Employee Onboarding**
1. System admin invites new employee to Microsoft
2. Employee receives invitation email
3. Employee sets up password via unique link
4. Employee accesses Microsoft portal at `/company/comp_d8be6904/login`
5. Employee logs in and sees Microsoft-branded dashboard

### **Scenario 2: Customer Access Request**
1. Customer visits Microsoft portal
2. Customer clicks "Request Access"
3. Customer fills out access request form
4. HR Admin reviews request in user management
5. HR Admin invites customer with appropriate role

### **Scenario 3: Multi-Company Management**
1. System admin manages users across all companies
2. Each company maintains isolated user data
3. Company-specific themes and branding work
4. Role hierarchy is maintained per company

---

## 🏁 Success Criteria

**✅ User Management:**
- Invite button appears for system admins
- All roles can be assigned during invitation
- User invitation modal works correctly

**✅ Domain-Specific Access:**
- Each company has unique login portal
- Company branding themes work
- Access request system functional

**✅ Multi-Tenant Isolation:**
- Each company's users are isolated
- Database separation maintained
- Role-based permissions work per company

This testing guide ensures that both the **user invitation functionality** and **domain-specific login system** work as intended across all three companies (Microsoft, Amazon, SafespaceLabs) with proper role-based access controls. 