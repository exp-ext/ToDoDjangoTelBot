document.addEventListener("DOMContentLoaded", function() {
  const bannerData = document.getElementById('banner-data');
  const banner = {
    reference: bannerData.getAttribute('data-reference'),
    image: bannerData.getAttribute('data-image'),
    text: bannerData.getAttribute('data-text'),
    mobileText: bannerData.getAttribute('data-mobile-text')
  };

  const desktopContent = `
    <a href="${banner.reference}" target="_blank" rel="nofollow">
      <img class="card-img-top mx-auto d-block" src="${banner.image}" style="max-width: 100%; max-height: 380px; height: auto;" />
    </a>
    <div class="card-body">
      <p class="card-text">${banner.text}</p>
    </div>
  `;

  const mobileContent = `
    <a href="${banner.reference}" target="_blank" rel="nofollow" class="d-flex justify-content-center align-items-center flex-shrink-0" style="max-width: 50%;">
      <img src="${banner.image}" style="max-width: 100%; height: auto;" />
    </a>
    <p class="flex-grow-1 d-flex" style="max-width: 50%; margin: 0;">${banner.mobileText}</p>
  `;

  const adContainer = document.getElementById('yandex_rtb_R-A-3403802-1');
  const adMobileContainer = document.getElementById('yandex_rtb_R-A-3403802-10');

  function checkAdBlock() {
    if ((adContainer && adContainer.innerHTML.trim() === "") || 
      (adMobileContainer && adMobileContainer.innerHTML.trim() === "")) {
      const isMobile = window.matchMedia("only screen and (max-width: 768px)").matches;

      const content = isMobile ? mobileContent : desktopContent;     

      document.getElementById('card-container').innerHTML = content;
      document.getElementById('card-container').style.display = isMobile ? 'flex' : 'block';
      if (isMobile) {
        document.getElementById('card-container').style.justifyContent = 'center';
        document.getElementById('card-container').style.alignItems = 'center';
        document.getElementById('card-container').style.height = '100%';
      }
    }
  }

  setTimeout(checkAdBlock, 1500);
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
