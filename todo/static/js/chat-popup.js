$(document).ready(function () {
    var element = $('.floating-chat');
    var myStorage = localStorage;
    var chatIsEmpty = true;
    var roomName = createUUID();

    const socket = new WebSocket(`wss://${window.location.host}/ws/${roomName}/`);

    socket.onopen = function(event) {
        console.log("WebSocket connection opened:", event);
    };

    function updateTypingIndicator() {
        var selfMessagesCount = $('.messages .self').length;
        var otherMessagesCount = $('.messages .other').length;
    
        if (selfMessagesCount !== otherMessagesCount) {
            $('.typing-indicator').show();
        } else {
            $('.typing-indicator').hide();
        }
    }

    socket.onmessage = function(event) {
        var messages = $('.messages');
        const data = JSON.parse(event.data);
        messages.append(data.message);
        messages.scrollTop(messages.prop("scrollHeight"));
        updateTypingIndicator();
    };

    socket.onclose = function(event) {
        console.log('WebSocket connection closed:', event);
    };

    if (!myStorage.getItem('chatID')) {
        myStorage.setItem('chatID', roomName);
    }

    setTimeout(function () {
        element.addClass('enter');
    }, 1000);

    element.click(openElement);

    function openElement() {
        var messages = element.find('.messages');
        var textInput = element.find('.text-box');
        element.find('>i').hide();
        element.addClass('expand');
        element.find('.chat').addClass('enter');
        element.find('.contact').addClass('expand');
        textInput.keydown(onMetaAndEnter).attr("contenteditable", "true").focus();
        element.off('click', openElement);
        element.find('.header button').click(closeElement);
        element.find('#sendMessage').click(sendNewMessage);

        if (chatIsEmpty) {
            // Запрос на получение последних сообщений
            $.ajax({
                url: '/ai/last-message/',
                type: 'GET',
                dataType: 'json',
                success: function (response) {
                    chatIsEmpty = false;
                    roomName = response.room_name

                    for (var i = 0; i < response.history.length; i++) {
                        var message = response.history[i];
                        if (message.question) {
                            messages.append('<li class="self">' + message.question + '</li>');
                        }
                        if (message.answer) {
                            messages.append('<li class="other">' + message.answer + '</li>');
                        }
                    }
                    messages.scrollTop(messages.prop("scrollHeight"));
                },
                error: function () {
                    console.error('Ошибка при получении последних сообщений');
                }
            });
        }
    }

    function sendNewMessage() {
        var userInput = $('.text-box');
        var newMessage = userInput.text().trim();

        if (!newMessage) return;

        var messagesContainer = $('.messages');    

        userInput.text(''); // Clean out old message

        messagesContainer.finish().animate({
            scrollTop: messagesContainer.prop("scrollHeight")
        }, 250);

        // Sending message through WebSocket
        var chat_id = myStorage.getItem('chatID');
        socket.send(JSON.stringify({ chat_id: chat_id, message: newMessage }));
    }

    function closeElement() {
        element.find('.chat').removeClass('enter').hide();
        element.find('>i').show();
        element.removeClass('expand');
        element.find('.contact').removeClass('expand');
        element.find('.header button').off('click', closeElement);
        element.find('#sendMessage').off('click', sendNewMessage);
        element.find('.text-box').off('keydown', onMetaAndEnter).attr("contenteditable", "false").blur();
        setTimeout(function () {
            element.find('.chat').removeClass('enter').show()
            element.click(openElement);
        }, 500);
    }

    function onMetaAndEnter(event) {
        if ((event.metaKey || event.ctrlKey) && event.keyCode == 13) {
            sendNewMessage();
        }
    }

    function createUUID() {
        // Генерация UUID
        var s = [];
        var hexDigits = "0123456789abcdef";
        for (var i = 0; i < 36; i++) {
            s[i] = hexDigits.charAt(Math.floor(Math.random() * 16));
        }
        s[14] = "4";
        s[19] = hexDigits.charAt((s[19] & 0x3) | 0x8);
        s[8] = s[13] = s[18] = s[23] = "-";

        var uuid = s.join("");
        return uuid;
    }

    $('.text-box').keydown(function (event) {
        if (event.keyCode === 13) {
        event.preventDefault();
        sendNewMessage();
        }
    });
});