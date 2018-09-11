from openerp import models, fields, api
from datetime import datetime
from openerp.exceptions import ValidationError, Warning, UserError
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class WizardApproveWorkcenterLine(models.TransientModel):
    _name = 'wizard.approve.workcenter.line'

    attachment = fields.Binary('Salvage Image', required=False)
    attachment_filename = fields.Char('File Name')

    @api.one
    def approved_workcenter_line(self):
        mrp_production_workcenter_line_obj = self.env['mrp.production.workcenter.line']
        active_id = self.env.context.get('active_id') or False
        mrp_production_workcenter_line = mrp_production_workcenter_line_obj.browse(active_id)
        routing_wc_line = mrp_production_workcenter_line.routing_wc_line
        if routing_wc_line.iface_salvage_image:
            logger.info("Need Salvage Image")
            if self.attachment:
                logger.info("Image Exist")
                logger.info('Close Production Workcenter Line')
                #mrp_production_workcenter_line.action_done()
                if mrp_production_workcenter_line.do_production:
                    logger.info('Production Do Production and Action End')
                    mrp_production_workcenter_line.action_done()
                    mrp_production_workcenter_line.production_id.action_production_end()
                else:
                    mrp_production_workcenter_line.action_done()
                #Create  Image
                sale_order_id = mrp_production_workcenter_line.sale_order_id
                sale_order_salvage_image_obj = self.env['sale.order.before.image']
                sale_order_salvage_image_obj.create({'sale_order_id': sale_order_id.id, 'attachment': self.attachment, 'attachment_filename': self.attachment_filename})
            else:
                raise ValidationError('Please Provide Salvage Image')
        else:
            logger.info("No Need Salvage Image")
            logger.info('Close Production Workcenter Line')
            #mrp_production_workcenter_line.action_done()
            if mrp_production_workcenter_line.do_production:
                logger.info('Production Do Production and Action End')
                mrp_production_workcenter_line.action_done()
                mrp_production_workcenter_line.production_id.action_production_end()
            else:
                mrp_production_workcenter_line.action_done()
        return True