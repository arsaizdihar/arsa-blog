$(document).ready(function(){
 $('#image-upload').change(function(event) {
        console.log('heiawhuihwfa')
        var form_data = new FormData($('#upload-form')[0]);
        console.log(form_data)
        console.log(room_id)
        $.ajax({
            type: 'POST',
            url: '/chat/upload_ajax',
            data: form_data,
            headers: {
                "room_id": room_id,
            },
            contentType: false,
            cache: false,
            processData: false,
            success: function(data) {
                console.log('Success!');
            },
        });
    });
});