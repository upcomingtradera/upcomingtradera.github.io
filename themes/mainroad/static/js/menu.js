'use strict';

(function iifeMenu(document, window, undefined) {
    var menuBtn = document.querySelector('.menu__btn');
    var menu = document.querySelector('.menu__list');
    
    // Define the TOC button and menu elements
    var tocBtn = document.querySelector('.toc__btn');
    var tocMenu = document.querySelector('.toc__menu');

    function toggleMainMenu(targetBtn, targetMenu) {
        targetMenu.classList.toggle('menu__list--active');
        targetMenu.classList.toggle('menu__list--transition');
        targetBtn.classList.toggle('menu__btn--active');
        targetBtn.setAttribute(
            'aria-expanded',
            targetBtn.getAttribute('aria-expanded') === 'true' ? 'false' : 'true'
        );
    }

    function toggleTOC(targetBtn, targetMenu) {
        targetMenu.classList.toggle('toc__menu--active');
        targetBtn.classList.toggle('toc__btn--active');
        targetBtn.setAttribute(
            'aria-expanded',
            targetBtn.getAttribute('aria-expanded') === 'true' ? 'false' : 'true'
        );
    }

    function removeMenuTransition() {
        this.classList.remove('menu__list--transition');
    }

    function removeTOCTransition() {
        this.classList.remove('toc__menu--transition');
    }

    if (menuBtn && menu) {
        menuBtn.addEventListener('click', function() {
            toggleMainMenu(menuBtn, menu);
        }, false);
        menu.addEventListener('transitionend', removeMenuTransition, false);
    }

    // New TOC button event listeners
    if (tocBtn && tocMenu) {
        tocBtn.addEventListener('click', function() {
            toggleTOC(tocBtn, tocMenu);
        }, false);
        tocMenu.addEventListener('transitionend', removeTOCTransition, false);
    }
}(document, window));
