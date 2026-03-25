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
    const demoBtn = document.querySelector('.demo-btn');

    const DEMO_REPO_URL = 'https://github.com/RPi-Boy/dissect';
    let demoTypingToken = 0;

    if (demoBtn && repoInput) {
        demoBtn.addEventListener('click', () => {
            demoTypingToken += 1;
            const token = demoTypingToken;
            repoInput.value = '';
            repoInput.focus();

            let i = 0;
            const msPerChar = 32;

            function typeNext() {
                if (token !== demoTypingToken) return;
                if (i >= DEMO_REPO_URL.length) return;
                repoInput.value += DEMO_REPO_URL[i];
                i += 1;
                setTimeout(typeNext, msPerChar);
            }

            typeNext();
        });
    }

    document.getElementById("scanBtn").addEventListener("click", function () {

        const btn = this;
    
        // Change button text while waiting
        btn.innerText = "SCANNING...";
        btn.disabled = true;
    
        // Wait 2 seconds then redirect
        setTimeout(() => {
            window.location.href = "dashboard.html";
        }, 2000);
    
    });
    
    const isValidGitHubUrl = (url) => {
        // Accepts formats like:
        // https://github.com/organization/repo
        // https://github.com/organization/repo/
        // git@github.com:organization/repo.git
        const githubRegex = /^(?:https:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\/?|git@github\.com:[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\.git)$/;
        return githubRegex.test(url);
    };

    scanBtn.addEventListener('click', () => {
        const repoVal = repoInput.value.trim();

        if (!repoVal) {
            repoInput.focus();
            return;
        }

        if (!isValidGitHubUrl(repoVal)) {
            alert('Please enter a valid GitHub repository URL (e.g. https://github.com/user/repo)');
            repoInput.style.borderColor = '#ff3366';
            repoInput.focus();
            return;
        }

        repoInput.style.borderColor = ''; // reset any previous error state

        scanBtn.innerHTML = 'SCANNING...';
        scanBtn.style.opacity = '0.8';

        // Simulate a scan process
        setTimeout(() => {
            scanBtn.innerHTML = 'SCAN REPOSITORY →';
            scanBtn.style.opacity = '1';
            repoInput.value = '';
        }, 1500);
    });

    // Page transition for nav links
    document.body.classList.add('fade-in');

    const transitionLinks = document.querySelectorAll('.nav-link');
    transitionLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            const href = link.getAttribute('href');
            if (!href || href.startsWith('#')) return;

            event.preventDefault();
            document.body.classList.add('fade-out');
            setTimeout(() => {
                window.location.href = href;
            }, 350);
        });
    });
});