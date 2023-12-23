(function() {
    // Функция для добавления элементов в навбар и инициализации всплывающих подсказок
    function addItemsToNavbar(items, media_bucket) {
        const navbarItems = document.getElementById('navbarItems');
        items.forEach(item => {
            const li = document.createElement('li');
            li.className = 'nav-item';

            const a = document.createElement('a');
            a.className = 'nav-link';
            a.href = `?q=${encodeURIComponent(item.fields.slug)}`;
            a.title = item.fields.description;
            a.setAttribute('data-bs-toggle', 'tooltip');
            a.setAttribute('data-bs-placement', 'bottom');

            if (item.fields.image) {
                const img = document.createElement('img');
                img.src = media_bucket + item.fields.image;
                img.style.width = '32px';
                img.style.height = '32px';
                img.style.marginRight = '10px';
                a.appendChild(img);
            }

            a.appendChild(document.createTextNode(item.fields.title));

            li.appendChild(a);
            navbarItems.appendChild(li);
        });

        let tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.forEach(function (tooltipTriggerEl) {
            new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    window.addItemsToNavbar = addItemsToNavbar;
})();