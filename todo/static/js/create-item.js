document.getElementById('id_image').addEventListener('change', function(event) {
  var imageGrid = document.getElementById('image-grid');
  imageGrid.innerHTML = '';
  var files = event.target.files;
  for (var i = 0; i < files.length; i++) {
    var file = files[i];
    if (file.type.startsWith('image/')) {
      var img = document.createElement('img');
      img.classList.add('preview', 'grid-item');
      img.file = file;
      imageGrid.appendChild(img);
      var reader = new FileReader();
      reader.onload = (function(aImg) { 
        return function(e) { 
          aImg.src = e.target.result; 
        }; 
      })(img);
      reader.readAsDataURL(file);
    }
  }
});
document.getElementById('id_picture_link').addEventListener('change', function(event) {
  var imageGridLine = document.getElementById('image-grid-link');
  imageGridLine.innerHTML = '';
  var imageUrl = event.target.value;
  if (imageUrl && imageUrl.startsWith('http')) {
    var img = document.createElement('img');
    img.classList.add('preview', 'grid-item');
    img.src = imageUrl;
    imageGridLine.appendChild(img);
  }
});