$(document).ready(function() {

  $('.counter').each(function () {
    $(this).prop('Counter',0).animate({
      Counter: $(this).text()
    }, {
      duration: 4000,
      easing: 'swing',
      step: function (now) {
        $(this).text(Math.ceil(now));
      }
    });
    }); 

});

document.querySelectorAll('oembed[url]').forEach(element => {
  const anchor = document.createElement('a');
  anchor.setAttribute('href', element.getAttribute('url'));
  anchor.className = 'embedly-card';
  element.appendChild(anchor);
});

function scrollDown(event) {
  event.preventDefault();
  var targetId = event.target.getAttribute('href').substring(1);
  var targetElement = document.getElementById(targetId);
  if (targetElement) {
    var offset = 64;
    var targetPosition = targetElement.offsetTop - offset;

    window.scrollTo({
      top: targetPosition,
      behavior: 'smooth'
    });
  }
}

function toggleList(event, toggleIcon) {
  const ul = toggleIcon.parentElement.querySelector('ul');
  if (ul) {
    if (ul.style.display === 'none' || ul.style.display === '') {
      ul.style.display = 'block';
      toggleIcon.innerHTML = '<i class="bi bi-circle">';
    } else {
      ul.style.display = 'none';
      toggleIcon.innerHTML = '<i class="bi bi-plus-circle"></i>';
    }
  }
}
