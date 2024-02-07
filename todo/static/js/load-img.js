var needDiv;

window.addEventListener('load', function() {
  var scrollDiv = document.querySelector(needDiv);
  var images = scrollDiv.querySelectorAll('img');
  var allImagesLoaded = Array.from(images).every(function(img) {
    return img.complete && img.naturalHeight !== 0;
  });
  if (allImagesLoaded) {
    scrollDiv.style.display = 'block';
  }
});