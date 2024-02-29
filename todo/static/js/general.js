document.addEventListener('DOMContentLoaded', function() {
    document.body.addEventListener('click', function(event) {
        if (event.target.id === 'redirectLink') {
            fetch('/auth/login/tg/generate-td-auth-url/')
                .then(response => response.json())
                .then(data => {
                    window.location.href = data.url;
                })
                .catch(error => console.error('Error fetching the ID:', error));
        }
    });
});

const animItems = document.querySelectorAll('._anim-items');
if (animItems.length > 0) {
    window.addEventListener('scroll', animOnScroll);

    function animOnScroll() {
        for (let index = 0; index < animItems.length; index++) {
            const animItem = animItems[index];
            const animItemsHeight = animItem.offsetHeight;
            const animItemsOffset = offset(animItem).top;
            const animStart = 4;

            let animItemPoint = window.innerHeight - animItemsHeight / animStart;
            if (animItemsHeight > window.innerHeight) {
                animItemPoint = window.innerHeight - window.innerHeight / animStart;
            }
            if (
                window.scrollY > animItemsOffset - animItemPoint &&
                window.scrollY < animItemsOffset + animItemsHeight
            ) {
                animItem.classList.add('_active');
            } else {
                if (!animItem.classList.contains('_anim-no-hide')) {
                    animItem.classList.remove('_active');
                }
            }
        }
    }
    function offset(el) {
        const rect = el.getBoundingClientRect(),
            scrollLeft = window.scrollX || document.documentElement.scrollLeft,
            scrollTop = window.scrollY || document.documentElement.scrollTop;
        return { top: rect.top + scrollTop, left: rect.left + scrollLeft };
    }
    setTimeout(() => {
        animOnScroll();
    }, 300);
}
