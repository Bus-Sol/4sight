/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { SignatureDialog } from "@web/core/signature/signature_dialog";
import { useService } from "@web/core/utils/hooks";
import { url } from "@web/core/utils/urls";
import { isBinarySize } from "@web/core/utils/binary";
import { fileTypeMagicWordMap, imageCacheKey } from "@web/views/fields/image/image_field";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { NameAndSignature } from "@web/core/signature/name_and_signature";
import { Component, useState } from "@odoo/owl";

const placeholder = "/web/static/img/placeholder.png";

export class SignatureField extends Component {
    static template = "odoo_timestead.SignatureField";
    static props = {
        ...standardFieldProps,
        defaultFont: { type: String },
        fullName: { type: String, optional: true },
        height: { type: Number, optional: true },
        previewImage: { type: String, optional: true },
        width: { type: Number, optional: true },
    };

    setup() {
        this.displaySignatureRatio = 3;

        this.dialogService = useService("dialog");
        this.state = useState({
            isValid: true,
        });
    }

    get rawCacheKey() {
        return this.props.record.data.write_date;
    }

    get getUrl() {
        const { name, previewImage, record } = this.props;
        if (this.state.isValid && this.value) {
            if (isBinarySize(this.value)) {
                return url("/web/image", {
                    model: record.resModel,
                    id: record.resId,
                    field: previewImage || name,
                    unique: imageCacheKey(this.rawCacheKey),
                });
            } else {
                // Use magic-word technique for detecting image type
                const magic = fileTypeMagicWordMap[this.value[0]] || "png";
                return `data:image/${magic};base64,${this.props.record.data[this.props.name]}`;
            }
        }
        return placeholder;
    }

    get sizeStyle() {
        let { width, height } = this.props;

        if (!this.value) {
            if (width && height) {
                width = Math.min(width, this.displaySignatureRatio * height);
                height = width / this.displaySignatureRatio;
            } else if (width) {
                height = width / this.displaySignatureRatio;
            } else if (height) {
                width = height * this.displaySignatureRatio;
            }
        }

        let style = "";
        if (width) {
            style += `width:${width}px; max-width:${width}px;`;
        }
        if (height) {
            style += `height:${height}px; max-height:${height}px;`;
        }
        return style;
    }

    get value() {
        return this.props.record.data[this.props.name];
    }

    onClickSignature() {
        console.log("\n +++++++++++ 88 ++++++++++++")
        if (!this.props.readonly) {
            const nameAndSignatureProps = {
                displaySignatureRatio: 3,
                signatureType: "signature",
                noInputName: true,
            };
            const { fullName, record } = this.props;
            let defaultName = "";
            if (fullName) {
                let signName;
                const fullNameData = record.data[fullName];
                if (record.fields[fullName].type === "many2one") {
                    // If m2o is empty, it will have falsy value in recordData
                    signName = fullNameData && fullNameData[1];
                } else {
                    signName = fullNameData;
                }
                defaultName = signName === "" ? undefined : signName;
            }

            nameAndSignatureProps.defaultFont = this.props.defaultFont;

            const dialogProps = {
                defaultName,
                nameAndSignatureProps,
                uploadSignature: (signature) => this.uploadSignature(signature),
            };
            this.dialogService.add(SignatureDialog, dialogProps);
        }
    }

    onLoadFailed() {
        this.state.isValid = false;
        this.notification.add(_t("Could not display the selected image"), {
            type: "danger",
        });
    }

    /**
     * Upload the signature image if valid and close the dialog.
     *
     * @private
     */
    uploadSignature({ signatureImage }) {
        return this.props.record.update({ [this.props.name]: signatureImage[1] || false });
    }

    get nameAndSignatureProps() {
        return {
            ...this.props.nameAndSignatureProps,
            signature: this.signature,
        };
    }
}

export const signatureField = {
    component: NameAndSignature,
    fieldDependencies: [{ name: "write_date", type: "datetime" }],
    supportedOptions: [
        {
            label: _t("Prefill with"),
            name: "full_name",
            type: "field",
            availableTypes: ["char", "many2one"],
            help: _t("The selected field will be used to pre-fill the signature"),
        },
        {
            label: _t("Default font"),
            name: "default_font",
            type: "string",
        },
        {
            label: _t("Size"),
            name: "size",
            type: "selection",
            choices: [
                { label: _t("Small"), value: "[0,90]" },
                { label: _t("Medium"), value: "[0,180]" },
                { label: _t("Large"), value: "[0,270]" },
            ],
        },
        {
            label: _t("Preview image field"),
            name: "preview_image",
            type: "field",
            availableTypes: ["binary"],
        },
    ],
    extractProps: ({ attrs, options }) => ({
        defaultFont: options.default_font || "",
        fullName: options.full_name,
        height: options.size ? options.size[1] || undefined : attrs.height,
        previewImage: options.preview_image,
        width: options.size ? options.size[0] || undefined : attrs.width,
    }),
};

registry.category("fields").add("custom_signature", signatureField);





//odoo.define('odoo_timestead.digital_sign', function(require) {
//    "use strict";
//
//    var core = require('web.core');
//    var BasicFields= require('web.basic_fields');
//    var FormController = require('web.FormController');
//    var Registry = require('web.field_registry');
//    var utils = require('web.utils');
//    var session = require('web.session');
//    var field_utils = require('web.field_utils');
//
//    var _t = core._t;
//    var QWeb = core.qweb;
//
//    var FieldSignature = BasicFields.FieldBinaryImage.extend({
//        template: 'FieldSignature',
//        events: _.extend({}, BasicFields.FieldBinaryImage.prototype.events, {
//            'click .save_sign': '_on_save_sign',
//            'click #sign_clean': '_on_clear_sign'
//        }),
//        jsLibs: ['/odoo_timestead/static/lib/jSignature/jSignatureCustom.js'],
//        placeholder: "/web/static/src/img/placeholder.png",
//        init: function() {
//            this._super.apply(this, arguments);
//            this.sign_options = {
//                'decor-color': '#D1D0CE',
//                'color': '#000',
//                'background-color': '#fff',
//                'height': '150',
//                'width': '550'
//            };
//            this.empty_sign = [];
//        },
//        start: function() {
//            var self = this;
//            this.$(".signature").jSignature("init", this.sign_options);
//            this.$(".signature").attr({
//                "tabindex": "0",
//                'height': "100"
//            });
//            this.empty_sign = this.$(".signature").jSignature("getData", 'image');
//            self._render();
//        },
//        _on_clear_sign: function() {
//            this.$(".signature > canvas").remove();
//            this.$('> img').remove();
//            this.$(".signature").attr("tabindex", "0");
//            var sign_options = {
//                'decor-color': '#D1D0CE',
//                'color': '#000',
//                'background-color': '#fff',
//                'height': '150',
//                'width': '550',
//                'clear': true
//            };
//            this.$(".signature").jSignature(sign_options);
//            this.$(".signature").focus();
//            this._setValue(false);
//        },
//        _on_save_sign: function(value_) {
//            var self = this;
//            this.$('> img').remove();
//            var signature = this.$(".signature").jSignature("getData", 'image');
//            var is_empty = signature ?
//                self.empty_sign[1] === signature[1] :
//                false;
//            if (!is_empty && typeof signature !== "undefined" && signature[1]) {
//                this._setValue(signature[1]);
//            }
//        },
//        _render: function() {
//            var self = this;
//            var url = this.placeholder;
//            if (this.value && !utils.is_bin_size(this.value)) {
//                url = 'data:image/png;base64,' + this.value;
//            } else if (this.value) {
//                url = session.url('/web/image', {
//                    model: this.model,
//                    id: JSON.stringify(this.res_id),
//                    field: this.nodeOptions.preview_image || this.name,
//                    unique: field_utils.format.datetime(this.recordData.__last_update).replace(/[^0-9]/g, ''),
//                });
//            } else {
//                url = this.placeholder;
//            }
//            if (this.mode === "readonly") {
//                var $img = $(QWeb.render("FieldBinaryImage-img", {
//                    widget: self,
//                    url: url
//                }));
//                this.$('> img').remove();
//                this.$(".signature").hide();
//                this.$el.prepend($img);
//                $img.on('error', function() {
//                    self.on_clear();
//                    $img.attr('src', self.placeholder);
//                    self.do_warn(_t("Image"), _t("Could not display the selected image."));
//                });
//            } else if (this.mode === "edit") {
//                this.$('> img').remove();
//                if (this.value) {
//                    var field_name = this.nodeOptions.preview_image ?
//                        this.nodeOptions.preview_image :
//                        this.name;
//                    self._rpc({
//                        model: this.model,
//                        method: 'read',
//                        args: [this.res_id, [field_name]]
//                    }).then(function(data) {
//                        if (data) {
//                            var field_desc = _.values(_.pick(data[0], field_name));
//                            self.$(".signature").jSignature("clear");
//                            self.$(".signature").jSignature("setData", 'data:image/png;base64,' + field_desc[0]);
//                        }
//                    });
//                } else {
//                    this.$('> img').remove();
//                    this.$('.signature > canvas').remove();
//                    var sign_options = {
//                        'decor-color': '#D1D0CE',
//                        'color': '#000',
//                        'background-color': '#fff',
//                        'height': '150',
//                        'width': '550'
//                    };
//                    this.$(".signature").jSignature("init", sign_options);
//                }
//            } else if (this.mode === 'create') {
//                this.$('> img').remove();
//                this.$('> canvas').remove();
//                if (!this.value) {
//                    this.$(".signature").empty().jSignature("init", {
//                        'decor-color': '#D1D0CE',
//                        'color': '#000',
//                        'background-color': '#fff',
//                        'height': '150',
//                        'width': '550'
//                    });
//                }
//            }
//        }
//    });
//
//    FormController.include({
//        saveRecord: function() {
//            this.$('.save_sign').click();
//            return this._super.apply(this, arguments);
//        }
//    });
//
//    Registry.add('signature', FieldSignature);
//});
