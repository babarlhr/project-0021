from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from openerp import models, fields, api


class WizardProcessAbsence(models.TransientModel):
    _name = 'wizard.process.absence'



    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    iface_all_employee = fields.Boolean('All Employee', default=True)
    employee_ids = fields.Many2many('hr.employee','rel_process_absence_employee','employee_id','employee_absence_id')
    re_calculate = fields.Boolean('Re-Calculate', default=False)

    def daterange(self, str_start_date, str_end_date):
        start_date = fields.Date.from_string(str_start_date)
        end_date = fields.Date.from_string(str_end_date)
        for n in range(int((end_date - start_date).days + 1)):
            yield start_date + timedelta(n)

    def unlink_exception(self, schedule_detail_id):
        exception_obj = self.env['hr.schedule.detail.exception']
        args = [('schedule_detail_id','=' , schedule_detail_id)]
        exception_ids = exception_obj.search(args)
        exception_obj.unlink(exception_ids)

    @api.one
    def process_absence(self):
        print "Proces Absence"
        employee_obj = self.env['hr.employee']
        contract_obj = self.env['hr.contract']
        schedule_detail_obj = self.env['hr.schedule.detail']
        absence_obj = self.env['hr.absence']

        if self.iface_all_employee:
            employees = employee_obj.search([])
        else:
            employee_ids = []
            print "employee"
            print self.employee_ids
            for employee in self.employee_ids:
                employee_ids.append(employee.id)
            print employee_ids
            employees = employee_obj.search([('id', 'in', employee_ids)])

        for employee in employees:
            contract_args = [('employee_id', '=', employee.id)]
            contract = contract_obj.search(contract_args)
            if contract:
                print employee.name
                #schedule_template_id = contract.schedule_template_id
                for single_date in self.daterange(self.start_date, self.end_date):
                    schedule_detail_args = [('employee_id', '=', employee.id), ('day', '=', single_date)]
                    schedule_detail = schedule_detail_obj.search(schedule_detail_args)
                    str_start_date = False
                    str_end_date = False
                    if schedule_detail:
                        print 'Found Schedule Detail'
                        if self.re_calculate:
                            #Clear Exception
                            for exception in schedule_detail.exception_ids:
                                exception.unlink()

                            start_date = datetime.strptime(single_date.strftime('%Y-%m-%d') + ' 00:00:00', '%Y-%m-%d %H:%M:%S') + timedelta(hours=-7)
                            str_start_date = start_date.strftime('%Y-%m-%d %H:%M:%S')
                            print str_start_date
                            end_date = datetime.strptime(single_date.strftime('%Y-%m-%d') + ' 00:00:00','%Y-%m-%d %H:%M:%S') + timedelta(days=1) +  timedelta(hours=-7)
                            str_end_date = end_date.strftime('%Y-%m-%d %H:%M:%S')
                            print str_end_date

                            absence_args = [('name', '=', employee.id),
                                            '&',
                                            ('trans_date_time', '>', str_start_date)
                                            , ('trans_date_time', '<', str_end_date)
                                            ]
                        else:
                            absence_args = [('name', '=', employee.id),
                                            '&', ('trans_date_time', '>', str_start_date)
                                            , ('trans_date_time', '<', str_end_date)
                                            , ('state', '=', 'open')
                                            ]

                        employee_absences = absence_obj.search(absence_args, order='trans_date_time asc')
                        for employee_absence in employee_absences:
                            values = {}
                            values.update({'schedule_detail_id': schedule_detail[0].id})
                            values.update({'state': 'done'})
                            employee_absence.write(values)

                        if schedule_detail.type == 'work':
                            schedule_detail.process_absence()

