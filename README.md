# Daily Tasks Module

## Overview
The Daily Tasks module allows employees to record their daily tasks and provides HR/Managers with comprehensive reporting capabilities.

## Features

### For Employees
- Record daily tasks with title and date
- Plan of the Day (POD) - describe what you plan to accomplish
- Summary of the Day (SOD) - summarize what was actually accomplished
- View only your own tasks
- Task status tracking (Draft/Done)

### For HR/Managers
- View all employee tasks
- Comprehensive reporting with graphs and pivot views
- Dashboard analytics
- Department and manager tracking

## Installation
1. Copy the `daily_tasks` folder to your Odoo addons directory
2. Update the module list in Odoo
3. Install the "Daily Tasks" module

## Usage

### Main Menu Structure
- **Daily Tasks**
  - **Tasks**
    - My Tasks (All users)
    - All Tasks (HR/Managers only)
  - **Reporting** (HR/Managers only)
    - Dashboard
  - **Configuration** (System Admin only)
    - Settings

### Access Rights
- **Employees**: Can create, read, edit, and delete their own tasks only
- **HR Users/Managers**: Can view and manage all employee tasks
- **System Admin**: Full access to all features

### Task Fields
- **Name**: Task title (required)
- **Date**: Auto-filled with today's date
- **Employee**: Auto-filled from logged-in user
- **Department**: Auto-filled from employee's department
- **Manager**: Auto-filled from employee's manager
- **POD Description**: Plan of the Day
- **SOD Description**: Summary of the Day
- **State**: Draft or Done

### Views Available
- Tree View: List of tasks with all key information
- Form View: Detailed task form with POD/SOD buttons
- Calendar View: Task calendar overview
- Kanban View: Card-based task management
- Graph View: Visual analytics
- Pivot View: Cross-tabulation reporting

## Technical Details
- **Model**: `daily.task`
- **Dependencies**: `base`, `hr`
- **Version**: Compatible with Odoo 17.0

## Author
Custom Development Team