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
    export_as_JSON: function () {
        return _.extend(_paylineproto.export_as_JSON.apply(this, arguments), {paid: this.paid,
                                                                              cardnumber: this.cardnumber,
                                                                              cardowner: this.cardowner});
                                                                              
    },
   
});

//Popup to show all transaction state for the payment.

var CreditCardPopupWidget = PopupWidget.extend({
    template: 'CreditCardPopupWidget',
    
    show: function(options){
    	
    	// This keyboard handler listens for keypress events. It is
        // also called explicitly to handle some keydown events that
        // do not generate keypress event
    	
        this.keyboard_handler = function(event){
            var key = '';
           
            if (event.type === "keypress") {
                if (event.keyCode === 13) { // Enter
                    self.validate_order();
                } else if ( event.keyCode === 190 || // Dot
                            event.keyCode === 110 ||  // Decimal point (numpad)
                            event.keyCode === 188 ||  // Comma
                            event.keyCode === 46 ) {  // Numpad dot
                    key = self.decimal_point;
                } else if (event.keyCode >= 48 && event.keyCode <= 57) { // Numbers
                    key = '' + (event.keyCode - 48);
                } else if (event.keyCode === 45) { // Minus
                    key = '-';
                } else if (event.keyCode === 43) { // Plus
                    key = '+';
                }
            } else { // keyup/keydown
                if (event.keyCode === 46) { // Delete
                    key = 'CLEAR';
                } else if (event.keyCode === 8) { // Backspace
                    key = 'BACKSPACE';
                }
            }
            this.$("#cardnumber").val(String.fromCharCode(event.keyCode))
            event.preventDefault();
        }
        
        options = options || {};
        this._super(options);

        this.renderElement();
        
        var cardnumber = "";
        
        this.chrome.widget.keyboard.connect($(this.el.querySelector("#cardnumber")));
        this.chrome.widget.keyboard.connect($(this.el.querySelector("#cardowner")));
        this.$("#cardnumber").focus();
        
    },
    click_confirm: function(){
        var cardnumber = this.$("#cardnumber").val();
        var cardowner = this.$("#cardowner").val();
        this.gui.close_popup();
        if( this.options.confirm ){
            this.options.confirm.call(this,cardnumber,cardowner);
        }
    },
});
gui.define_popup({name:'creditcard', widget: CreditCardPopupWidget});


var CardNumberPopupWidget = PopupWidget.extend({
    template: 'CardNumberPopupWidget',
    show: function(options){
        options = options || {};
        this._super(options);

        this.inputbuffer = '' + (options.value   || '');
        this.decimal_separator = _t.database.parameters.decimal_point;
        this.renderElement();
        this.firstinput = true;
    },
    click_numpad: function(event){
        var newbuf = this.gui.numpad_input(
            this.inputbuffer, 
            $(event.target).data('action'), 
            {'firstinput': this.firstinput});

        this.firstinput = (newbuf.length === 0);
        
        if (newbuf !== this.inputbuffer) {
            this.inputbuffer = newbuf;
            this.$('.value').text(this.inputbuffer);
        }
    },
    click_confirm: function(){
        this.gui.close_popup();
        if( this.options.confirm ){
            this.options.confirm.call(this,this.inputbuffer);
        }
    },
});
gui.define_popup({name:'cardnumber', widget: CardNumberPopupWidget});

PaymentScreenWidget.include({
        	   
            click_card_paymentline: function(cid){
                var self = this;
                var order = this.pos.get_order();
            	var lines = order.get_paymentlines();
                for ( var i = 0; i < lines.length; i++ ) {
                    if (lines[i].cid === cid) {
        				self.gui.show_popup('cardnumber',{
        				    'title': _t('Card Number'),
        		            'value': order.selected_paymentline.cardnumber,
        		            'confirm': function(value) {
        		            	order.selected_paymentline.cardnumber = value;
        		                self.order_changes();
        		                self.render_paymentlines();
        		            }
        				});
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