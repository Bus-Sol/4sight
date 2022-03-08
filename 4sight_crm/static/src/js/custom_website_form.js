odoo.define('4sight_crm.custom_s_website_form', function (require) {
    'use strict';

    var core = require('web.core');
    var ajax = require('web.ajax');
    var publicWidget = require('web.public.widget');

    var _t = core._t;
    var qweb = core.qweb;

    publicWidget.registry.RetailForm = publicWidget.Widget.extend({

        selector: '.s_website_form form, form.s_website_form',
        events: {
            'change .js_change_district': function (e) {
                var district_id = $(e.currentTarget).val();
                console.log(district_id);
                $(".js_update_area option").remove();
                ajax.post('/data/district/update_area_selection', {
                    district_id: district_id
                }).then(function (result) {
                    let obj = JSON.parse(result);
                    $('.js_update_area').append("<option value=''>Select Area</option>");
                    obj.map(function(k) {
                        $('.js_update_area').append('<option value='+k.id+'>'+k.name+'</option>');
//                        $('.js_update_area').append('<option value={"key":'+k.key+',"id":'+k.id+'}>'+k.name+'</option>)');
                    });
                });
            },
            'click .js_look_for_street': '_onClickSearchStreet',
            'change .js_select_street': function (e) {
                var code = $(e.currentTarget).val();
                var street_name = $('.js_select_street > option:selected').text()
                $('#street').val(street_name);
                $('#postal_code').val(code);
            },
        },

        _onClickSearchStreet: function(e) {

            var name_inserted = $('.js_name_inserted').val();
            var district_key = $('.js_change_district').val();
            var area_key = $('.js_update_area').val();
            $('.js_name_inserted').removeClass('is-invalid');
            $('small').addClass('d-none');
            console.log(name_inserted);
            $(".js_select_street option").remove();
            ajax.post('/data/district/update_street_api', {
                name_inserted: name_inserted,
                district_key: district_key,
                area_key: area_key,
            }).then(function (result) {
                var obj = JSON.parse(result);
                if(obj.includes("error")) {
                    $('.js_name_inserted').addClass('is-invalid');
                    $('small').removeClass('d-none');
                 }
                else if (obj.length ==0) {
                    $('.js_select_street').append("<option value=''>No result</option>");
                }
                else {
                    $('.js_select_street').append("<option value=''>Select Street</option>");
                        obj.map(function(k) {
                            let street = ""
                            let postal = ""
                            if (k.street) { street = k.street}
                            if (k.service) { street = k.service}
                            if (k.description) { street = k.description}
                            if (k.postal_code) { postal = k.postal_code}
                            if (k.postal_address) { postal = k.postal_address.substring(0,4)}

                            $('.js_select_street').append('<option value=' +postal+'>'+street+'</option>');
                        });
                }
            });
        },
    });
    return publicWidget.registry.RetailForm;
    });