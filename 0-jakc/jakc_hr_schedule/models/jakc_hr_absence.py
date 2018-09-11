from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from openerp import fields, models, api

AVAIALABLE_STATES = [
    ('open','Open'),
    ('done','Close')
]

class HrAbsence(models.Model):
    _name = 'hr.absence'

    schedule_detail_id = fields.Many2one('hr.schedule.detail', 'Schedule Detail')
    name = fields.Many2one('hr.employee','Employee', required=True, readonly=True)
    trans_date_time = fields.Datetime('Date And Time', required=True, readonly=True)
    machine_id = fields.Char('Machine #', size=20)
    state = fields.Selection(AVAIALABLE_STATES, 'Status', default='open', readonly=True)











