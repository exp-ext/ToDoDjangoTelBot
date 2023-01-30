let stcard = document.querySelectorAll(".stcard"), rotate;
for(let i = 0; i < stcard.length; i++){
    rotate = Math.random() * 5 * (Math.round(Math.random()) ? 1 : -1);
    stcard[i].style.transform = "rotate("+ rotate +"deg)";
}
