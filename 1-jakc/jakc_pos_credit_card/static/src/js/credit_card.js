odoo.define('pos_mercury.pos_mercury', function (require) {
"use strict";

var Class   = require('web.Class');
var Model   = require('web.Model');
var session = require('web.session');
var core    = require('web.core');
var screens = require('point_of_sale.screens');
var gui     = require('point_of_sale.gui');
var pos_model = require('point_of_sale.models');
var utils = require('web.utils');

var QWeb = core.qweb;
var _t   = core._t;


var BarcodeParser = require('barcodes.BarcodeParser');
var PopupWidget = require('point_of_sale.popups');
var ScreenWidget = screens.ScreenWidget;
var PaymentScreenWidget = screens.PaymentScreenWidget;
var round_pr = utils.round_precision;

//Load Field iface_card
pos_model.load_fields("account.journal", "iface_card");

var _paylineproto = pos_model.Paymentline.prototype;
pos_model.Paymentline = pos_model.Paymentline.extend({
    init_from_JSON: function (json) {
        _paylineproto.init_from_JSON.apply(this, arguments);

        this.paid = json.paid;
        this.cardnumber = json.cardnumber;
        this.cardowner = json.cardowner;
       
    },

    set_cardnumber: function(cardnumber){
        this.cardnumber = cardnumber;
    },

    set_cardowner: function(cardowner){
        this.cardowner = cardowner;
    },

    export_as_JSON: function () {
        return _.extend(_paylineproto.export_as_JSON.apply(this, arguments), {paid: this.paid,
                                                                              cardnumber: this.cardnumber,
                                                                              cardowner: this.cardowner});
                                                                              
    },

   
});


/*--------------------------------------*\
 |          THE CARD PAYMENT SCREEN            |
\*======================================*/

// The scale screen displays the weight of
// a product on the electronic scale.

var CreditCardScreenWidget = PaymentScreenWidget.extend({
    template:'CreditCardPaymentScreenWidget',

    next_screen: 'payment',
    previous_screen: 'payment',

    init: function(parent, options){
        var self = this;
        this._super(parent, options);

        this.keyboard_keydown_handler = function(event){
            //
        }

        this.keyboard_handler = function(event){
            //
        }

    },

    show: function(){
        this._super();
        var self = this;
        var queue = this.pos.proxy_queue;

        this.renderElement();

        this.$('.back-card').click(function(){
            self.gui.show_screen(self.previous_screen);
        });

        this.$('.next-card').click(function(){
            self.fill_data();
            self.gui.show_screen(self.next_screen);
        });

        self.fill_screen();
    },

    fill_screen: function(){
        var line = this.pos.get_order().selected_paymentline;
        console.log(line);
        this.$('.card-number').val(line.cardnumber);
        this.$('.card-sowner').val(line.cardowner);
    },

    fill_data: function(){
        var line = this.pos.get_order().selected_paymentline;
        line.cardnumber = this.$('.card-number').val();
        line.cardowner = this.$('.card-owner').val();
        console.log(line);
        this.order_changes();
        this.render_paymentlines();
    },

    close: function(){
        this._super();
       //$('body').off('keypress',this.hotkey_handler);
       //this.pos.proxy_queue.clear();

    },
});

gui.define_screen({name: 'creditcardscreen', widget: CreditCardScreenWidget});

PaymentScreenWidget.include({
        	   
            click_card_paymentline: function(cid){
                var self = this;
                var order = this.pos.get_order();
            	var lines = order.get_paymentlines();
                for ( var i = 0; i < lines.length; i++ ) {
                    if (lines[i].cid === cid) {
        				self.gui.show_screen('creditcardscreen');
                    }
                }	        
            },

            render_paymentlines: function() {
            	var self  = this;
                var order = this.pos.get_order();
                if (!order) {
                    return;
                }

                var lines = order.get_paymentlines();
                var due   = order.get_due();
                var extradue = 0;
                if (due && lines.length  && due !== order.get_due(lines[lines.length-1])) {
                    extradue = due;
                }

                this.$('.paymentlines-container').empty();
                var lines = $(QWeb.render('PaymentScreen-Paymentlines', { 
                    widget: this, 
                    order: order,
                    paymentlines: lines,
                    extradue: extradue,
                }));

                lines.on('click','.delete-button',function(){
                    self.click_delete_paymentline($(this).data('cid'));
                });

                lines.on('click','.card-button',function(){
                    self.click_card_paymentline($(this).data('cid'));
                });
                
                lines.on('click','.paymentline',function(){
                    self.click_paymentline($(this).data('cid'));
                });
                    
                lines.appendTo(this.$('.paymentlines-container'));
            	
            },    
});

})