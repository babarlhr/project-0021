from openerp import api, fields, models, _
import logging

logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    origin = fields.Char('Source Document', copy=True, \
                         help="Reference of the document that generated this purchase order "
                              "request (e.g. a sale order or an internal procurement request)")
    printed_num = fields.Integer('Printed #', readonly=True)

    @api.multi
    def print_purchase_order(self):
        res = self.env['report'].get_action(self, 'jakc_purchase.report_purchaseorder_custom')
        printed_num = self.printed_num + 1
        self.write({'printed_num': printed_num})
        return res


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    @api.multi
    def make_po(self):
        mrp_production_obj = self.env['mrp.production']
        cache = {}
        res = []
        for procurement in self:
            suppliers = procurement.product_id.seller_ids.filtered(
                lambda r: not r.product_id or r.product_id == procurement.product_id)
            if not suppliers:
                procurement.message_post(
                    body=_('No vendor associated to product %s. Please set one to fix this procurement.') % (
                        procurement.product_id.name))
                continue
            supplier = suppliers[0]
            partner = supplier.name

            gpo = procurement.rule_id.group_propagation_option
            group = (gpo == 'fixed' and procurement.rule_id.group_id) or \
                    (gpo == 'propagate' and procurement.group_id) or False

            domain = (
                ('partner_id', '=', partner.id),
                ('state', '=', 'draft'),
                ('picking_type_id', '=', procurement.rule_id.picking_type_id.id),
                ('company_id', '=', procurement.company_id.id),
                ('dest_address_id', '=', procurement.partner_dest_id.id))
            if group:
                domain += (('group_id', '=', group.id),)

            if domain in cache:
                po = cache[domain]
            else:
                po = self.env['purchase.order'].search([dom for dom in domain])
                po = po[0] if po else False
                cache[domain] = po
            if not po:
                vals = procurement._prepare_purchase_order(partner)
                po = self.env['purchase.order'].create(vals)
                cache[domain] = po
            elif not po.origin or procurement.origin not in po.origin.split(', '):
                # Keep track of all procurements
                if po.origin:
                    if procurement.origin:
                        po.write({'origin': po.origin + ', ' + procurement.origin})
                    else:
                        po.write({'origin': po.origin})
                else:
                    po.write({'origin': procurement.origin})
            if po:
                res += [procurement.id]

                #Update Purchase Order Notes
                if ':' in procurement.origin:
                    sale_order_id = self.env['sale.order'].search([('name', '=', procurement.origin.split(':')[0])])
                    if sale_order_id and procurement.product_id.iface_paint:
                        po.write({'notes':sale_order_id.partner_vehicle_id.vehicle_color + ' - ' + sale_order_id.paint_category_id.name})


            # Create Line
            po_line = False
            for line in po.order_line:

                if line.product_id == procurement.product_id and line.product_uom == procurement.product_id.uom_po_id:
                    procurement_uom_po_qty = self.env['product.uom']._compute_qty_obj(procurement.product_uom,
                                                                                      procurement.product_qty,
                                                                                      procurement.product_id.uom_po_id)
                    seller = self.product_id._select_seller(
                            procurement.product_id,
                            partner_id=partner,
                            quantity=line.product_qty + procurement_uom_po_qty,
                            date=po.date_order and po.date_order[:10],
                            uom_id=procurement.product_id.uom_po_id)


                    price_unit = self.env['account.tax']._fix_tax_included_price(seller.price,
                                                                                 line.product_id.supplier_taxes_id,
                                                                                 line.taxes_id) if seller else 0.0

                    if price_unit and seller and po.currency_id and seller.currency_id != po.currency_id:
                        price_unit = seller.currency_id.compute(price_unit, po.currency_id)

                    if sale_order_id:
                        if sale_order_id.paint_category_id and procurement.product_id.iface_paint:
                          price_unit = sale_order_id.paint_category_id.standard_price

                    po_line = line.write({
                        'product_qty': line.product_qty + procurement_uom_po_qty,
                        'price_unit': price_unit,
                        'procurement_ids': [(4, procurement.id)]
                    })
                    break

            if not po_line:
                vals = procurement._prepare_purchase_order_line(po, supplier)
                if sale_order_id:
                    if sale_order_id.paint_category_id and procurement.product_id.iface_paint:
                        vals.update({'price_unit':sale_order_id.paint_category_id.standard_price})
                self.env['purchase.order.line'].create(vals)

        return res