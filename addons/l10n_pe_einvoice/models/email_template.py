from openerp.osv import osv, fields

class email_template(osv.osv):
    _inherit = "email.template"
    
    def generate_email_batch(self, cr, uid, template_id, res_ids, context=None, fields=None):
        res_fd = super(email_template, self).generate_email_batch(cr, uid, template_id, res_ids, context, fields)
        res = dict(res_fd)
        ctx = dict(context)
        if ctx.get('is_attach_evinvoice'):
            for res_id in res_ids:
                vals = dict(res[res_id])
                attach = vals.get('attachment_ids', [])
                attach_ids = ctx.get('attach_evinvoice', []) + attach
                vals.update({'attachment_ids':attach_ids})
                res[res_id]=vals
        return  res