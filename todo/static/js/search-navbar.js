// autocomplete.js
function initAutocomplete(searchUrl) {
  $("#search-input").autocomplete({
    source: searchUrl,
    minLength: 2,
    focus: function(event, ui) {
      $("#search-input").val(ui.item.label);
      return false;
    },
    select: function(event, ui) {
      if (ui.item.link) {
        window.location.href = ui.item.link;
      } else {
        $("#search-input").val(ui.item.label);
      }
      return false;
    },
  }).data("ui-autocomplete")._renderItem = function(ul, item) {
    var listItem = $("<li>");
    listItem.addClass("ui-menu-item");
    if (item.link) {
      listItem.append("<img src='" + item.image + "' height='30'/>" + "<a href='" + item.link + "'>" + item.label + " </a>");
    } else {
      listItem.append("<div>" + item.label + "</div>");
    }
    return listItem.appendTo(ul);
  };
}

// Функция для добавления элементов в навбар и инициализации всплывающих подсказок
(function() {
    function addItemsToNavbar(items, media_bucket) {
        const navbarItems = document.getElementById('navbarItems');
        items.forEach(item => {
            const li = document.createElement('li');
            li.className = 'nav-item';

            const a = document.createElement('a');
            a.className = 'nav-link';
            a.href = `?q=${encodeURIComponent(item.slug)}`;
            a.title = item.description;
            a.setAttribute('data-bs-toggle', 'tooltip');
            a.setAttribute('data-bs-placement', 'bottom');

            if (item.image) {
                const img = document.createElement('img');
                img.src = item.image;
                img.style.width = '32px';
                img.style.height = '32px';
                img.style.marginRight = '10px';
                a.appendChild(img);
            }

            a.appendChild(document.createTextNode(item.title));

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
