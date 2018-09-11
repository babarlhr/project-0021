from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from openerp import models, fields, api


class WizardProcessException(models.TransientModel):
    _name = 'wizard.process.exception'

    @api.multi
    def process_exception(self):
        schedule_detail_exception_obj = self.env['hr.schedule.detail.exception']
        schedule_detail_exception = schedule_detail_exception_obj.browse(self.schedule_detail_exception_id.id)
        values = {}
        values.update({'exception_request_date': datetime.now()})
        values.update({'exception_reason': self.exception_reason.id})
        values.update({'approved_by': schedule_detail_exception.schedule_detail_id.employee_id.parent_id.id})
        values.update({'state': 'request'})
        schedule_detail_exception.sudo().write(values)
        print "Send Notification to Manager"

    schedule_detail_exception_id = fields.Many2one('hr.schedule.detail.exception', 'Schedule Detail Exception', readonly=True)
    date_start = fields.Datetime(string='Start Date Time', store=True, related='schedule_detail_exception_id.schedule_detail_id.date_start', readonly=True)
    date_end = fields.Datetime(string='End Date Time', store=True, related='schedule_detail_exception_id.schedule_detail_id.date_end', readonly=True)
    actual_in = fields.Datetime(string='Actual In', store=True, related='schedule_detail_exception_id.schedule_detail_id.actual_in', readonly=True)
    actual_out = fields.Datetime(string='Actual Out', store=True, related='schedule_detail_exception_id.schedule_detail_id.actual_out', readonly=True)
    exception_code = fields.Selection([('normal', 'NO'),
                                       ('normexcept', 'NWE'),
                                       ('noswapin', 'NSI'),
                                       ('noswapout', 'NSO'),
                                       ('latein', 'LI'),
                                       ('earlyout', 'EO'),], 'Exception',
                                      related='schedule_detail_exception_id.exception_code', readonly=True)
    exception_reason = fields.Many2one('hr.exception.reason', 'Exception Reason', required=True)
    exception_description = fields.Text('Exception Description')


class WizardProcessExceptionApproved(models.TransientModel):
    _name = 'wizard.process.exception.approved'

    @api.multi
    def process_exception_approved(self):
        schedule_detail_obj = self.env['hr.schedule.detail']
        schedule_detail_exception_obj = self.env['hr.schedule.detail.exception']
        schedule_detail_exception = schedule_detail_exception_obj.browse(self.schedule_detail_exception_id.id)
        values = {}
        values.update({'approved_state': self.approved_state})
        values.update({'approved_date': datetime.now()})
        values.update({'approved_reason': self.approved_reason})
        values.update({'state': self.approved_state})
        schedule_detail_exception.sudo().write(values)
        schedule_detail_exception.schedule_detail_id.validate_schedule_detail()
        print "Send Notification to Employee"


    schedule_detail_exception_id = fields.Many2one('hr.schedule.detail.exception', 'Schedule Detail Exception', readonly=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', related='schedule_detail_exception_id.employee_id', readonly=True)
    date_start = fields.Datetime(string='Start Date Time', store=True, related='schedule_detail_exception_id.schedule_detail_id.date_start', readonly=True)
    date_end = fields.Datetime(string='End Date Time', store=True, related='schedule_detail_exception_id.schedule_detail_id.date_end', readonly=True)
    actual_in = fields.Datetime(string='Actual In', store=True, related='schedule_detail_exception_id.schedule_detail_id.actual_in', readonly=True)
    actual_out = fields.Datetime(string='Actual Out', store=True, related='schedule_detail_exception_id.schedule_detail_id.actual_out', readonly=True)
    exception_code = fields.Selection([('normal', 'NO'),
                                       ('normexcept', 'NWE'),
                                       ('noswapin', 'NSI'),
                                       ('noswapout', 'NSO'),
                                       ('latein', 'LI'),
                                       ('earlyout', 'EO'), ], 'Exception',
                                      related='schedule_detail_exception_id.exception_code', readonly=True)
    exception_reason = fields.Many2one('hr.exception.reason', 'Exception Reason', related='schedule_detail_exception_id.exception_reason', readonly=True)
    exception_description = fields.Text('Exception Description', related='schedule_detail_exception_id.exception_description', readonly=True)
    approved_state = fields.Selection([
                                        ('approve', 'Approve'),
                                        ('reject', 'Reject'),
                                    ], 'Choose', required=True)
    approved_reason = fields.Text('Rejected Reason')


