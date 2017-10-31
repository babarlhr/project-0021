from openerp import fields, models, api, _
from openerp.exceptions import Warning
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class VehicleCategory(models.Model):
    _name = 'vehicle.category'
    _description = 'Vehicle Category'

    name = fields.Char('Name', size=50)


class VehicleType(models.Model):
    _name = 'vehicle.type'
    _description = 'Vehicle Type'

    name = fields.Char('Name', size=50)


class VehicleBrand(models.Model):
    _name = 'vehicle.brand'
    _description = 'Vehicle Brand'

    name = fields.Char('Name', size=50)


class VehicleBrandType(models.Model):
    _name = 'vehicle.brand.type'
    _description = 'Vehicle Brand Type'

    name = fields.Char('Name', size=50)


class VehicleDamageType(models.Model):
    _name = 'vehicle.damage.type'
    _description = 'Vehicle Damage Type'

    name = fields.Char('Name', size=50)

class VehicleWorkType(models.Model):
    _name = 'vehicle.work.type'
    _description = 'Vehicle Work Type'

    name = fields.Char('Name', size=50, required=True)
    comment = fields.Text('Description')
    work_type_stage_ids = fields.One2many('vehicle.work.type.stage','work_type_id','Stages')

class VehicleWorkTypeStage(models.Model):
    _name = 'vehicle.work.type.stage'
    _description = 'Vehicle Work Type Stage'
    _order = 'work_type_id, sequence'

    name = fields.Char('Name', size=50, required=True)
    work_type_id = fields.Many2one('vehicle.work.type','Work Type')
    product_id = fields.Many2one('product.template','Product')
    duration = fields.Integer('Duration in Day')
    sequence = fields.Integer('Sequence', required=True)
    comment = fields.Text('Description')
    work_type_stage_material_ids = fields.One2many('vehicle.work.type.stage.material','work_type_stage_id','Materials')

class VehicleWorkTypeStageMaterial(models.Model):
    _name = 'vehicle.work.type.stage.material'
    _description = 'Vechile Work Type Stage Material'

    work_type_stage_id = fields.Many2one('vehicle.work.type.stage', 'Stage #')
    product_id = fields.Many2one('product.template', 'Product', required=True)
    quantity = fields.Integer('Qty', required=True, default=1)


class PartnerVehicle(models.Model):
    _name = 'partner.vehicle'
    _description = 'Partner Vehicle'

    name = fields.Char('Plat Number', size=10, required=True)
    partner_id = fields.Many2one('res.partner', 'Customer',required=True)
    vehicle_category_id = fields.Many2one('vehicle.category', 'Vehicle Category', required=True)
    #vehicle_type_id = fields.Many2one('vehicle.type', 'Vehicle Type', required=True)
    vehicle_color = fields.Char('Vehicle Color', required=True)
    chassis_number = fields.Char('Chassis Number', required=True)
    vehicle_brand_id = fields.Many2one('vehicle.brand', 'Vehicle Brand', required=True)
    vehicle_brand_type_id = fields.Many2one('vehicle.brand.type','Vehicle Brand Type', required=True)
    manufacture_year = fields.Integer('Manufacture Year', required=True)
    machine_sn = fields.Char('Machine Number', size=50, required=True)
    image = fields.Binary('Image')

    _sql_constraints = [
        ('uniq_name', 'unique(name)', "A Plat Number already exists with this number .Plat Number name must be unique!"),
    ]

    @api.multi
    def create_workorder(self):
        #view_ref = self.env['ir.model.data'].get_object_reference('jakc_workorder', 'view_workorder_form')
        #view_id = view_ref[1] if view_ref else False

        res = {
           'type': 'ir.actions.act_window',
           'name': _('Workorder'),
           'res_model': 'workorder',
           'view_type': 'form',
           'view_mode': 'form',
           'view_id': 768,
           'context': {'default_partner_vehicle_id': self.id}
        }

        return res



