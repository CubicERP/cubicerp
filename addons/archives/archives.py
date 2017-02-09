# -*- encoding: utf-8 -*-
##############################################################################
#
#    Branch Cubic ERP, Enterprise Management Software
#    Copyright (C) 2013 Cubic ERP - Teradata SAC (<http://cubicerp.com>).
#
#    This program can only be used with a valid Branch Cubic ERP agreement,
#    it is forbidden to publish, distribute, modify, sublicense or sell 
#    copies of the program.
#
#    The adove copyright notice must be included in all copies or 
#    substancial portions of the program.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT WARRANTY OF ANY KIND; without even the implied warranty
#    of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
##############################################################################

from openerp import models, fields, api
from openerp.tools.translate import _


class archives_medium_type(models.Model):
    _name = "archives.medium.type"
    name = fields.Char('Name', required=True)


class archives_table_department(models.Model):
    _name = "archives.table.department"
    retention_table_id = fields.Many2one('archives.retention.table', 'Retention Table')
    department_id = fields.Many2one('hr.department', 'Department')
    work_time = fields.Float('Work Time', help="Time in days")


class archives_retention_table(models.Model):
    _name = "archives.retention.table"
    _description = "Archives Retention Table"
    
    name = fields.Char('Name', size=1024, required=True)
    code = fields.Char('Code', size=32, required=False)
    type =  fields.Selection([('view','View'),
                              ('normal','Normal')], 'Type', required=True)
    parent_id = fields.Many2one('archives.retention.table', 'Parent Table', domain=[('type','=','view')])
    retention_time_handling = fields.Integer('Retention Time Handling', help="Time in years")
    retention_time_archive = fields.Integer('Retention Time Archive', help="Time in years")
    final_disposition_preserve = fields.Boolean('Final Disposition Preserve')
    final_disposition_medium = fields.Boolean('Final Disposition Medium')
    final_medium_type_id = fields.Many2one('archives.medium.type', 'Final Medium Type')
    final_disposition_removal = fields.Boolean('Final Disposition Removal')
    final_disposition_selection = fields.Boolean('Final Disposition Selection')
    medium_type_ids = fields.Many2many('archives.medium.type','archives_table_medium_rel', string="Medium Types",
                                       help="Leave blank to permit all medium types")
    department_ids = fields.One2many('archives.table.department', 'retention_table_id', string='Departments',
                                     help="Leave blank to permit all departments")
    active = fields.Boolean('Acive', default=True)


class archives_process(models.Model):
    _name = "archives.process"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    name = fields.Char('Code', size=32, required=True)
    parent_id = fields.Many2one('archives.process', 'Parent Process')
    retention_table_id = fields.Many2one('archives.retention.table', 'Retention Table', required=True)
    description = fields.Text('Description')
    state = fields.Selection([('run','Run'),
                              ('cancel','Cancel')], 'State', readonly=True, default="run")
    step_ids = fields.One2many('archives.process.step', 'process_id', string="Steps")
    load_balance = fields.Selection([('robin', 'Round Robin'),
                                     ('random', 'Random'),
                                     ('alive', 'First Alive')], required=True, string="Load Balancing", default='robin')


class archives_process_step(models.Model):
    _name = "archives.process.step"
    
    sequence = fields.Integer('Sequence', required=True)
    name = fields.Char('Name', required=True)
    process_id = fields.Many2one('archives.process','Process', required=True, ondelete="cascade")
    department_id = fields.Many2one('hr.department', 'Department')
    job_ids = fields.One2many('archives.process.step.job', 'step_id', 'Jobs')
    document_ids = fields.One2many('archives.document', 'process_step_id', string='Current Documents')
    retention_table_ids = fields.Many2many('archives.retention.table', 'archives_process_table_rel',
                                           string='Retention Table Control',
                                           help="Leave blank to permit all retention tables")
    work_time = fields.Float('Work Time', help="Time in days")
    fold = fields.Boolean('Folded in Kanban View',
                           help='This stage is folded in the kanban view when'
                                'there are no records in that stage to display.')


class archives_transition(models.Model):
    _name = "archives.transition"

    sequence = fields.Integer("Sequence", default=5)
    src_step_id = fields.Many2one('archives.process.step', string="Source Step")
    dst_step_id = fields.Many2one('archives.process.step', string="Destinity Step")
    condition = fields.Text("Python Condition")
    params_action_id = fields.Many2one('ir.actions.act_window', string="Params Window")
    group_id = fields.Many2one('res.groups', string="Group Restriction")

    _order = "sequence"


class archives_process_step_job(models.Model):
    _name = "archives.process.step.job"

    step_id = fields.Many2one("archives.process.step", 'Process Step')
    job_id = fields.Many2one('hr.job', 'Job')
    sequence = fields.Integer("Priorty", default=5)

    _order = "sequence"


class archives_document_step(models.Model):
    _name = "archives.document.step"

    step_id = fields.Many2one('archives.process.step', 'Process Step')
    department_id = fields.Many2one('hr.department', 'Department')
    document_id = fields.Many2one('archives.document', string='Document')
    date_start = fields.Datetime('Date Start')
    date_compute = fields.Datetime('Date Compute', readonly=True)
    date_end = fields.Datetime('Date End')
    state = fields.Selection([('wait', 'Wait'),
                              ('run', 'Run'),
                              ('done', 'Done'),
                              ('cancel', 'Cancel')], 'State', readonly=True, default="wait")

    _order = "date_start desc"


class archives_collection_location(models.Model):
    _name = "archives.collection.location"
    
    name = fields.Char('Name', required=True)
    type = fields.Selection([('view','View'),
                              ('temporal','Temporal'),
                              ('handling','Handling'),
                              ('archive','Archive'),
                              ('destruction','Destruction'),
                              ('conversion','Conversion')], 'Type', required=True)
    parent_id = fields.Many2one('archives.collection.location', 'Parent Location', domain=[('type','=','view')])
    medium_type_ids = fields.Many2many('archives.medium.type', 'archives_collection_location_medium_rel',
                                       string="Medium Types", help="Leave blank to permit all medium types")
    partner_id = fields.Many2one('res.partner', string='Location Adress')


class archives_collection(models.Model):
    _name = "archives.collection"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    name = fields.Char('Code', required=True)
    parent_id = fields.Many2one('archives.collection', string="Copy Of")
    description = fields.Text('Description')
    location_id = fields.Many2one('archives.collection.location', 'Current Location', readonly=True) #Función
    move_ids = fields.One2many('archives.collection.move', 'collection_id', string="Moves")
    state= fields.Selection([('view','View'),
                              ('temporal','Temporal'),
                              ('handling','Handling'),
                              ('archive','Archive'),
                              ('destruction','Destruction'),
                              ('conversion','Conversion')], 'State', related='location_id.type', readonly=True)
    restrict_location_id = fields.Many2many('archives.collection.location', 'archives_collection_location_rel', string="Restrict Locations",
                                            help="Restrict the moves to selected locations for this collection. Leave blank to allow all locations")
    active = fields.Boolean('Active')

    
class archives_collection_move(models.Model):
    _name = "archives.collection.move"
    
    name = fields.Char('Name')
    date = fields.Datetime('Date', required=True)
    collection_id = fields.Many2one('archives.collection', string="Collection")
    employee_id = fields.Many2one('hr.employee', string="Responsible Employee")
    location_id = fields.Many2one('archives.collection.location', string="Source Location", required=True)
    location_dest_id = fields.Many2one('archives.collection.location', string="Destinity Location", required=True)
    partner_id = fields.Many2one('res.partner', string="Partner")


class archives_document(models.Model):
    _name = "archives.document"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.model
    def _get_attach_model(self):
        return []
    
    name = fields.Char('Name', size=32, required=True, readonly=True, states={'pending': [('readonly', False)]})
    parent_id = fields.Many2one('archives.document', string="Parent Document",
                                readonly=True, states={'pending': [('readonly', False)]})
    subject = fields.Text('Subject', readonly=True, states={'pending': [('readonly', False)]})
    retention_table_id = fields.Many2one('archives.retention.table', string='Retention Table', required=True,
                                         readonly=True, states={'pending': [('readonly', False)]})
    responsible_id = fields.Many2one('res.users', string="Responsible User", readonly=True) #Function from document.move
    process_step_id = fields.Many2one('archives.process.step', string='Last Process Step',
                                      readonly=True, states={'pending': [('readonly', False)]})
    collection_id = fields.Many2one('archives.collection', string='Collection',
                                    readonly=True, states={'pending': [('readonly', False)]})
    date_start = fields.Datetime('Date Start', readonly=True, states={'pending': [('readonly', False)]})
    date_compute = fields.Datetime('Date Compute', readonly=True)
    date_end = fields.Datetime('Date End', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Reply To',
                                 readonly=True, states={'pending': [('readonly', False)]})
    state = fields.Selection([('pending','Pending'),
                              ('done','Done'),
                              ('cancel','Cancel')], 'State', readonly=True, default="pending")
    folios = fields.Integer('Folios', readonly=True, states={'pending': [('readonly', False)]})
    adjunct = fields.Integer('Adjunct', readonly=True, states={'pending': [('readonly', False)]},
                             help="Zero disable this option")
    propagate = fields.Boolean('Parent Propagate',
                                 readonly=True, states={'pending': [('readonly', False)]})
    step_ids = fields.One2many('archives.document.step', 'document_id', string="Step History",
                               readonly=True, states={'pending': [('readonly', False)]})
    move_ids = fields.One2many('archives.document.move', 'document_id', string="Moves",
                                 readonly=True, states={'pending': [('readonly', False)]})
    version_ids = fields.One2many('archives.document.version', 'document_id', string="Versions",
                                 readonly=True, states={'pending': [('readonly', False)]})
    attach_model = fields.Reference(_get_attach_model, string="Attach Models")
    company_id = fields.Many2one('res.company', string="Company", required=True, 
                                 default=lambda self: self.env.user.company_id.id,
                                 readonly=True, states={'pending': [('readonly', False)]})
    color = fields.Integer('Color')
    active = fields.Boolean('Active', default=True)

    def _read_group_stage_ids(self, cr, uid, ids, domain, read_group_order=None, access_rights_uid=None, context=None):
        access_rights_uid = access_rights_uid or uid
        stage_obj = self.pool.get('archives.process.step')
        stage_ids = stage_obj.search(cr, uid, [], context=context)
        result = stage_obj.name_get(cr, access_rights_uid, stage_ids, context=context)
        # restore order of the search
        result.sort(lambda x, y: cmp(stage_ids.index(x[0]), stage_ids.index(y[0])))

        fold = {}
        for stage in stage_obj.browse(cr, access_rights_uid, stage_ids, context=context):
            fold[stage.id] = stage.fold or False
        return result, fold

    _group_by_full = {
        'process_step_id': _read_group_stage_ids
    }
    

class archives_document_version(models.Model):
    _name = "archives.document.version"
    
    document_id = fields.Many2one('archives.document', string="Docuement", required=True)
    name = fields.Char('Name', required=True)
    date = fields.Date('Date', required=True)
    attachment_ids = fields.One2many('ir.attachment', 'archive_version_id', string="Attachments")


class archives_document_move_type(models.Model):
    _name = "archives.document.move.type"
    name = fields.Char('Name', required=True)


class archives_document_move(models.Model):
    _name = "archives.document.move"
    
    document_id = fields.Many2one('archives.document', string="Docuement", required=True)
    type = fields.Many2one('archives.document.move.type', string="Move Type", required=True)
    date_start = fields.Datetime('Date Start')
    date_end = fields.Datetime('Date End')
    source_department_id = fields.Many2one('hr.department', string="Source Department") # related to user
    dest_department_id = fields.Many2one('hr.department', string="Destinity Department") # related to user
    source_user_id = fields.Many2one('res.users', string="Source User", required=True)
    dest_user_id = fields.Many2one('res.users', string="Destinity User", required=True)
    state = fields.Selection([('pending','Pending'),
                              ('acept','Acept'),
                              ('reject','Reject')], 'State', readonly=False, default="pending")
