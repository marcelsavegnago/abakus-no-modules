# -*- coding: utf-8 -*-
# (c) AbAKUS IT Solutions
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class ProductTemplateWithCostPriceAuto(models.Model):
    _inherit = ['product.template']

    cost_price_from_suppliers = fields.Boolean('Auto cost from suppliers', default=True)
    standard_price = fields.Float('Cost Price', compute='_compute_lowest_supplier_price')
    manual_cost_price = fields.Float(default=0)

    @api.one
    @api.depends('cost_price_from_suppliers', 'seller_ids', 'manual_cost_price')
    def _compute_lowest_supplier_price(self):
        self.ensure_one()
        if self.cost_price_from_suppliers:
            # Get the lowest price for suppliers
            min_price = 0
            for supp in self.seller_ids:
                if (min_price == 0 and supp.price > 0) or (supp.state == 'sellable' and supp.price < min_price):
                    min_price = supp.price

            self.standard_price = min_price
        else:
            self.standard_price = self.manual_cost_price

        # Set the flag on the child products
        for variant in self.product_variant_ids:
            variant.standard_price = self.standard_price


class ProductProductWithCostPriceAuto(models.Model):
    _inherit = ['product.product']

    standard_price = fields.Float('Cost Price', compute='_compute_standard_price')

    @api.multi
    @api.depends('product_tmpl_id')
    def _compute_standard_price(self):
        self.ensure_one()
        self.standard_price = self.product_tmpl_id.standard_price

    @api.multi
    def open_product_template(self):
        if self.product_tmpl_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'product.product_template_only_form_view',
                'res_model': 'product.template',
                'res_id': self.product_tmpl_id.id,
                'view_type': 'form',
                'view_mode': 'form',
            }
