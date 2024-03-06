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
let optimized = false;
if (animItems.length > 0) {
    window.addEventListener('scroll', () => {
        if (!optimized) {
            requestAnimationFrame(animOnScroll);
            optimized = true;
        }
    });
    function animOnScroll() {
        const windowHeight = window.innerHeight;
        animItems.forEach(animItem => {
            const animItemHeight = animItem.offsetHeight;
            const animItemOffset = offset(animItem).top;
            const animStart = 4;
            let animItemPoint = windowHeight - animItemHeight / animStart;
            if (animItemHeight > windowHeight) {
                animItemPoint = windowHeight - windowHeight / animStart;
            }
            if (
                (window.scrollY > animItemOffset - animItemPoint) &&
                (window.scrollY < animItemOffset + animItemHeight)
            ) {
                animItem.classList.add('_active');
            } else {
                if (!animItem.classList.contains('_anim-no-hide')) {
                    animItem.classList.remove('_active');
                }
            }
        });
        optimized = false;
    }
    function offset(el) {
        const rect = el.getBoundingClientRect(),
            scrollTop = window.scrollY || document.documentElement.scrollTop;
        return { top: rect.top + scrollTop };
    }
    setTimeout(() => {
        animOnScroll();
    }, 300);
}