# Daily Tasks Module - Installation Guide

## Prerequisites
- Odoo 17.0 installation
- HR module installed
- Mail module installed (usually comes with Odoo)

## Installation Steps

### 1. Copy Module Files
Copy the entire `daily_tasks` folder to your Odoo addons directory:
```bash
cp -r daily_tasks /path/to/odoo/addons/
```

### 2. Update Module List
1. Go to Apps menu in Odoo
2. Click "Update Apps List"
3. Search for "Daily Tasks"

### 3. Install Module
1. Find "Daily Tasks" in the Apps list
2. Click "Install"

### 4. Configure Users and Permissions
1. Ensure users have the appropriate HR permissions:
   - **Employees**: User access rights
   - **HR Users**: HR Officer access rights
   - **HR Managers**: HR Manager access rights

### 5. Set Up Employees
1. Go to Employees menu
2. Ensure all employees have:
   - Associated user account
   - Department assigned
   - Manager assigned (optional)

## Post-Installation Verification

### Test Employee Access
1. Login as a regular employee
2. Go to Daily Tasks > Tasks > My Tasks
3. Create a new task
4. Verify you can only see your own tasks

### Test HR Access
1. Login as HR user/manager
2. Go to Daily Tasks > Tasks > All Tasks
3. Verify you can see all employee tasks
4. Check Daily Tasks > Reporting > Dashboard

## Troubleshooting

### Common Issues
1. **"No module named 'daily_tasks'"**
   - Ensure the module is in the correct addons path
   - Restart Odoo server
   - Update apps list

2. **Access denied errors**
   - Check user permissions
   - Ensure HR module is installed
   - Verify employee records are properly configured

3. **Empty employee field**
   - Ensure the user has an associated employee record
   - Check that the employee record has user_id set

### Support
If you encounter issues, check:
1. Odoo server logs
2. Module dependencies
3. User permissions and employee setup

## Features Overview

### Main Menu Structure
```
Daily Tasks
├── Tasks
│   ├── My Tasks (All Users)
│   └── All Tasks (HR Only)
├── Reporting (HR Only)
│   └── Dashboard
└── Configuration (Admin Only)
    └── Settings
```

### Access Control
- **Employees**: Own tasks only
- **HR Users/Managers**: All tasks
- **System Admin**: Full access

Enjoy using the Daily Tasks module!