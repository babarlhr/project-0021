from openerp import models, fields, api
from datetime import datetime


class WizardConsumeMaterial(models.TransientModel):
    _name = 'wizard.consume.material'

    @api.model
    def default_get(self, fields):
        res = super(WizardConsumeMaterial, self).default_get(fields)
        sale_order_consume_material_obj = self.env['sale.order.consume.material']
        active_id = self.env.context.get('active_id') or False
        sale_order_consume_material = sale_order_consume_material_obj.browse(active_id)
        res['consume_material_id'] = sale_order_consume_material.id
        return res

    consume_material_id = fields.Many2one('sale.order.consume.material', 'Consume Material', readonly=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)

    @api.one
    def process_consume_material(self):
        consume_material_id = self.consume_material_id
        consume_material_id.employee_id = self.employee_id.id
        consume_material_id.trans_consume_material()
