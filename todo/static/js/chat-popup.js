$(document).ready(function () {    
  const element = $('.floating-chat');
  let myStorage = localStorage;
  let chatIsEmpty = true;
  let roomName = createUUID();
  const socket = new WebSocket(`wss://${window.location.host}/ws/${roomName}/`);

  socket.onopen = function(event) {
    console.log("WebSocket connection opened:", event);
  };

  function updateTypingIndicator() {
    let $messages = $('.messages');
    let lastMessageIsOther = $messages.children().last().hasClass('other');
    if (lastMessageIsOther) {
      $('.typing-indicator').hide();
    } else {
      $('.typing-indicator').show();
    }
  }

  socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    const messagesContainer = $('.messages');
    let messageType = data.username === 'Eva' ? 'other' : 'self';
    let messageElement;
    const messageHTML = marked.parse(data.message);
    if (data.is_stream) {
      if (data.is_start) {
        messageElement = $(`<li class="${messageType} stream-message"></li>`).data('is_streaming', true);
        messagesContainer.append(messageElement);
      } else {
        messageElement = messagesContainer.find('.stream-message').last();
        if (data.is_end) {
          messageElement.data('is_streaming', false);
        } else {
          if (data.message) {
            messageElement.html(messageHTML);
          }
        }
      }
    } else {
      messageElement = $(`<li class="${messageType}"></li>`).html(messageHTML);
      messagesContainer.append(messageElement);
    }
    messagesContainer.scrollTop(messagesContainer.prop("scrollHeight"));
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
    let messages = element.find('.messages');
    const textInput = element.find('.text-box');
    element.find('>i').hide();
    element.addClass('expand');
    element.find('.chat').addClass('enter');
    element.find('.contact').addClass('expand');
    textInput.keydown(onMetaAndEnter).attr("contenteditable", "true").focus();
    element.off('click', openElement);
    element.find('.header button').click(closeElement);
    element.find('#sendMessage').click(sendNewMessage);
    if (chatIsEmpty) {
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
    const userInput = $('.text-box');
    const newMessage = userInput.text().trim().replace(/\n/g, '<br>');
    updateTypingIndicator();
    if (!newMessage) return;
    const messagesContainer = $('.messages');
    userInput.text('');
    messagesContainer.finish().animate({
      scrollTop: messagesContainer.prop("scrollHeight")
    }, 250);
    const chat_id = myStorage.getItem('chatID');
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

  function pasteIntoInput(el, text) {
    el.focus();
    if (document.getSelection) {
      let selection = window.getSelection();
      let range = selection.getRangeAt(0);
      range.deleteContents();
      const currentText = el.innerText;
      if (!currentText.endsWith('\n') && text !== '\n') {
        const textNode = document.createTextNode(text);
        range.insertNode(textNode);
        range.setStartAfter(textNode);
        range.setEndAfter(textNode);
        selection.removeAllRanges();
        selection.addRange(range);
      }
    }
  }

  function onMetaAndEnter(event) {
    if (event.keyCode === 13) {
      if (event.shiftKey) {
        if (event.type == "keydown") {
          pasteIntoInput(this, "\n");
        }
      } else {
        event.preventDefault();
        sendNewMessage();
      }
    }
  }

  function createUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
      const r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

});