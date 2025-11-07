from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, datetime, time


class DailyTask(models.Model):
    _name = 'daily.task'
    _description = 'Daily Task'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'
    _rec_name = 'date'
    _sql_constraints = [
        ('unique_employee_date', 'UNIQUE(employee_id, date)', 
         'You can only create one daily task per day. A task for this date already exists.')
    ]

    
    date = fields.Date(
        string='Date',
        readonly=True,
        required=True,
        default=fields.Date.context_today,
        help='Date when the task was created'
    )
    
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        default=lambda self: self._get_default_employee(),
        help='Employee who created this task',
        readonly=True,
    )
    
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        compute='_compute_employee_details',
        store=True,
        help='Department of the employee'
    )
    
    manager_id = fields.Many2one(
        'hr.employee',
        string='Manager',
        compute='_compute_employee_details',
        store=True,
        help='Manager of the employee'
    )
    
    pod_description = fields.Text(
        string='Plan of the Day (POD)',
        help='Plan and objectives for the day',
        tracking=True
    )
    
    pod_submitted = fields.Boolean(
        string='POD Submitted',
        default=False,
        help='Indicates if the Plan of the Day has been submitted and locked',
        tracking=True
    )
    
    pod_submitted_date = fields.Datetime(
        string='POD Submitted Date',
        help='Date and time when POD was submitted',
        readonly=True
    )
    
    sod_description = fields.Text(
        string='Summary of the Day (SOD)',
        help='Summary of what was accomplished during the day',
        tracking=True
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')
    ], string='Status', default='draft', required=True, tracking=True)

    @api.model
    def name_get(self):
        """Return a meaningful name for the record"""
        result = []
        for record in self:
            if record.employee_id and record.date:
                name = f"{record.employee_id.name} - {record.date}"
            elif record.date:
                name = f"Task - {record.date}"
            else:
                name = "Daily Task"
            result.append((record.id, name))
        return result

    def _get_default_employee(self):
        """Get the employee record for the current user"""
        employee = self.env['hr.employee'].search([
            ('user_id', '=', self.env.uid)
        ], limit=1)
        return employee.id if employee else False

    @api.depends('employee_id')
    def _compute_employee_details(self):
        """Compute department and manager from employee"""
        for record in self:
            if record.employee_id:
                record.department_id = record.employee_id.department_id.id
                record.manager_id = record.employee_id.parent_id.id
            else:
                record.department_id = False
                record.manager_id = False

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """Update department and manager when employee changes"""
        if self.employee_id:
            self.department_id = self.employee_id.department_id
            self.manager_id = self.employee_id.parent_id

    def action_set_pod(self):
        """Action to focus on POD field"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Plan of the Day',
            'res_model': 'daily.task',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
            'context': {'focus_field': 'pod_description'}
        }
    
    def action_submit_pod(self):
        """Submit and lock the POD"""
        if not self.pod_description:
            raise ValidationError('Please enter Plan of the Day before submitting.')
        
        self.write({
            'pod_submitted': True,
            'pod_submitted_date': fields.Datetime.now()
        })
        
        # Send email notification to manager
        self._send_email_to_manager(
            subject=f'POD Submitted - {self.employee_id.name}',
            body=f"""
            <p>Hello,</p>
            <p><strong>{self.employee_id.name}</strong> has submitted their Plan of the Day (POD) for {self.date}.</p>
            <h4>Plan of the Day:</h4>
            <p>{self.pod_description or 'No description provided'}</p>
            <p>This is an automated notification from the Daily Tasks system.</p>
            """
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'POD Submitted',
                'message': 'Plan of the Day has been submitted and locked successfully.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_set_sod(self):
        """Action to focus on SOD field"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Summary of the Day',
            'res_model': 'daily.task',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
            'context': {'focus_field': 'sod_description'}
        }

    def action_mark_done(self):
        """Mark task as done"""
        self.write({'state': 'done'})

    def action_mark_draft(self):
        """Mark task as draft"""
        self.write({'state': 'draft'})

    @api.model
    def create(self, vals):
        """Override create to ensure employee_id is set and check for duplicates"""
        if not vals.get('employee_id'):
            vals['employee_id'] = self._get_default_employee()
        
        # Check if a task already exists for this employee on this date
        employee_id = vals.get('employee_id')
        task_date = vals.get('date', fields.Date.context_today(self))
        
        if employee_id and task_date:
            existing_task = self.search([
                ('employee_id', '=', employee_id),
                ('date', '=', task_date)
            ], limit=1)
            
            if existing_task:
                raise ValidationError(
                    f'You can only create one daily task per day. '
                    f'A task for {task_date} already exists.'
                )
        
        # Create the record
        record = super(DailyTask, self).create(vals)
        
        # Trigger computation of department and manager
        if record.employee_id:
            record._compute_employee_details()
        
        return record

    @api.model
    def default_get(self, fields_list):
        """Override default_get to set default values"""
        defaults = super(DailyTask, self).default_get(fields_list)
        
        # Get current employee
        employee = self.env['hr.employee'].search([
            ('user_id', '=', self.env.uid)
        ], limit=1)
        
        if employee:
            defaults['employee_id'] = employee.id
            if 'department_id' in fields_list:
                defaults['department_id'] = employee.department_id.id if employee.department_id else False
            if 'manager_id' in fields_list:
                defaults['manager_id'] = employee.parent_id.id if employee.parent_id else False
                
        return defaults
    
    def write(self, vals):
        """Override write to prevent POD changes after submission and notify on SOD"""
        # Check if SOD is being written for the first time
        sod_written = False
        for record in self:
            # If POD is submitted and someone tries to change it, restore the original value
            if record.pod_submitted and 'pod_description' in vals:
                # Remove pod_description from vals to prevent any changes
                vals.pop('pod_description', None)
            
            # Check if SOD is being added or updated
            if 'sod_description' in vals and vals.get('sod_description'):
                if not record.sod_description or record.sod_description != vals['sod_description']:
                    sod_written = True
        
        result = super(DailyTask, self).write(vals)
        
        # Send email notification to manager when SOD is written
        if sod_written:
            for record in self:
                if vals.get('sod_description'):
                    record._send_email_to_manager(
                        subject=f'SOD Submitted - {record.employee_id.name}',
                        body=f"""
                        <p>Hello,</p>
                        <p><strong>{record.employee_id.name}</strong> has submitted their Summary of the Day (SOD) for {record.date}.</p>
                        <h4>Summary of the Day:</h4>
                        <p>{vals.get('sod_description', 'No description provided')}</p>
                        <p>This is an automated notification from the Daily Tasks system.</p>
                        """
                    )
        
        return result
    
    def _send_email_to_manager(self, subject, body):
        """Send email notification to manager"""
        if not self.manager_id or not self.manager_id.work_email:
            return
        
        mail_values = {
            'subject': subject,
            'body_html': body,
            'email_to': self.manager_id.work_email,
            'email_from': self.env.user.email or self.env.company.email,
            'auto_delete': True,
        }
        
        mail = self.env['mail.mail'].sudo().create(mail_values)
        mail.send()
    
    @api.model
    def _cron_check_unsubmitted_pod(self):
        """Scheduled action to check for unsubmitted PODs and notify managers"""
        today = fields.Date.context_today(self)
        
        # Get all active employees
        employees = self.env['hr.employee'].search([
            ('active', '=', True),
            ('user_id', '!=', False)
        ])
        
        employees_without_task = self.env['hr.employee']
        employees_without_pod = self.env['hr.employee']
        
        for employee in employees:
            # Check if employee has a task for today
            task = self.search([
                ('employee_id', '=', employee.id),
                ('date', '=', today)
            ], limit=1)
            
            if not task:
                # No task created at all
                employees_without_task |= employee
            elif not task.pod_submitted:
                # Task exists but POD not submitted
                employees_without_pod |= employee
        
        # Send notifications to managers
        self._notify_managers_about_missing_pod(employees_without_task, employees_without_pod)
    
    def _notify_managers_about_missing_pod(self, employees_without_task, employees_without_pod):
        """Send notification to managers about employees who haven't submitted POD"""
        # Group employees by manager
        manager_employees_map = {}
        
        all_employees = employees_without_task | employees_without_pod
        
        for employee in all_employees:
            if employee.parent_id:
                manager = employee.parent_id
                if manager not in manager_employees_map:
                    manager_employees_map[manager] = {
                        'no_task': self.env['hr.employee'],
                        'no_pod': self.env['hr.employee']
                    }
                
                if employee in employees_without_task:
                    manager_employees_map[manager]['no_task'] |= employee
                else:
                    manager_employees_map[manager]['no_pod'] |= employee
        
        # Send notifications to each manager
        for manager, employee_data in manager_employees_map.items():
            if manager.user_id:
                message_parts = []
                
                if employee_data['no_task']:
                    no_task_names = ', '.join(employee_data['no_task'].mapped('name'))
                    message_parts.append(f"<b>No task created:</b> {no_task_names}")
                
                if employee_data['no_pod']:
                    no_pod_names = ', '.join(employee_data['no_pod'].mapped('name'))
                    message_parts.append(f"<b>Task created but POD not submitted:</b> {no_pod_names}")
                
                if message_parts:
                    message = f"""
                    <p>The following employees have not submitted their Plan of the Day (POD) by 11:00 AM:</p>
                    <ul>
                        <li>{'</li><li>'.join(message_parts)}</li>
                    </ul>
                    <p>Please follow up with them.</p>
                    """
                    
                    # Send email to manager
                    if manager.work_email:
                        mail_values = {
                            'subject': f'POD Escalation Alert - {len(all_employees)} employee(s) pending',
                            'body_html': message,
                            'email_to': manager.work_email,
                            'email_from': self.env.company.email or 'noreply@odoo.com',
                            'auto_delete': False,
                        }
                        mail = self.env['mail.mail'].sudo().create(mail_values)
                        mail.send()
                    
                    # Send message to manager via mail thread
                    if manager.user_id and manager.user_id.partner_id:
                        self.env['mail.message'].create({
                            'subject': f'POD Escalation Alert - {len(all_employees)} employee(s) pending',
                            'body': message,
                            'partner_ids': [(4, manager.user_id.partner_id.id)],
                            'message_type': 'notification',
                            'subtype_id': self.env.ref('mail.mt_note').id,
                        })
                    
                    # Create activity for manager
                    if manager.user_id:
                        self.env['mail.activity'].create({
                            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                            'summary': f'POD Escalation - {len(all_employees)} employee(s) pending',
                            'note': message,
                            'user_id': manager.user_id.id,
                            'res_id': self.env['hr.employee'].search([], limit=1).id,
                            'res_model_id': self.env['ir.model']._get('hr.employee').id,
                        })
