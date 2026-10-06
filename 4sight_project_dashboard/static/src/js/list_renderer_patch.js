/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";

patch(ListRenderer.prototype, {
    getColumnClass(column) {
        const className = super.getColumnClass(...arguments);
        const fieldClassName = column.attrs && column.attrs.class;
        return fieldClassName ? `${className} ${fieldClassName}` : className;
    },
});
