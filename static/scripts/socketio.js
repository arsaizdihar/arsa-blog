document.addEventListener('DOMContentLoaded', () => {

    // Connect to websocket
    var socket = io();

    // Retrieve username
    const username = document.querySelector('#get-username').innerHTML;

    // Set default room
    let room_id = document.querySelector('#first_room_id').value;
    joinRoom(document.querySelector('#first_room_id').value);

    // Send messages
    document.querySelector('#send_message').onclick = () => {
        socket.emit('incoming-msg', {'msg': document.querySelector('#user_message').value,
            'username': username, 'room_id': room_id});

        document.querySelector('#user_message').value = '';
    };

    // Display all incoming messages
    socket.on('message', data => {
        // Display current message
        if (data.msg) {
            const p = document.createElement('p');
            const span_username = document.createElement('span');
            const span_timestamp = document.createElement('span');
            const br = document.createElement('br')
            // Display user's own message
            if (data.username == username) {
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
            // Display other users' messages
            else if (typeof data.username !== 'undefined') {
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
            // Display system message
            else {
                printSysMsg(data.msg);
            }


        }
        scrollDownChatWindow();
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
            else {
                if (chat.username == "Server") {
                    printSysMsg(chat.msg)
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
            scrollDownChatWindow();
        }
    });

    // Select a room
    document.querySelectorAll('.select-room').forEach(p => {
        p.onclick = () => {
            let newRoom = p.id
            // Check if user already in the room
            if (newRoom === room_id) {
                msg = `You are already in ${room_id} room.`;
                printSysMsg(msg);
            } else {
                leaveRoom(room_id);
                joinRoom(newRoom);
                room_id = newRoom;
            }
        };
    });

    // Logout from chat
    document.querySelector("#logout-btn").onclick = () => {
        leaveRoom(room_id);
    };

    // Trigger 'leave' event if user was previously on a room
    function leaveRoom(room_id) {
        socket.emit('leave', {'username': username, 'room_id': room_id});
        document.querySelectorAll('.select-room').forEach(p => {
            p.style.color = "black";
        });
    }

    // Trigger 'join' event
    function joinRoom(room_id) {
        // Join room
        socket.emit('join', {'username': username, 'room_id': room_id});

        // Highlight selected room
        document.querySelector('#' + CSS.escape(room_id)).style.color = "#ffc107";
        document.querySelector('#' + CSS.escape(room_id)).style.backgroundColor = "white";

        // Clear message area
        document.querySelector('#display-message-section').innerHTML = '';

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
