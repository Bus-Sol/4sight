odoo.define('helpdesk_connect.submit_button', function (require) {
'use strict';

var publicWidget = require('web.public.widget');
var ajax = require('web.ajax');
const {_t, qweb} = require('web.core');
var rpc = require('web.rpc');

publicWidget.registry.ButtonSubmit = publicWidget.Widget.extend({
    selector: '.oc_create_instance',
    events: {
        'click .oc_btn_create': 'onClickBtn',
    },


    onClickBtn: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        var self = this;
        var email = this.$('input[type="email"]').val();
        if (email) {
                var $button = $(ev.currentTarget);
                return this.inviteUser(email);
            }

    },

    inviteUser: function (email) {
        var self = this;
        rpc.query({
            route: "/portal/check_user",
            params: {
                'email': email,
            },
        }).then(function (data) {

            if (data['sent']) {
                $('.success_send_mail').removeClass('d-none');
                $('input[type="email"]').val('');
                $('.success_send_mail').text('A Link was send to your email');
            }
            if(data['error']) {
                $('.error_send_mail').removeClass('d-none');
                $('.error_send_mail').text('Something went wrong!');
            }
            $('.oc_btn_create').removeAttr('disabled');
        });
        $('.oc_btn_create').attr('disabled', 'disabled');
       },
});
});