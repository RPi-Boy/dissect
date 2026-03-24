document.addEventListener('DOMContentLoaded', () => {
    // Select elements to animate
    const heroSection = document.querySelector('.animate-fade-in');
    const scanCard = document.querySelector('.animate-slide-up');

    // Trigger animations by adding the 'loaded' class after DOM is ready
    // A slight delay ensures the browser paints the initial state first
    setTimeout(() => {
        if(heroSection) heroSection.classList.add('loaded');
        if(scanCard) scanCard.classList.add('loaded');
    }, 100);

    // Optional: Add interaction to the buttons
    const scanBtn = document.querySelector('.scan-btn');
    const repoInput = document.querySelector('.repo-input');

    scanBtn.addEventListener('click', () => {
        const repoVal = repoInput.value.trim();
        if(repoVal) {
            scanBtn.innerHTML = 'SCANNING...';
            scanBtn.style.opacity = '0.8';
            
            // Simulate a scan process
            setTimeout(() => {
                scanBtn.innerHTML = 'SCAN REPOSITORY →';
                scanBtn.style.opacity = '1';
                repoInput.value = '';
            }, 1500);
        } else {
            repoInput.focus();
        }
    });
});