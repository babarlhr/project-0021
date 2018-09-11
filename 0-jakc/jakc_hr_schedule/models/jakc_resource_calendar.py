from openerp import fields, models, api, _
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ResourceCalendarAttendance(models.Model):
    _inherit = 'resource.calendar.attendance'

    @api.onchange('shift')
    def onchange_shift(self):
        if self.shift:
            shift_data = self.env['hr.schedule.shift'].browse(self.shift.id)
            self.hour_from = shift_data.start_hours
            self.hour_to = shift_data.end_hours

    type = fields.Selection([
                                ('work','Work'),
                                ('holiday','Public Holiday'),
                                ('off','Off'), ], 'Type', required=True, default='work')
    shift = fields.Many2one('hr.schedule.shift', 'Shift', required=True)