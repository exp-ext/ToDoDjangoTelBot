document.querySelectorAll('.button').forEach(button => {
  const text = button.textContent.trim();
  const spannedText = text.split('').map(letter => `<span>${letter}</span>`).join('');
  button.innerHTML = `<div>${spannedText}</div>`;
});
