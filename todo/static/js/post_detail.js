document.addEventListener("DOMContentLoaded", function() {
  const bannerData = document.getElementById('banner-data');
  const my_banner = {
    reference: bannerData.getAttribute('data-reference'),
    image: bannerData.getAttribute('data-image'),
    text: bannerData.getAttribute('data-text')
  };
  
  const alternativeContent = `
    <a href="${my_banner.reference}" target="_blank" rel="nofollow">
      <img class="card-img-top mx-auto d-block" src="${my_banner.image}" style="width: 380px; height: 380px;" />
    </a>
    <div class="card-body">
      <p class="card-text">${my_banner.text}</p>
    </div>
  `;

  const adContainer = document.getElementById('yandex_rtb_R-A-3403802-1');

  function checkAdBlock() {
    if (adContainer && adContainer.innerHTML.trim() === "") {
      document.getElementById('card-container').innerHTML = alternativeContent;
      document.getElementById('card-container').style.display = 'block';
    }
  }

  setTimeout(checkAdBlock, 2000);
});


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

setTimeout(function() {
  const content = document.querySelector('.hidden-content');
  if (content) {
    content.classList.remove('hidden-content');
  }
}, 4000);

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
