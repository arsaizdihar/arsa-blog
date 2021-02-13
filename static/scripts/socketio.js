document.addEventListener('DOMContentLoaded', () => {

    // Connect to websocket
    var socket = io();

    // Retrieve username
    const username = document.querySelector('#get-username').innerHTML;

    // Send messages
    document.querySelector('#send_message').onclick = () => {
        var message = document.querySelector('#user_message');
        if (String(message.value).trim()){
            socket.emit('incoming-msg', {'msg': message.value,
                'username': username, 'room_id': room_id});
        }
        message.value = '';
    };

    // Display all incoming messages
    socket.on('message', data => {
        // Display current message
        if (data.msg) {
            const p = document.createElement('p');
            const span_username = document.createElement('span');
            const span_timestamp = document.createElement('span');
            const br = document.createElement('br');

            // Display user's own message
            if (data.username == username) {
                if (data.is_image) {
                    const img = document.createElement("IMG");
                    const anchor = document.createElement("a");
                    p.setAttribute("class", "my-msg");

                    // Username
                    span_username.setAttribute("class", "my-username");
                    span_username.innerText = data.username;

                    span_timestamp.setAttribute("class", "timestamp");
                    span_timestamp.innerText = data.time_stamp;


                    img.setAttribute("src", data.msg);
                    img.setAttribute("class", "img-msg");

                    anchor.setAttribute("href", data.msg);
                    anchor.setAttribute("target", "_blank");

                    anchor.innerHTML += img.outerHTML;

                    p.innerHTML += span_username.outerHTML + br.outerHTML + anchor.outerHTML + br.outerHTML + span_timestamp.outerHTML;

                    //Append
                    document.querySelector('#display-message-section').append(p);
                }
                else {
                    p.setAttribute("class", "my-msg");

                    // Username
                    span_username.setAttribute("class", "my-username");
                    span_username.innerText = data.username;

                    // Timestamp
                    span_timestamp.setAttribute("class", "timestamp");
                    span_timestamp.innerText = data.time_stamp;

                    // HTML to append
                    p.innerHTML += span_username.outerHTML + br.outerHTML + data.msg + br.outerHTML + span_timestamp.outerHTML

                    //Append
                    document.querySelector('#display-message-section').append(p);
                }
            }
            // Display other users' messages
            else if (typeof data.username !== 'undefined') {
                if (data.is_image) {
                    const img = document.createElement("IMG");
                    const anchor = document.createElement("a");
                    p.setAttribute("class", "others-msg");

                    // Username
                    span_username.setAttribute("class", "other-username");
                    span_username.innerText = data.username;

                    span_timestamp.setAttribute("class", "timestamp");
                    span_timestamp.innerText = data.time_stamp;


                    img.setAttribute("src", data.msg);
                    img.setAttribute("class", "img-msg");

                    anchor.setAttribute("href", data.msg);
                    anchor.setAttribute("target", "_blank");

                    anchor.innerHTML += img.outerHTML;

                    p.innerHTML += span_username.outerHTML + br.outerHTML + anchor.outerHTML + br.outerHTML + span_timestamp.outerHTML;

                    //Append
                    document.querySelector('#display-message-section').append(p);
                }
                else {
                    p.setAttribute("class", "others-msg");

                    // Username
                    span_username.setAttribute("class", "other-username");
                    span_username.innerText = data.username;

                    // Timestamp
                    span_timestamp.setAttribute("class", "timestamp");
                    span_timestamp.innerText = data.time_stamp;

                    // HTML to append
                    p.innerHTML += span_username.outerHTML + br.outerHTML + data.msg + br.outerHTML + span_timestamp.outerHTML;

                    //Append
                    document.querySelector('#display-message-section').append(p);
                }
            }
            // Display system message
            else {
                printSysMsg(data.msg);
            }


        }
        scrollDownChatWindow();
        socket.emit('read', {'user_id': user_id, 'username': username, 'room_id': room_id});
    });

    socket.on('show_history', data => {
        chats = data.chats;
        const span_username = document.createElement('span');
        const span_timestamp = document.createElement('span');
        const br = document.createElement('br')
        for (var i = 0; i < chats.length; i++){
            const p = document.createElement('p');
            chat = chats[i]
            if (chat.is_user) {
                if (chat.is_image) {
                    const img = document.createElement("IMG");
                    const anchor = document.createElement("a");
                    p.setAttribute("class", "my-msg");

                    // Username
                    span_username.setAttribute("class", "my-username");
                    span_username.innerText = chat.username;

                    span_timestamp.setAttribute("class", "timestamp");
                    span_timestamp.innerText = chat.time;


                    img.setAttribute("src", chat.msg);
                    img.setAttribute("class", "img-msg");

                    anchor.setAttribute("href", chat.msg);
                    anchor.setAttribute("target", "_blank");

                    anchor.innerHTML += img.outerHTML;

                    p.innerHTML += span_username.outerHTML + br.outerHTML + anchor.outerHTML + br.outerHTML + span_timestamp.outerHTML;

                    //Append
                    document.querySelector('#display-message-section').append(p);
                }
                else {
                    p.setAttribute("class", "my-msg");
                    // Username
                    span_username.setAttribute("class", "my-username");
                    span_username.innerText = chat.username;

                    // Timestamp
                    span_timestamp.setAttribute("class", "timestamp");
                    span_timestamp.innerText = chat.time;

                    // HTML to append
                    p.innerHTML += span_username.outerHTML + br.outerHTML + chat.msg + br.outerHTML + span_timestamp.outerHTML

                    //Append
                    document.querySelector('#display-message-section').append(p);
                }
            }
            else {
                if (chat.username == "Server") {
                    printSysMsg(chat.msg)
                }
                else {
                    if (chat.is_image) {
                        const img = document.createElement("IMG");
                        const anchor = document.createElement("a");
                        p.setAttribute("class", "others-msg");

                        // Username
                        span_username.setAttribute("class", "other-username");
                        span_username.innerText = chat.username;

                        span_timestamp.setAttribute("class", "timestamp");
                        span_timestamp.innerText = chat.time;


                        img.setAttribute("src", chat.msg);
                        img.setAttribute("class", "img-msg");

                        anchor.setAttribute("href", chat.msg);
                        anchor.setAttribute("target", "_blank");

                        anchor.innerHTML += img.outerHTML;

                        p.innerHTML += span_username.outerHTML + br.outerHTML + anchor.outerHTML + br.outerHTML + span_timestamp.outerHTML;

                        //Append
                        document.querySelector('#display-message-section').append(p);
                    }
                    else {
                        p.setAttribute("class", "others-msg");

                        // Username
                        span_username.setAttribute("class", "other-username");
                        span_username.innerText = chat.username;

                        // Timestamp
                        span_timestamp.setAttribute("class", "timestamp");
                        span_timestamp.innerText = chat.time;

                        // HTML to append
                        p.innerHTML += span_username.outerHTML + br.outerHTML + chat.msg + br.outerHTML + span_timestamp.outerHTML;

                        //Append
                        document.querySelector('#display-message-section').append(p);
                    }
                }
            }
            scrollDownChatWindow();
        }
    });

    socket.on('notify_chat', data => {
        var room = document.querySelector("#p"+data.room_id);
        if (room){
            if (!room.style.backgroundColor){
                room.classList.add('room-unread');
                var span = room.children[0];
                var read = parseInt(span.innerText);
                if (read) {
                    read += 1;
                }
                else {
                    read = 1;
                }
                span.innerText = read;
            }

            var title = document.querySelector('#sidebar-title');
            var sidebar = document.querySelector('#sidebar-scroll');
            var elements = sidebar.children;
            var next_inner = title.outerHTML + room.outerHTML;
            for (var i = 0; i < elements.length; i++) {
                var element = elements[i];
                if( element != title && element != room){
                    next_inner += element.outerHTML;
                }
            }
            sidebar.innerHTML = next_inner;
            document.querySelectorAll('.select-room').forEach(p => {
                p.onclick = () => {
                    pClick(p);
                };
            });
        }
    });

    // Select a room
    document.querySelectorAll('.select-room').forEach(p => {
        p.onclick = () => {
            pClick(p);
        };
    });

    function pClick(p) {
        let newRoom = p.id.substring(1);
        console.log(newRoom);
        span = p.children[1];
        span.innerText = "";
        // Check if user already in the room
        if (newRoom === room_id) {
            msg = `You are already in ${p.innerHTML} room.`;
            printSysMsg(msg);
        } else {
            leaveRoom(room_id);
            joinRoom(newRoom);
            room_id = newRoom;
        }
    }

    // Logout from chat
    document.querySelector("#logout-btn").onclick = () => {
        leaveRoom(room_id);
    };

    document.querySelector("#image-btn").onclick = () => {
        document.querySelector("#image-upload").click();
    };


    // Trigger 'leave' event if user was previously on a room
    function leaveRoom(room_id) {
        socket.emit('leave', {'username': username, 'room_id': room_id});
        document.querySelectorAll('.select-room').forEach(p => {
            p.style.backgroundColor = null;
        });
        document.querySelector('#display-message-section').innerHTML = "";
    }

    // Trigger 'join' event
    function joinRoom(room_id) {
        document.querySelector("#input-area").removeAttribute("hidden");
        // Join room
        socket.emit('join', {'username': username, 'room_id': room_id});
        document.querySelector("#p"+room_id).classList.remove("room-unread");

        fetch('/chat/group-member/' + room_id).then(function(response) {

            response.json().then(function(data) {
                member_name = [];
                for(let user of data.members) {
                    member_name.push(user.name);
                }
                console.log(member_name)
                newTypeahead(member_name);
            });
        });



        // Highlight selected room
//        document.querySelector('#' + CSS.escape(room_id)).style.color = "#ffc107";
        document.querySelector('#p' + CSS.escape(room_id)).style.backgroundColor = "#323739";

        // Clear message area
        document.querySelector('#user_message').value = '';

        // Autofocus on text box
        document.querySelector("#user_message").focus();
    }

    // Scroll chat window down
    function scrollDownChatWindow() {
        const chatWindow = document.querySelector("#display-message-section");
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    // Print system messages
    function printSysMsg(msg) {
        const p = document.createElement('p');
        p.setAttribute("class", "system-msg");
        p.innerHTML = msg;
        document.querySelector('#display-message-section').append(p);
        scrollDownChatWindow()

        // Autofocus on text box
        document.querySelector("#user_message").focus();
    }
});
