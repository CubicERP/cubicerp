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
import random

from openerp import api, fields, models, _
from openerp import SUPERUSER_ID
# from openerp.exceptions import

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
    active = fields.Boolean('Active', default=True)


class archives_process(models.Model):
    _name = "archives.process"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _parent_store = True
    
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
    parent_left = fields.Integer('Parent Left')
    parent_right = fields.Integer('Parent Right')

    step_count = fields.Integer('Step Count', compute='_compute_step_count')
    document_count = fields.Integer('Document', compute='_compute_document_count')

    color = fields.Integer('Color')

    @api.multi
    @api.depends('step_ids')
    def _compute_step_count(self):
        for record in self:
            record.step_count = len(record.step_ids)

    @api.multi
    @api.depends('step_ids.document_ids')
    def _compute_document_count(self):
        for record in self:
            record.document_count = len(record.mapped('step_ids.document_ids'))


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

    @api.one
    @api.depends('process_id.load_balance', 'job_ids')
    def _compute_candidate(self):
        candidate_2skip = self.env['hr.employee']

        for job in self.job_ids:
            candidate = self.find_candidate(job)

            if candidate not in candidate_2skip and self.check_availability(candidate):
                return candidate.user_id

            candidate_2skip |= candidate

    @api.one
    @api.returns('hr.employee', lambda r: r.id)
    def find_candidate(self, job=None):
        candidate = self.env['hr.employee']
        query = ''
        job = job or self.job_ids[:1] or False

        if not job or not job.employee_ids:
            return candidate

        # find a random candidate in the job
        if self.process_id.load_balance == 'random':
            candidate = random.choice(job.employee_ids)

        # find the (LRU) Least Recently Used candidate in the job
        if self.process_id.load_balance == 'robin':
            query = '''
            SELECT DISTINCT
                   e.id AS employee_id, e.name_related, u.id AS dest_user_id,
                   CAST(9999999999 - EXTRACT(
                                        DAY FROM CURRENT_DATE
                                               - COALESCE(m.date_start, '1900-01-01 00:00:00')
                                        ) AS BIGINT) AS key
              FROM archives_process_step_job AS p INNER JOIN hr_job AS j
                ON p.job_id = j.id INNER JOIN hr_employee AS e
                ON j.id = e.job_id INNER JOIN resource_resource AS r
                ON e.resource_id = r.id INNER JOIN res_users AS u
                ON r.user_id = u.id LEFT JOIN archives_document_move AS m
                ON u.id = m.dest_user_id
             WHERE p.step_id = 1 AND j.id = 3
             ORDER BY CAST(9999999999 - EXTRACT(
                                        DAY FROM CURRENT_DATE
                                               - COALESCE(m.date_start, '1900-01-01 00:00:00')
                                        ) AS BIGINT) ASC
             LIMIT 1;
            '''

        # fiend the Less Loaded candidate in the job
        if self.process_id.load_balance == 'alive':
            query = '''
            SELECT e.id AS employee_id, e.name_related, u.id AS dest_user_id,
                   COUNT(d.responsible_id) AS key
              FROM archives_process_step_job AS p INNER JOIN hr_job AS j
                ON p.job_id = j.id INNER JOIN hr_employee AS e
                ON j.id = e.job_id INNER JOIN resource_resource AS r
                ON e.resource_id = r.id INNER JOIN res_users AS u
                ON r.user_id = u.id LEFT JOIN archives_document AS d
                ON u.id = d.responsible_id
             WHERE p.step_id = 1 AND j.id = 3
             GROUP BY e.id, e.name_related, u.id
             ORDER BY COUNT(d.responsible_id) ASC
             LIMIT 1;
            '''

        if not candidate and query:
            self.env.cr.execute(query, (self.id, job.id))
            data = self.env.cr.dictfetchnone()
            try:
                candidate = candidate.browse(data['employee_id'])
            except:
                pass

        return candidate

    @api.model
    def sort_candidates(self, candidates, step_id):
        if not candidates:
            return candidates

        query = ''

        # random sort of the given candidates
        if step_id.process_id.load_balance == 'random':
            random.shuffle(candidates)

        # (LRU) Least Recently Used sort of the given candidates
        if step_id.process_id.load_balance == 'robin':
            query = '''
            SELECT DISTINCT
                   e.id AS employee_id, e.name_related, u.id AS dest_user_id,
                   CAST(9999999999 - EXTRACT(
                                        DAY FROM CURRENT_DATE
                                               - COALESCE(m.date_start, '1900-01-01 00:00:00')
                                        ) AS BIGINT) AS key
              FROM archives_process_step_job AS p INNER JOIN hr_job AS j
                ON p.job_id = j.id INNER JOIN hr_employee AS e
                ON j.id = e.job_id INNER JOIN resource_resource AS r
                ON e.resource_id = r.id INNER JOIN res_users AS u
                ON r.user_id = u.id LEFT JOIN archives_document_move AS m
                ON u.id = m.dest_user_id
             WHERE p.step_id = %s AND e.id in %s
             ORDER BY CAST(9999999999 - EXTRACT(
                                        DAY FROM CURRENT_DATE
                                               - COALESCE(m.date_start, '1900-01-01 00:00:00')
                                        ) AS BIGINT) ASC;
            '''

        # Less Loaded sort of the given candidate
        if step_id.process_id.load_balance == 'alive':
            query = '''
            SELECT e.id AS employee_id, e.name_related, u.id AS dest_user_id,
                   COUNT(d.responsible_id) AS key
              FROM archives_process_step_job AS p INNER JOIN hr_job AS j
                ON p.job_id = j.id INNER JOIN hr_employee AS e
                ON j.id = e.job_id INNER JOIN resource_resource AS r
                ON e.resource_id = r.id INNER JOIN res_users AS u
                ON r.user_id = u.id LEFT JOIN archives_document AS d
                ON u.id = d.responsible_id
             WHERE p.step_id %s AND e.id in %s
             GROUP BY e.id, e.name_related, u.id
             ORDER BY COUNT(d.responsible_id) ASC;
            '''

        if query:
            self.env.cr.execute(query, (step_id.id, tuple(candidates.ids),))
            data = {item.pop('employee_id'): item for item in self.env.cr.dictfetchall()}

            candidates = candidates.sorted(key=lambda r: data.get(r.id, {'key': 0})['key'])

        return candidates

    @api.model
    def check_availability(self, candidate):
        return True

    @api.cr
    def _register_hook(self, cr):
        """ Register discovered exporters addons dynamically to configuration settings model's fields
            and registers then in the model's table """

        def make_res_users_search():
            """ instantiate a _search method for order users based on process policy """
            @api.model
            def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
                result = _search.origin(self, args=args, offset=offset, limit=limit, order=order,
                                        count=count, access_rights_uid=access_rights_uid)

                if not result:
                    return result

                if not count and self._context.get('arch_process_policy', False):
                    if self._context.get('arch_document_id'):
                        if self._context.get('arch_behavior') == 'delegate':
                            document = self.env['archives.document'].browse(self._context.get('arch_document_id'))
                            candidates = self.env['hr.employee'].search([
                                                        ('user_id', 'in', result),
                                                        ])
                            res = self.env['archives.process.step'].sort_candidates(
                                                            candidates,
                                                            document.process_step_id
                                                            )
                            return res and [r.user_id.id for r in res] or []

                return result

            return _search

        env = api.Environment(cr, SUPERUSER_ID, {})
        env['res.users']._patch_method('_search', make_res_users_search())


class archives_transition(models.Model):
    _name = "archives.transition"

    _order = "sequence"

    sequence = fields.Integer("Sequence", default=5)
    src_step_id = fields.Many2one('archives.process.step', string="Source Step")
    dst_step_id = fields.Many2one('archives.process.step', string="Destinity Step")
    condition = fields.Text("Python Condition")
    params_action_id = fields.Many2one('ir.actions.act_window', string="Params Window")
    group_id = fields.Many2one('res.groups', string="Group Restriction")

    # TODO: Add boolean parameter to merge wizard's params of other transition


class archives_process_step_job(models.Model):
    _name = "archives.process.step.job"

    _order = "sequence"

    step_id = fields.Many2one("archives.process.step", 'Process Step')
    job_id = fields.Many2one('hr.job', 'Job')
    sequence = fields.Integer("Priorty", default=5)


class archives_document_step(models.Model):
    _name = "archives.document.step"

    _order = "date_start desc"

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
    # document's movement fields
    move_ids = fields.One2many('archives.document.move', 'document_step_id', "Document's movement")


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
    def _compute_attach_model_selection(self):
        return []
    
    @api.model
    def _default_process_id(self):
        """ Gives default process by checking if present in the context """
        return self._resolve_process_id_from_context() or False

    @api.model
    def _resolve_process_id_from_context(self):
        """ Returns ID of process based on the value of 'default_process_id'
            context key, or None if it cannot be resolved to a single
            process.
        """
        if type(self._context.get('default_process_id')) in (int, long):
            return self._context['default_process_id']

        if isinstance(self._context.get('default_process_id'), basestring):
            try:
                return self.env['archives.process'].name_search(
                                        name=self._context['default_process_id']
                                        ).ensure_one().id
            except:
                pass

        return None

    @api.model
    def _read_group_stage_ids(self, ids, domain, read_group_order=None, access_rights_uid=None):
        access_rights_uid = access_rights_uid or self.sudo()._uid
        ProcessStep = self.env['archives.process.step']

        search_domain = []
        process_id = self._resolve_process_id_from_context()
        if process_id:
            search_domain += ['|', ('process_id', '=', process_id)]
        search_domain += [('id', 'in', ids)]

        stage_ids = ProcessStep._search(search_domain, access_rights_uid=access_rights_uid)
        stages = ProcessStep.sudo(access_rights_uid).browse(stage_ids)
        result = stages.name_get()
        # restore order of the search
        result.sort(lambda x, y: cmp(stage_ids.index(x[0]), stage_ids.index(y[0])))

        fold = {}
        for stage in stages:
            fold[stage.id] = stage.fold or False
        return result, fold

    name = fields.Char('Name', size=32, required=True, readonly=True, states={'pending': [('readonly', False)]})
    parent_id = fields.Many2one('archives.document', string="Parent Document",
                                readonly=True, states={'pending': [('readonly', False)]})
    subject = fields.Text('Subject', readonly=True, states={'pending': [('readonly', False)]})
    retention_table_id = fields.Many2one('archives.retention.table', string='Retention Table', required=True,
                                         readonly=True, states={'pending': [('readonly', False)]})
    responsible_id = fields.Many2one('res.users', string="Responsible User", readonly=True,
                                     default=lambda self: self.env.user,
                                     compute="_compute_responsible_id",
                                     store=True) #Function from document.move
    process_step_id = fields.Many2one('archives.process.step', string='Last Process Step',
                                      readonly=True, states={'pending': [('readonly', False)]},
                                      domain="[('process_id', '=', process_id)]")
    collection_id = fields.Many2one('archives.collection', string='Collection',
                                    readonly=True, states={'pending': [('readonly', False)]})
    date_start = fields.Datetime('Date Start', readonly=True, states={'pending': [('readonly', False)]})
    date_compute = fields.Datetime('Date Compute', readonly=True)
    date_end = fields.Datetime('Date End', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Reply To')#, readonly=True, states={'pending': [('readonly', False)]}
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
    attach_model = fields.Reference(_compute_attach_model_selection, string="Attach Models")
    company_id = fields.Many2one('res.company', string="Company", required=True, 
                                 default=lambda self: self.env.user.company_id.id,
                                 readonly=True, states={'pending': [('readonly', False)]})
    color = fields.Integer('Color')
    active = fields.Boolean('Active', default=True)

    process_id = fields.Many2one('archives.process', string="Process", required=True,
                                 # related='process_step_id.process_id',
                                 default=_default_process_id,
                                 domain="[('step_ids', '!=', False)]",
                                 help='Actual Document Process') #, compute="_compute_process_id"

    _group_by_full = {
        'process_step_id': _read_group_stage_ids
        }

    @api.model
    def create(self, vals):
        res = super(archives_document, self).create(vals)
        if len(vals.get('step_ids')) != 0:
            # list_step = sorted(vals.get('step_ids'),key='date_start')
            list_step = self.env['archives.document.step'].browse(vals.get('step_ids'))
            vals.update({'process_step_id': list_step[0].step_id})
        else:

            process = self.env['archives.process'].browse(vals.get('process_id'))
            if len(process.step_ids) ==0:
                a=0
            vals_document_step = {}
            vals_document_step['step_id'] = process.step_ids[0].id
            vals_document_step['department_id'] = process.step_ids[0].department_id.id

            document_step = self.env['archives.document.step'].create(vals_document_step)
            res.step_ids += document_step
            lis_doc = process.step_ids[0].document_ids
            lis_doc += res
            process.step_ids[0].document_ids = lis_doc
            vals.update({'process_step_id': process.step_ids[0].id})

        return res

    @api.multi
    @api.depends('move_ids.dest_user_id')
    def _compute_responsible_id(self):
        for record in self:
            record.responsible_id = record.move_ids[-1:].dest_user_id

    # @api.multi
    # @api.depends('step_ids.step_id')
    # def _compute_process_id(self):
    #     """ return the process of the last document's step """
    #     for record in self:
    #         record.process_id = record.step_ids[:1].document_id

    @api.multi
    @api.onchange('process_id')
    def _onchange_process_id(self):
        for record in self:
            record.retention_table_id = record.process_id.retention_table_id


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
    
    _order = 'date_start asc'

    document_id = fields.Many2one('archives.document', string="Docuement", required=True)
    # in what step was the document when it moved
    document_step_id = fields.Many2one('archives.document.step', string="Document Steps",
                                       help="In what step was the document when it moved")
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
