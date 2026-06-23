/** @odoo-module **/

import { Component, onMounted, onWillStart, onWillUnmount, useRef, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { FieldPicker } from "./field_picker";
import { buildEditor } from "./gjs_setup";

export class ReportBuilderEditor extends Component {
    static template = "report_builder.Editor";
    static props = { "*": true };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.dialog = useService("dialog");

        this.canvasRef = useRef("canvas");
        this.blocksRef = useRef("blocks");
        this.traitsRef = useRef("traits");
        this.stylesRef = useRef("styles");
        this.layersRef = useRef("layers");

        this.state = useState({ name: "", model: "", loading: true, busy: false });
        this.templateId = this.props.action.context.template_id;

        onWillStart(async () => {
            this.data = await this.orm.call(
                "report.builder.template",
                "load_editor_data",
                [this.templateId]
            );
            this.state.name = this.data.name;
            this.state.model = this.data.model_label || this.data.model;
            this.picker = new FieldPicker(this.orm);
            this.picker.cache[this.data.model] = this.data.fields;
        });

        onMounted(() => {
            this.editor = buildEditor(this.canvasRef.el, {
                picker: this.picker,
                rootModel: this.data.model,
                blocksEl: this.blocksRef.el,
                traitsEl: this.traitsRef.el,
                stylesEl: this.stylesRef.el,
                layersEl: this.layersRef.el,
            });
            if (this.data.gjs_data) {
                try {
                    this.editor.loadProjectData(JSON.parse(this.data.gjs_data));
                } catch (e) {
                    this.editor.setComponents(this.data.body_html || "");
                }
            } else {
                this.editor.setComponents(this.data.body_html || "");
            }
            this.state.loading = false;
        });

        onWillUnmount(() => {
            if (this.editor) {
                this.editor.destroy();
            }
        });
    }

    _design() {
        const css = this.editor.getCss() || "";
        const html = this.editor.getHtml() || "";
        return {
            body: css ? `<style>${css}</style>${html}` : html,
            project: JSON.stringify(this.editor.getProjectData()),
        };
    }

    async _save() {
        const d = this._design();
        await this.orm.call("report.builder.template", "save_design", [
            this.templateId,
            d.body,
            d.project,
        ]);
    }

    async onSave() {
        this.state.busy = true;
        try {
            await this._save();
            this.notification.add(_t("Design saved."), { type: "success" });
        } finally {
            this.state.busy = false;
        }
    }

    async onPublish() {
        this.state.busy = true;
        try {
            await this._save();
            await this.orm.call("report.builder.template", "action_publish", [
                this.templateId,
            ]);
            this.notification.add(_t("Report published."), { type: "success" });
        } finally {
            this.state.busy = false;
        }
    }

    async onPreview() {
        this.state.busy = true;
        try {
            await this._save();
            await this.orm.call("report.builder.template", "action_publish", [
                this.templateId,
            ]);
            const action = await this.orm.call(
                "report.builder.template",
                "action_print_preview",
                [this.templateId]
            );
            if (action) {
                await this.action.doAction(action);
            }
        } finally {
            this.state.busy = false;
        }
    }

    onBack() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "report.builder.template",
            res_id: this.templateId,
            views: [[false, "form"]],
            target: "main",
        });
    }
}

registry.category("actions").add("report_builder.editor", ReportBuilderEditor);
