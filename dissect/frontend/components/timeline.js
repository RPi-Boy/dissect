function renderTimeline(steps) {
    return steps.map(step => `
        <div style="
            padding:10px;
            border-left:2px solid #2563eb;
            margin:10px;
        ">
            <p><b>Step ${step.step}</b></p>
            <p>${step.description}</p>
        </div>
    `).join("");
}