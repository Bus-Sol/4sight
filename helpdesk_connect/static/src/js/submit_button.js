    console.log( "ready!");

    $(document).ready(function() {

        $('.oc_btn_create').on('click', function (e) {
        e.stopPropagation();
        e.preventDefault();
        var email = $('input[type="email"]').val();
        btn = $(e.target);
        if (email) {
            inviteUser(email);
            }
        });


        function inviteUser(email) {

        $.ajax({
            type: 'POST',
            url: '/portal/check_user',
            data: JSON.stringify ({"params": {'email': email}}),
            success: function(data) {
                if (!('error' in data.result )) {
                    setTimeout(function() {
                        $('.success_send_mail').removeClass('d-none');
                        $('input[type="email"]').val('');
                        $('.success_send_mail').text('A Link was send to your email');
                        $('.oc_btn_create').removeAttr('disabled');
                     },2000);
                    return;
                 }
                 else {
                    setTimeout(function() {
                        $('.error_send_mail').removeClass('d-none');
                        $('input[type="email"]').val('');
                        $('.error_send_mail').text('Something went wrong!');
                        $('.oc_btn_create').removeAttr('disabled');
                        }, 2000);
                        return;
                    }
                 },
            error: function(data) { console.log( "Error"); },
            contentType: "application/json",
            dataType: 'json'
        });
        $('.oc_btn_create').attr('disabled', 'disabled');
       }
})