odoo.define('account_report.account_report_ledger', function (require) {
'use strict';

var core = require('web.core');
var Widget = require('web.Widget');
var ControlPanelMixin = require('web.ControlPanelMixin');
var session = require('web.session');
var ReportWidget = require('account_report.ReportWidget');
var framework = require('web.framework');
var crash_manager = require('web.crash_manager');

var QWeb = core.qweb;

var account_report_ledger = Widget.extend(ControlPanelMixin, {
    // Stores all the parameters of the action.
    init: function(parent, action) {
        this.actionManager = parent;
        this.given_context = {};
        if (action.context.data) {
            this.given_context = action.context.data;
        }
        return this._super.apply(this, arguments);
    },
    willStart: function() {
        return this.get_html();
    },
    set_html: function() {
        var self = this;
        var def = $.when();
        if (!this.report_widget) {
            this.report_widget = new ReportWidget(this, this.given_context);
            def = this.report_widget.appendTo(this.$el);
        }
        def.then(function () {
            self.report_widget.$el.html(self.html);
        });
    },
    start: function() {
        this.set_html();
        return this._super();
    },
    // Fetches the html and is previous report.context if any, else create it
    get_html: function() {
        var self = this;
        var defs = [];
        return this._rpc({
                model: 'account.report.ledger',
                method: 'get_html',
                args: [self.given_context],
            })
            .then(function (result) {
                self.html = result.html;
                self.renderButtons();
                defs.push(self.update_cp());
                return $.when.apply($, defs);
            });
    },
    // Updates the control panel and render the elements that have yet to be rendered
    update_cp: function() {
        if (!this.$buttons) {
            this.renderButtons();
        }
        var status = {
            breadcrumbs: this.actionManager.get_breadcrumbs(),
            cp_content: {$buttons: this.$buttons},
        };
        return this.update_control_panel(status);
    },
    renderButtons: function() {
        var self = this;
        this.$buttons = $(QWeb.render("accountReport.buttons", {}));
        // pdf output
        this.$buttons.bind('click', function () {
            var form = $(self.$el[0]).find('table').data('form');
            return self.do_action({
                type: 'ir.actions.report',
                report_name: form['report_name'],
                report_file: form['report_name'],
                report_type: this.getAttribute('report_type'),
                name: 'Report',
                context: {landscape: true,
                          active_model: form['active_model'],
                          active_ids: [form['active_id']]},
                data: {form: form}
            });
        });
        return this.$buttons;
    },
    do_show: function() {
        this._super();
        this.update_cp();
    },
});

core.action_registry.add("account_report_ledger", account_report_ledger);
return account_report_ledger;
});
