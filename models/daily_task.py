from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, datetime, time, timedelta
import pytz


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
        """Mark task as done and send SOD notification to manager"""
        self.write({'state': 'done'})
        
        # Send SOD notification to manager when task is marked as done
        for record in self:
            if record.sod_description:
                record._send_email_to_manager(
                    subject=f'SOD Submitted - {record.employee_id.name}',
                    body=f"""
                    <p>Hello,</p>
                    <p><strong>{record.employee_id.name}</strong> has submitted their Summary of the Day (SOD) for {record.date}.</p>
                    <h4>Summary of the Day:</h4>
                    <p>{record.sod_description or 'No description provided'}</p>
                    <p>This is an automated notification from the Daily Tasks system.</p>
                    """
                )

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
        """Override write to prevent POD changes after submission and SOD after done"""
        for record in self:
            # Prevent POD changes after submission
            if record.pod_submitted and 'pod_description' in vals:
                vals.pop('pod_description', None)
            # Prevent SOD changes after state is done
            if record.state == 'done' and 'sod_description' in vals:
                vals.pop('sod_description', None)
        result = super(DailyTask, self).write(vals)
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
        # Use company timezone and ensure we send notifications once per day
        company_tz = self.env.user.tz or self.env.company.tz or 'UTC'
        tz = pytz.timezone(company_tz)
        now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
        now_local = now_utc.astimezone(tz)

        # Only proceed at 11:00 in company timezone
        target_hour = 11
        if now_local.hour != target_hour:
            return

        today_local = now_local.date()
        
        # Skip sending on Sunday (weekday() returns 6 for Sunday)
        if today_local.weekday() == 6:
            return

        # Ensure we only send once per day
        param_key = 'daily_tasks.last_pod_notification'
        last_sent = self.env['ir.config_parameter'].sudo().get_param(param_key)
        if last_sent:
            try:
                last_sent_date = fields.Date.from_string(last_sent)
                if last_sent_date == today_local:
                    return
            except Exception:
                # If parsing fails, continue and overwrite
                pass

        # Get active employees who have a task for today but haven't submitted POD
        employees_without_pod = self.env['hr.employee']
        today = fields.Date.context_today(self)
        employees = self.env['hr.employee'].search([
            ('active', '=', True),
            ('user_id', '!=', False)
        ])

        for employee in employees:
            task = self.search([
                ('employee_id', '=', employee.id),
                ('date', '=', today)
            ], limit=1)
            if task and not task.pod_submitted:
                employees_without_pod |= employee

        # Send notifications to managers (only for no_pod)
        self._notify_managers_about_missing_pod(employees_without_pod)

        # Record that we've sent today's notifications
        self.env['ir.config_parameter'].sudo().set_param(param_key, fields.Date.to_string(today_local))
    
    def _notify_managers_about_missing_pod(self, employees_without_pod):
        """Send notification to direct managers about employees who haven't submitted POD.

        This method notifies only the direct manager of employees who have a task
        for today but did not submit their POD. It will only send an email to the
        manager's `work_email` and will not create extra mail messages or activities
        that might propagate to higher-level managers.
        """
        # Group employees by direct manager
        manager_employees_map = {}

        for employee in employees_without_pod:
            manager = employee.parent_id
            if not manager:
                continue
            if manager not in manager_employees_map:
                manager_employees_map[manager] = self.env['hr.employee']
            manager_employees_map[manager] |= employee

        # Send notifications to each manager (email only)
        for manager, emp_records in manager_employees_map.items():
            if not manager.user_id or not manager.work_email:
                continue

            emp_names = ', '.join(emp_records.mapped('name'))
            message = f"""
            <p>The following employees have not submitted their Plan of the Day (POD) by 11:00 AM:</p>
            <p><strong>{emp_names}</strong></p>
            <p>Please follow up with them.</p>
            """

            mail_values = {
                'subject': f'POD Escalation Alert ',
                'body_html': message,
                'email_to': manager.work_email,
                'email_from': self.env.company.email or 'noreply@odoo.com',
                'auto_delete': False,
            }
            mail = self.env['mail.mail'].sudo().create(mail_values)
            mail.send()
