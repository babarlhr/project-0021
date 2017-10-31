from datetime import date, datetime
from openerp import SUPERUSER_ID, api, models, fields
import logging
from openerp import tools
import smtplib
from email.mime.text import MIMEText

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    printed_num = fields.Integer('Printed #', readonly=True)

    @api.multi
    def do_print_picking(self):
        res = super(StockPicking, self).do_print_picking()
        printed_num = self.printed_num + 1
        self.write({'printed_num': printed_num})
        return res

    @api.model
    def send_picking_reminder(self):
        print "Send Picking Reminder"
        args = [('state','not in',['done','cancel','waiting']),('min_date','<', datetime.now().strftime("%Y-%m-%d " + "23:59:00"))]
        picking_ids = self.env['stock.picking'].search(args)

        res_users_args = [('iface_receive_notification','=',True)]
        res_users_ids = self.env['res.users'].search(res_users_args)

        recipients = []
        for res_users_id in res_users_ids:
            recipients.append(res_users_id.email)

        # define content

        sender = "andarumotors@gmail.com"
        subject = "Stock Picking In Waiting"

        body = '<html><head></head><body><table border="1">'
        body = '<tr><td>Reference</td><td>Destination Location</td><td>Partner</td><td>Schedule</td><td>Status</td></tr>'
        for picking_id in picking_ids:
            body = body + '<tr> ' + '<td>' + picking_id.name + '</td>' + '<td>' + picking_id.location_dest_id.name + '</td>' + '<td>' + picking_id.partner_id.name + '</td>' + '<td>' + picking_id.min_date + '</td>' +  '<td>' + picking_id.state + '</td>' + '</tr>'

        body = body + '</table></body></html>'

        # make up message
        msg = MIMEText(body,'html')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = ", ".join(recipients)


        # Send the message via our own SMTP server, but don't include the
        # envelope header.
        s = smtplib.SMTP_SSL('smtp.gmail.com',465)
        s.ehlo()
        s.login("andarumotors@gmail.com", "P@ssw0rd!@#")
        s.sendmail(sender, recipients, msg.as_string())
        s.quit()


        #headers = {}
        #IrMailServer = self.env['ir.mail_server']
        #msg = IrMailServer.build_email(
        #    email_from='Andaru Motors <andarumotors@gmail.com>',
        #    email_to='Wahyu Hidayat <wahhid@gmail.com>',
        #    subject='Stock Picking Follow Up',
        #    body='Email Body',
        #    body_alternative='Email Body',
        #    email_cc=tools.email_split(''),
        #    reply_to='Wahyu Hidayat <wahhid@gmail.com>',
        #    message_id='231312312',
        #    subtype='html',
        #    subtype_alternative='plain',
        #    headers=headers)
        #try:
        #    res = IrMailServer.send_email(msg, mail_server_id=1)
        #except AssertionError as error:
        #    print error.message