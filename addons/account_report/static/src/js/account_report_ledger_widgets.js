odoo.define('account_report.ReportWidget', function (require) {
'use strict';

var core = require('web.core');
var Widget = require('web.Widget');

var QWeb = core.qweb;

var _t = core._t;

var ReportWidget = Widget.extend({
    events: {
        'click span.o_account_report_foldable': 'fold',
        'click span.o_account_report_unfoldable': 'unfold',
        'click .o_account_report_web_action': 'boundLink',
    },
    init: function(parent) {
        this._super.apply(this, arguments);
    },
    start: function() {
        QWeb.add_template("/account_report/static/src/xml/account_report_ledger_line.xml");
        return this._super.apply(this, arguments);
    },
    boundLink: function(e) {
        return this.do_action({
            type: 'ir.actions.act_window',
            res_model: $(e.target).data('res-model'),
            res_id: $(e.target).data('active-id'),
            views: [[false, 'form']],
            target: 'current'
        });
    },
    removeLine: function(element) {
        var self = this;
        var el, $el;
        var rec_id = element.data('id');
        var $stockEl = element.nextAll('tr[data-parent_id=' + rec_id + ']')
        for (el in $stockEl) {
            $el = $($stockEl[el]).find(".o_account_report_domain_line_0, .o_account_report_domain_line_1");
            if ($el.length === 0) {
                break;
            }
            else {
                var $nextEls = $($el[0]).parents("tr");
                self.removeLine($nextEls);
                $nextEls.remove();
            }
            $el.remove();
        }
        return true;
    },
    fold: function(e) {
        this.removeLine($(e.target).parents('tr'));
        var active_id = $(e.target).parents('tr').find('td.o_account_report_foldable').data('id');
        $(e.target).parents('tr').find('td.o_account_report_foldable').attr('class', 'o_account_report_unfoldable ' + active_id); // Change the class, rendering, and remove line from model
        $(e.target).parents('tr').find('span.o_account_report_foldable').replaceWith(QWeb.render("unfoldable", {lineId: active_id}));
        $(e.target).parents('tr').toggleClass('o_account_report_unfolded');
    },
    unfold: function(e) {
        var $CurretElement;
        $CurretElement = $(e.target).parents('tr').find('td.o_account_report_unfoldable');
        var active_id = $CurretElement.data('id');
        var active_model_name = $CurretElement.data('model');
        var active_model_id = $CurretElement.data('model_id');
        var row_level = $CurretElement.data('level');
        var form = $CurretElement.parents('table').data('form');
        var $cursor = $(e.target).parents('tr');
        this._rpc({
                model: 'account.report.ledger',
                method: 'get_lines',
                args: [parseInt(active_id, 10)],
                kwargs: {
                    'model_id': active_model_id,
                    'model_name': active_model_name,
                    'form': form,
                    'level': parseInt(row_level) + 30 || 1
                },
            })
            .then(function (lines) {// After loading the line
                var line;
                for (line in lines) { // Render each line
                    $cursor.after(QWeb.render("report_ledger_line", {l: lines[line], decimal_places: form['decimal_places']}));
                    $cursor = $cursor.next();
                }
            });
        $CurretElement.attr('class', 'o_account_report_foldable ' + active_id); // Change the class, and rendering of the unfolded line
        $(e.target).parents('tr').find('span.o_account_report_unfoldable').replaceWith(QWeb.render("foldable", {lineId: active_id}));
        $(e.target).parents('tr').toggleClass('o_account_report_unfolded');
    },

});

return ReportWidget;

});
