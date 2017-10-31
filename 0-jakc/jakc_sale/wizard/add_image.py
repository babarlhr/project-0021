from openerp import models, fields, api


class WizardAddImage(models.TransientModel):
    _name = 'wizard.add.image'

    attachment = fields.Binary('Image', required=True)
    state = fields.Selection([('before', 'Before'), ('after', 'After')], 'State', required=True)

    @api.one
    def add_image(self):
        active_id = self.env.context.get('active_id') or False
        values = {}
        values.update({'line_id': active_id})
        values.update({'attachment': self.attachment})
        values.update({'state': self.state})
        self.env['mrp.production.workcenter.line.image'].create(values)


