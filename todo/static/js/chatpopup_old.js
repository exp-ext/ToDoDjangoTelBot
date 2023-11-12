$(document).ready(function () {
    var element = $('.floating-chat');
    var myStorage = localStorage;
    var chatIsEmpty = true; // Переменная для отслеживания состояния чата
    var isRequestPending = false; // Флаг активного запроса

    if (!myStorage.getItem('chatID')) {
        myStorage.setItem('chatID', createUUID());
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
        var strLength = textInput.text().length * 2;
        textInput.keydown(onMetaAndEnter).attr("contenteditable", "true").focus();
        element.off('click', openElement);
        element.find('.header button').click(closeElement);
        element.find('#sendMessage').click(sendNewMessage);

        // Проверка наличия сообщений в чате
        if (chatIsEmpty) {
            // Запрос на получение последних сообщений
            $.ajax({
                url: '/ai/last-message/',
                type: 'GET',
                dataType: 'json',
                success: function (response) {
                    chatIsEmpty = false; // Устанавливаем флаг в false, так как чат больше не пустой
                    // Отобразить полученные сообщения в чате
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

    function createUUID() {
        // Генерация UUID
        var s = [];
        var hexDigits = "0123456789abcdef";
        for (var i = 0; i < 36; i++) {
            s[i] = hexDigits.charAt(Math.floor(Math.random() * 16));
        }
        s[14] = "4"; // bits 12-15 of the time_hi_and_version field to 0010
        s[19] = hexDigits.charAt((s[19] & 0x3) | 0x8); // bits 6-7 of the clock_seq_hi_and_reserved to 01
        s[8] = s[13] = s[18] = s[23] = "-";

        var uuid = s.join("");
        return uuid;
    }

    function sendNewMessage() {

        var userInput = $('.text-box');
        var newMessage = userInput.text().trim();

        if (!newMessage) return;

        if (isRequestPending) {
            // Если запрос уже активен, не выполняем новый
            console.log('A request is already pending. Please wait.');
            return;
        }
        isRequestPending = true;
    
        var messagesContainer = $('.messages');    
        messagesContainer.append([
            '<li class="self">',
            newMessage,
            '</li>'
        ].join(''));
    
        // Clean out old message
        userInput.text('');
        // Focus on input
        userInput.focus();
    
        messagesContainer.finish().animate({
            scrollTop: messagesContainer.prop("scrollHeight")
        }, 250);
    
        // Отправка сообщения на сервер
        var chat_id = myStorage.getItem('chatID');
        var data = {
            chat_id: chat_id,
            message: newMessage,
            csrfmiddlewaretoken: getCookie('csrftoken')
        };

        // Показываем "typing" рядом с названием ассистента
        $('.typing-indicator').show();
    
        // AJAX-запрос на сервер
        $.ajax({
            url: '/ai/message/',
            type: 'POST',
            dataType: 'json',
            data: data,
            timeout: 600000,
            success: function (response) {
                // Скрываем "typing"
                $('.typing-indicator').hide();
                chatIsEmpty = false;
    
                // Проверяем, совпадает ли chat_id
                if (response.chat_id === chat_id) {
                    // Выводим ответ от сервера
                    messagesContainer.append([
                        '<li class="other">',
                        response.message,
                        '</li>'
                    ].join(''));
                }
    
                messagesContainer.scrollTop(messagesContainer.prop("scrollHeight"));
    
                isRequestPending = false;
            },
            error: function () {
                // Скрываем "typing" и в случае ошибки
                $('.typing-indicator').hide();
                // В случае ошибки также разблокируем отправку
                isRequestPending = false;
            }
        });
    }

    function onMetaAndEnter(event) {
        if ((event.metaKey || event.ctrlKey) && event.keyCode == 13) {
            sendNewMessage();
        }
    }

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                // Проверяем, начинается ли куки с нужного имени
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    $('.text-box').keydown(function (event) {
        if (event.keyCode === 13) {
          event.preventDefault();
          sendNewMessage();
        }
      });
});

