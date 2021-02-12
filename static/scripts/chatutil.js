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

    function hideChatBar() {
        if($(window).innerWidth() <= 567) {
            $('#show-sidebar-button').click(function() {
                if ($('#sidebar').hasClass("view-sidebar")){
                    $('#rightside-pannel').hide();
                }
                else {
                    $('#rightside-pannel').show();
                    $('#user_message').focus();
                }
                if ($('#navbarSupportedContent').is(":visible")){
                    $('.navbar-toggler').click();
                    $('#rightside-pannel').hide();
                }
            });
            $('#sidebar p').each(function() {
                $(this).click(function() {
                    $('#sidebar').removeClass('view-sidebar');
                    $('#rightside-pannel').show();
                    $('#rightside-pannel').scrollTop($('#rightside-pannel').height());
                    $('#user_message').focus();
                });
            });
        }
    }

    hideChatBar();

    $(window).resize(function() {
        hideChatBar();
    });

    $('.navbar-toggler').click(function(){
        console.log($('#sidebar').hasClass("view-sidebar"))
        if (($('#sidebar').hasClass("view-sidebar"))){
            $('#rightside-pannel').show();
        }
        $('#rightside-pannel').scrollTop($('#rightside-pannel').height());
        if ($('#sidebar').hasClass("view-sidebar") && ($(this).hasClass("collapsed"))){
            $('#sidebar').removeClass('view-sidebar');
        }
    });
});
function newTypeahead(member) {

        if (members){
            members.clear();
            members.local = member;
            members.initialize(true);
        }
    }