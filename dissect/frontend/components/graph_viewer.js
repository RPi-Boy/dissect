function drawGraph(canvasId, graph) {
    const canvas = document.getElementById(canvasId);
    const ctx = canvas.getContext("2d");

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const nodes = graph.nodes || [];
    const positions = {};

    const spacing = canvas.width / (nodes.length + 1);

    nodes.forEach((node, i) => {
        positions[node] = {
            x: spacing * (i + 1),
            y: canvas.height / 2
        };

        ctx.fillStyle = "green";
        ctx.beginPath();
        ctx.arc(positions[node].x, positions[node].y, 15, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = "white";
        ctx.fillText(node.slice(0, 10), positions[node].x - 20, positions[node].y - 20);
    });

    // edges
    graph.edges.forEach(([src, dst]) => {
        if (positions[src] && positions[dst]) {
            ctx.strokeStyle = "white";
            ctx.beginPath();
            ctx.moveTo(positions[src].x, positions[src].y);
            ctx.lineTo(positions[dst].x, positions[dst].y);
            ctx.stroke();
        }
    });
}