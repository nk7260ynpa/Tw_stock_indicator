/**
 * 儀表板卡片互動。
 */
document.addEventListener('DOMContentLoaded', function () {
    const cards = document.querySelectorAll('.indicator-card');
    cards.forEach(function (card) {
        card.addEventListener('click', function () {
            cards.forEach(function (c) { c.classList.remove('active'); });
            card.classList.add('active');
        });
    });
});
