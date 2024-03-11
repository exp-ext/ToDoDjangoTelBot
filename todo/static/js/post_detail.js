document.addEventListener("DOMContentLoaded", function() {
  const bannerData = document.getElementById('banner-data');
  if (!bannerData) return;
  const banner = {
    reference: bannerData.getAttribute('data-reference'),
    image: bannerData.getAttribute('data-image'),
    text: bannerData.getAttribute('data-text'),
    mobileText: bannerData.getAttribute('data-mobile-text')
  };
  const adContainer = document.getElementById('yandex_rtb_R-A-3403802-1');
  const adMobileContainer = document.getElementById('yandex_rtb_R-A-3403802-10');
  const cardContainer = document.getElementById('card-container');
  function updateAdBlockContent() {
    const content = isMobile ? createMobileContent() : createDesktopContent();
    if (cardContainer) {
      cardContainer.innerHTML = content;
      adjustCardContainerStyle();
    }
  }
  function createDesktopContent() {
    return `
      <a href="${banner.reference}" target="_blank" rel="nofollow">
        <img class="card-img-top mx-auto d-block" src="${banner.image}" alt="QR-code" style="max-width: 100%; max-height: 380px; height: auto;" />
      </a>
      <div class="card-body">
        <p class="card-text">${banner.text}</p>
      </div>
    `;
  }
  function createMobileContent() {
    return `
      <a href="${banner.reference}" target="_blank" rel="nofollow" class="d-flex justify-content-center align-items-center flex-shrink-0" style="max-width: 50%;">
        <img src="${banner.image}" alt="QR-code" style="max-width: 100%; height: auto;" />
      </a>
      <p class="flex-grow-1 d-flex" style="max-width: 50%; margin: 0;">${banner.mobileText}</p>
    `;
  }
  function adjustCardContainerStyle() {
    if (isMobile) {
      Object.assign(cardContainer.style, {
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100%'
      });
    } else {
      cardContainer.style.display = 'block';
    }
  }
  function checkAdBlock() {
    const adContainer = document.getElementById('yandex_rtb_R-A-3403802-1');
    const adMobileContainer = document.getElementById('yandex_rtb_R-A-3403802-10');
    if ((adContainer && adContainer.innerHTML.trim() === "") || 
      (adMobileContainer && adMobileContainer.innerHTML.trim() === "")) {
      requestAnimationFrame(updateAdBlockContent);
    }
  }
  setTimeout(checkAdBlock, 2500);
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
  const url = element.getAttribute('url');
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.className = 'embedly-card';
  element.appendChild(anchor);
});
function scrollDown(event) {
  const hrefAttribute = event.target.getAttribute('href');
  if (hrefAttribute && hrefAttribute.startsWith('#')) {
    const targetId = hrefAttribute.slice(1);
    const targetElement = document.getElementById(targetId);
    if (targetElement) {
      event.preventDefault();
      const offset = 64;
      const targetPosition = targetElement.offsetTop - offset;
      window.scrollTo({
        top: targetPosition,
        behavior: 'smooth'
      });
    }
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
    ul.classList.toggle('hidden');
    ul.classList.toggle('visible');
    const svg = toggleIcon.querySelector('svg');
    if (svg.classList.contains('bi-plus-circle')) {
      svg.setAttribute('viewBox', "0 0 16 16");
      svg.innerHTML = '<path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>';
      svg.classList.replace('bi-plus-circle', 'bi-circle');
    } else {
      svg.setAttribute('viewBox', "0 0 16 16");
      svg.innerHTML = '<path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/><path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/>';
      svg.classList.replace('bi-circle', 'bi-plus-circle');
    }
  }
}
document.addEventListener('DOMContentLoaded', (event) => {
  if (isMobile) {
    const button = document.createElement('button');
    button.id = 'scrollToTopBtn';
    button.textContent = '↑ в начало';
    button.style.display = 'none';
    document.body.appendChild(button);
    setTimeout(() => {
      button.style.display = 'block';
    }, 30000);
    function scrollToTop() {
      window.scrollTo({top: 0, behavior: 'smooth'});
    }
    button.addEventListener('click', scrollToTop);
  }
});