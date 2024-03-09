document.querySelectorAll(".stcard").forEach(stcard => {
    const rotate = Math.random() * 2 * (Math.round(Math.random()) ? 1 : -1);
    stcard.style.transform = `rotate(${rotate}deg)`;
});