/* Fintech KPI Interactions */
document.addEventListener('DOMContentLoaded', () => {
    // 1. Counting Animation
    const counters = document.querySelectorAll('.count-up');

    const animateCount = (element) => {
        const value = parseFloat(element.getAttribute('data-target'));
        const duration = 1500; // 1.5s animation
        const frameDuration = 1000 / 60; // 60fps
        const totalFrames = Math.round(duration / frameDuration);
        let frame = 0;

        const counter = setInterval(() => {
            frame++;
            const progress = frame / totalFrames;
            // Ease out quart
            const easeProgress = 1 - Math.pow(1 - progress, 4);

            const current = value * easeProgress;

            // Format number with commas
            element.innerText = current.toLocaleString('en-IN', {
                maximumFractionDigits: 0
            });

            if (frame === totalFrames) {
                clearInterval(counter);
                element.innerText = value.toLocaleString('en-IN', {
                    maximumFractionDigits: 0
                });
            }
        }, frameDuration);
    };

    // Use Intersection Observer to trigger animation when visible
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                animateCount(element);
                observer.unobserve(element);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(counter => observer.observe(counter));

    // 2. Click Ripple Effect
    const cards = document.querySelectorAll('.fintech-card');
    cards.forEach(card => {
        card.addEventListener('click', function (e) {
            // Don't trigger if clicking link/button inside
            if (e.target.tagName === 'A' || e.target.closest('a')) return;

            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const ripple = document.createElement('span');
            ripple.classList.add('ripple');
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;

            this.appendChild(ripple);

            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
});
