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