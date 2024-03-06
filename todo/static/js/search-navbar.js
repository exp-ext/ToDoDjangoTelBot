function initAutocomplete(searchUrl) {
  const $searchInput = $("#search-input");
  $searchInput.autocomplete({
    source: searchUrl,
    minLength: 2,
    focus: function(event, ui) {
      $searchInput.val(ui.item.label);
      return false;
    },
    select: function(event, ui) {
      if (ui.item.link) {
        window.location.href = ui.item.link;
      } else {
        $searchInput.val(ui.item.label);
      }
      return false;
    },
  }).data("ui-autocomplete")._renderItem = function(ul, item) {
    const listItem = $("<li>").addClass("ui-menu-item");
    if (item.link) {
      listItem.append($(`<img src='${item.image}' height='30'/>`))
              .append($(`<a href='${item.link}'>`).text(item.label));
    } else {
      listItem.append($("<div>").text(item.label));
    }
    return listItem.appendTo(ul);
  };
}
(function() {
    function addItemsToNavbar(items, media_bucket) {
        const navbarItems = document.getElementById('navbarItems');
        const fragment = document.createDocumentFragment();
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
                img.className = 'nav-image';
                a.appendChild(img);
            }
            a.appendChild(document.createTextNode(item.title));
            li.appendChild(a);
            fragment.appendChild(li);
        });
        navbarItems.appendChild(fragment);
        let tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.forEach(function (tooltipTriggerEl) {
            new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    window.addItemsToNavbar = addItemsToNavbar;
})();