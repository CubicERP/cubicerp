from openerp import models, fields, api, _

class PeEinvoiceSendWizard(models.TransientModel):
    _name="pe.einvoice.send.wizard"
    
    @api.model
    def _get_number(self):
        self.number=len(self.pe_einvoice_lines)
    
    pe_einvoice_lines=fields.One2many("pe.einvoice.send.wizard.line", 'pe_invoice_send_id', 
                                      string="Batch Lines")
    state=fields.Selection([('draft','Draft'), ('ready','Ready'), ('send','Send')], string='State',
                           default="draft", readonly=True)
    number = fields.Integer("Number", compute=_get_number, help="Number of documents selected")
    
    date = fields.Date("Date", required=True, default=fields.Date.context_today)
    
    @api.multi
    def prepate_to_send(self):
        #pe_einvoice_lines= self.env['einvoice.batch.pe'].search(["|",('state','=','ready'),('state','=','draft'), ('invoice_id.date_invoice', '=', self.date)], order="date, type, id asc")
        pe_einvoice_lines= self.env['account.invoice'].search([('batch_pe_id.state', 'in', ['draft', 'ready', 'request']),  
                                                               ('date_invoice', '=', self.date), "|", ('sunat_payment_type', '=', '01'),
                                                               ('parent_id.sunat_payment_type', '=', '01')], order="date_invoice, type, id asc")
        for pe_einvoice_line in pe_einvoice_lines: 
            if pe_einvoice_line.batch_pe_id.type=="sync" and len(pe_einvoice_line.batch_pe_id.invoice_ids)==0:
                continue
            elif pe_einvoice_line.batch_pe_id.type=="RA" and len(pe_einvoice_line.batch_pe_id.invoice_voided_ids)==0:
                continue
            elif pe_einvoice_line.batch_pe_id.type=="RC" and len(pe_einvoice_line.batch_pe_id.invoice_summary_ids)==0:
                continue
            self.env['pe.einvoice.send.wizard.line'].create({'pe_invoice_send_id':self[0].id,
                                                             'type':pe_einvoice_line.batch_pe_id.type,
                                                             'date':pe_einvoice_line.date_invoice,
                                                             'state':pe_einvoice_line.batch_pe_id.state,
                                                             'status_code':pe_einvoice_line.status_code,
                                                             'pe_einvoice_id':pe_einvoice_line.batch_pe_id.id})
        self.write({'state': 'ready'})
        invoice_view=self.env.ref('l10n_pe_einvoice.pe_einvoice_send_wizard_from', False)
        
        return {'type': 'ir.actions.act_window',
            'res_model': 'pe.einvoice.send.wizard',
            'views': [(invoice_view.id, 'form')],
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': str(invoice_view.id),
            'res_id': self[0].id,
            'context': self.env.context.copy(),
            'view_mode': 'form',
            'target': 'new',}
    
    @api.one
    def send_invoice(self):
        for line in self.pe_einvoice_lines:
            if line.state not in ['ready', 'draft', 'request']:
                continue
            if line.status_code:
                continue
            if not line.pe_einvoice_id.emessage_ids:
                line.pe_einvoice_id.action_ready()
            line.pe_einvoice_id.action_request()
            self.env.cr.commit()
        self.write({'state': 'send'})
        invoice_view=self.env.ref('l10n_pe_einvoice.pe_einvoice_send_wizard_from', False)
        
        return {'type': 'ir.actions.act_window',
            'res_model': 'pe.einvoice.send.wizard',
            'views': [(invoice_view.id, 'form')],
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': str(invoice_view.id),
            'res_id': self[0].id,
            'context': self.env.context.copy(),
            'view_mode': 'form',
            'target': 'new',}
    
    @api.multi
    def close_cb(self):
        return {'type': 'ir.actions.act_window_close'}
    
class PeEinvoiceSendWizardLine(models.TransientModel):
    _name="pe.einvoice.send.wizard.line"
    
    @api.model
    def _get_status_code(self):
        return self.env['base.element'].get_as_selection('PE.SEE.ERROR')
    
    @api.model
    def _get_type(self):
        return self.env['base.element'].get_as_selection('PE.SEE.TIPO')
    
    pe_invoice_send_id=fields.Many2one("pe.einvoice.send.wizard", "Invoices to Send")
    type=fields.Selection(_get_type, string='Type', store=True, readonly=True)
    date=fields.Date("Date", readonly=True)
    state=fields.Char("State", readonly=True)
    status_code=fields.Selection(_get_status_code, string='Status code', store=True, readonly=True)
    pe_einvoice_id=fields.Many2one("einvoice.batch.pe", "Batch", 
                                   required=True, readonly=True)
        