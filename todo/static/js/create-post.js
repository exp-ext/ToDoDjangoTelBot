document.getElementById('id_image').addEventListener('change', function(event) {
  const imageGrid = document.getElementById('image-grid');
  imageGrid.innerHTML = '';
  const files = event.target.files;
  for (let i = 0; i < files.length; i++) {
    let file = files[i];
    if (file.type.startsWith('image/')) {
      const gridItem = document.createElement('div');
      gridItem.classList.add('grid-item');      
      let reader = new FileReader();
      reader.onload = function(e) {
        gridItem.style.backgroundImage = `url(${e.target.result})`;
      };
      reader.readAsDataURL(file);
      imageGrid.appendChild(gridItem);
    }
  }
});