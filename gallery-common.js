// gallery-common.js
// Comportement partagé par gallery_template.html, species_list_template.html et
// menacees_template.html : uniquement le menu mobile (hamburger) désormais, depuis
// que la visionneuse plein écran (lightbox + feed mobile) a été remplacée par les
// pages "feed" autonomes (gallery_feed_template.html).

// Menu mobile hamburger
function toggleMobileMenu() {
    document.getElementById('navMenu').classList.toggle('active');
}

// Fermer menu au clic ailleurs
document.addEventListener('click', (e) => {
    const nav = document.querySelector('nav');
    const menu = document.getElementById('navMenu');
    if (menu && !nav.contains(e.target)) {
        menu.classList.remove('active');
    }
});
