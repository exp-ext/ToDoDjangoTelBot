// Выбираем все элементы с классом "_anim-items"
const animItems = document.querySelectorAll('._anim-items');

if (animItems.length > 0) {
    // Добавляем обработчик события прокрутки страницы
    window.addEventListener('scroll', animOnScroll);

    function animOnScroll() {
        // Перебираем все элементы с классом "_anim-items"
        for (let index = 0; index < animItems.length; index++) {
            const animItem = animItems[index];
            // Получаем высоту текущего элемента
            const animItemsHeight = animItem.offsetHeight;
            // Получаем позицию элемента относительно верхней границы окна
            const animItemsOffset = offset(animItem).top;
            const animStart = 4;

            // Рассчитываем точку, на которой анимация должна начинаться
            let animItemPoint = window.innerHeight - animItemsHeight / animStart;
            if (animItemsHeight > window.innerHeight) {
                animItemPoint = window.innerHeight - window.innerHeight / animStart;
            }

            // Проверяем, если элемент виден на экране
            if (
                window.scrollY > animItemsOffset - animItemPoint &&
                window.scrollY < animItemsOffset + animItemsHeight
            ) {
                animItem.classList.add('_active');
            } else {
                // Если элемент не виден и не имеет класс "_anim-no-hide", удаляем класс "_active"
                if (!animItem.classList.contains('_anim-no-hide')) {
                    animItem.classList.remove('_active');
                }
            }
        }
    }

    // Функция для получения позиции элемента на странице
    function offset(el) {
        const rect = el.getBoundingClientRect(),
            scrollLeft = window.scrollX || document.documentElement.scrollLeft,
            scrollTop = window.scrollY || document.documentElement.scrollTop;
        return { top: rect.top + scrollTop, left: rect.left + scrollLeft };
    }

    // Вызываем функцию `animOnScroll` через 300 миллисекунд после загрузки страницы
    setTimeout(() => {
        animOnScroll();
    }, 300);
}
