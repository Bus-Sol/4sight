    console.log( "ready!");

    $(document).ready(function() {

        $('.oc_btn_create').on('click', function (e) {
        e.stopPropagation();
        e.preventDefault();
        var email = $('input[type="email"]').val();
        btn = $(e.target);
        if (email) {
            $('.oc_btn_create').attr('disabled', 'disabled');
            $('.oc_btn_create')[0].style['opacity'] = '0.65';
            if (!($('.success_send_mail').hasClass('d-none'))){
                $('.success_send_mail').addClass('d-none');
            }
            if (!($('.error_send_mail').hasClass('d-none'))){
                $('.error_send_mail').addClass('d-none');
            }
            inviteUser(email)
                .then((data) => {
                console.log(data)
                if (!('error' in data.result )) {
                    $('.success_send_mail').removeClass('d-none');
                    $('input[type="email"]').val('');
                    $('.success_send_mail').text('A link was sent to your mailbox');
                    $('.oc_btn_create').removeAttr('disabled');
                    console.log($('.oc_btn_create'));
                    $('.oc_btn_create')[0].style.removeProperty('opacity');
                }
                else {
                    $('.error_send_mail').removeClass('d-none');
                    $('input[type="email"]').val('');
                    $('.error_send_mail').text(data.result['error']);
                    $('.oc_btn_create').removeAttr('disabled');
                    $('.oc_btn_create')[0].style.removeProperty('opacity');
                }
                })
                .catch((error) => {
                $('.error_send_mail').text('Something went wrong!');
                })
    }
    });

        function inviteUser(email) {
            return new Promise((resolve, reject) => {
                $.ajax({
                  url: '/portal/check_user',
                  type: 'POST',
                  contentType: "application/json",
                  dataType: 'json',
                  data: JSON.stringify ({"params": {'email': email}}),
                  success: function (data) {
                    resolve(data)
                  },
                  error: function (error) {
                    reject(error)
                  },
                })
              })
       }
})