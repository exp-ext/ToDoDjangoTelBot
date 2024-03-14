document.querySelectorAll(".stcard").forEach(stcard => {
    const rotate = Math.random() * 2 * (Math.round(Math.random()) ? 1 : -1);
    stcard.style.transform = `rotate(${rotate}deg)`;
});
function truncateHtml(selector, maxLength) {
  var elements = document.querySelectorAll(selector);
  elements.forEach(function(element) {
    var walk = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null, false);
    var totalLength = 0;
    var charCount;
    var nodesToRemove = [];
    while (walk.nextNode()) {
      var currentNode = walk.currentNode;
      totalLength += currentNode.length;
      if (totalLength > maxLength) {
        charCount = maxLength - (totalLength - currentNode.length);
        currentNode.nodeValue = currentNode.nodeValue.substr(0, charCount) + '...';
        nodesToRemove.push(currentNode);
        break;
      }
    }
    for (var i = 0; i < nodesToRemove.length; i++) {
      var nodeToRemove = nodesToRemove[i];
      while (nodeToRemove.nextSibling) {
        nodeToRemove.parentNode.removeChild(nodeToRemove.nextSibling);
      }
    }
    var walker = document.createTreeWalker(element, NodeFilter.SHOW_ELEMENT, null, false);
    var node;
    while (walker.nextNode()) {
      node = walker.currentNode;
      if (node.hasChildNodes() && !node.firstChild.nodeValue.trim()) {
        node.parentNode.removeChild(node);
      }
    }
  });
}
document.addEventListener('DOMContentLoaded', function() {
  truncateHtml('.stcard p', 65);
});