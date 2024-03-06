function setCursorPosition(pos, elem) {
    elem.focus();
    if (elem.setSelectionRange) elem.setSelectionRange(pos, pos);
    else if (elem.createTextRange) {
        let range = elem.createTextRange();
        range.collapse(true);
        range.moveEnd("character", pos);
        range.moveStart("character", pos);
        range.select();
    }
}
function mask(event) {
    let matrix = this.placeholder,
        i = 0,
        def = matrix.replace(/\D/g, ""),
        val = this.value.replace(/\D/g, "");
    if (def.length >= val.length) {
        val = def;
    }
    matrix = matrix.replace(/[_\d]/g, a => val.charAt(i++) || "_");
    this.value = matrix;
    let lastChar = val.substr(-1);
    i = matrix.lastIndexOf(lastChar);
    i < matrix.length && matrix !== this.placeholder ? i++ : i = matrix.indexOf("_");
    setCursorPosition(i, this);
}
document.addEventListener("DOMContentLoaded", function() {
    const input = document.querySelector("#phone_number");
    if (input) {
        input.addEventListener("input", mask, false);
        input.focus();
        setCursorPosition(3, input);
    }
});
