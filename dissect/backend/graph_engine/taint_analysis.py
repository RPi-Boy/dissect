def perform_taint_analysis(code: str):
    """
    Tracks flow of user-controlled input to dangerous sinks
    """

    sources = ["input(", "request", "req.", "params", "argv"]
    sinks = ["execute(", "eval(", "query(", "os.system", "subprocess"]

    tainted_lines = []
    lines = code.split("\n")

    for i, line in enumerate(lines):
        if any(src in line for src in sources):
            tainted_lines.append(("SOURCE", i, line.strip()))

        if any(sink in line for sink in sinks):
            tainted_lines.append(("SINK", i, line.strip()))

    # Simple pairing: source → sink existence
    vulnerability_paths = []

    source_indices = [i for t, i, _ in tainted_lines if t == "SOURCE"]
    sink_indices = [i for t, i, _ in tainted_lines if t == "SINK"]

    for s in source_indices:
        for k in sink_indices:
            if s < k:  # forward flow
                vulnerability_paths.append((s, k))

    return {
        "tainted_lines": tainted_lines,
        "vulnerable_paths": vulnerability_paths,
        "count": len(vulnerability_paths)
    }