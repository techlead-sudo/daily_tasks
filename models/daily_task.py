from odoo import models, fields, api
from datetime import date


class DailyTask(models.Model):
    _name = 'daily.task'
    _description = 'Daily Task'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'
    _rec_name = 'date'

    
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
        """Override create to ensure employee_id is set"""
        if not vals.get('employee_id'):
            vals['employee_id'] = self._get_default_employee()
        
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
