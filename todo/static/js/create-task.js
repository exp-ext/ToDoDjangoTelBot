document.getElementById('id_image').addEventListener('change', function(event) {
  const imageGrid = document.getElementById('image-grid');
  imageGrid.innerHTML = '';
  const files = event.target.files;
  for (let i = 0; i < files.length; i++) {
    let file = files[i];
    if (file.type.startsWith('image/')) {
      let img = document.createElement('img');
      img.classList.add('preview', 'grid-item');
      img.file = file;
      imageGrid.appendChild(img);
      let reader = new FileReader();
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
  const imageGridLine = document.getElementById('image-grid-link');
  imageGridLine.innerHTML = '';
  const imageUrl = event.target.value;
  if (imageUrl && imageUrl.startsWith('http')) {
    let img = document.createElement('img');
    img.classList.add('preview', 'grid-item');
    img.src = imageUrl;
    imageGridLine.appendChild(img);
  }
});