# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Grzegorz Marczyński
#    Copyright 2016 QAQA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api
from openerp import tools

from openerp.osv import osv, fields
from openerp import models, api
from openerp.tools.translate import _

class stock_move(osv.osv):
    _inherit = "stock.move"

    _columns = {
            'reversed_by_stock_move': fields.boolean(string='Is Reversed by Stock Move?', default=False, copy=False),
            'reversed_stock_move_id': fields.many2one('stock.move', string='Reversed by Stock Move', copy=False),
        }

    @api.multi
    def action_reverse(self):
        self.reverse_stock_move(False)

    @api.multi
    def reverse_stock_move(self, process_to_done=True):
        not_done_reverse_moves = []
        for stock_move in self:
            if stock_move.reversed_stock_move_id or stock_move.state != 'done':
                not_done_reverse_moves.append(stock_move)
                continue
            reverse_data = {
                'name' : "Reversed "+stock_move.name,
                'location_id' : stock_move.location_dest_id.id,
                'location_dest_id' : stock_move.location_id.id,
                'reversed_stock_move_id' : None,
                'reversed_by_stock_move' : False
                }
            stock_move_reversed = stock_move.copy(reverse_data)
            stock_move.write({"reversed_stock_move_id" : stock_move_reversed.id, 'reversed_by_stock_move' : True})
            if process_to_done:
                self.pool("stock.move").action_assign(self._cr, self._uid, [stock_move_reversed.id])
                self.pool("stock.move").action_done(self._cr, self._uid, [stock_move_reversed.id])
        if len(not_done_reverse_moves):
            raise osv.except_osv("Warning!", "Some moves not reversed: "+str([x.name for x in not_done_reverse_moves])+". They were not 'done' or already reversed.")

class Wizard(models.TransientModel):
    _name = 'reverse_stock_move.wizard'

    def _default_stock_moves(self):
        moves = self.env['stock.move'].browse(self._context.get('active_ids'))
        return [move.id for move in moves if not move.reversed_by_stock_move and move.state == 'done']

    _columns = {
        'stock_moves_ids' :  fields.many2many('stock.move', string="Stock Moves", default=_default_stock_moves),
        'process_move' : fields.boolean(string="Process reverse move(s) to 'done'?", default=True),
    }

    @api.multi
    def reverse(self):
        self.stock_moves_ids.reverse_stock_move()

        return {}


