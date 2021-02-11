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
    members = new Bloodhound({
            datumTokenizer: Bloodhound.tokenizers.whitespace,
            queryTokenizer: Bloodhound.tokenizers.whitespace,
            local: member_name
        });


    // Initializing the typeahead
    $('.typeahead').typeahead({
        highlight: true, /* Enable substring highlighting */
        minLength: 3 /* Specify minimum characters required for showing suggestions */
    },
    {
        name: 'members',
        source: members
    });
});
function newTypeahead(member) {

        if (members){
            members.clear();
            members.local = member;
            members.initialize(true);
        }
    }