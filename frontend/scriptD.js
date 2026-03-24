document.addEventListener("DOMContentLoaded", () => {
    // Animate the critical risk gauge chart
    const gaugeProgress = document.querySelector('.gauge-progress');
    
    // Circle radius is 54, circumference = 2 * Math.PI * 54 ≈ 339
    const circumference = 339;
    
    // The target percentage based on the UI design (75%)
    const targetPercentage = 75; 
    
    // Calculate stroke-dashoffset (0 is full circle, 339 is empty)
    const offset = circumference - (targetPercentage / 100) * circumference;
    
    // Start empty and animate to the target value
    gaugeProgress.style.strokeDasharray = circumference;
    gaugeProgress.style.strokeDashoffset = circumference;
    
    // Trigger animation slightly after load
    setTimeout(() => {
        gaugeProgress.style.strokeDashoffset = offset;
    }, 300);

    // Optional: Add hover effect to nodes
    const nodes = document.querySelectorAll('.node');
    nodes.forEach(node => {
        node.addEventListener('mouseenter', () => {
            node.style.transform = 'translate(-50%, -50%) scale(1.05)';
            node.style.transition = 'transform 0.2s';
        });
        node.addEventListener('mouseleave', () => {
            node.style.transform = 'translate(-50%, -50%) scale(1)';
        });
    });
});
