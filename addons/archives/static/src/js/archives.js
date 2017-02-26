/**
 * Created by development on 2/19/17.
 */
openerp.archives = function(openerp) {
    openerp.web_kanban.KanbanRecord.include({
        on_card_clicked: function() {
            if (this.view.dataset.model === 'archives.process') {
                this.$('.oe_kanban_process_list a').first().click();
            } else {
                this._super.apply(this, arguments);
            }
        },
    });
};
