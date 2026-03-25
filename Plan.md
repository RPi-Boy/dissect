# PROJECT CONTEXT
You are the lead autonomous developer building "Dissect", an AI-driven threat modeling platform for open-source GitHub repositories. 

## TECH STACK
- Backend: Python (FastAPI for asynchronous webhook handling)
- AI Integration: OpenRouter API (Claude Opus / Qwen Coder)
- Frontend: Vanilla HTML, CSS, JS 
- UI Generation: Google Stitch (to build out our Figma designs)
- Environment: Local development (will use ngrok to expose the webhook to GitHub)

## AGENT DIRECTIVES
1. Do NOT use heavy frontend frameworks like React or Next.js. Stick strictly to vanilla HTML/CSS/JS and use Stitch to generate the UI components.
2. Generate an Implementation Plan Artifact before writing any code. I must approve the plan before you proceed.
3. Use the terminal to initialize the environment, install required Python packages (`fastapi`, `uvicorn`, `httpx`, `python-dotenv`), and freeze them into `requirements.txt`.
4. Create a `.env` file template for `OPENROUTER_API_KEY` and `GITHUB_WEBHOOK_SECRET`.
5. Execute the following phases sequentially. Do not move to the next phase until the current one is verified.

## EXECUTION PHASES

### Phase 1: Workspace & Frontend Scaffolding
- Create a clean directory structure:
  `/backend` (for FastAPI logic)
  `/frontend` (for index.html, styles.css, app.js)

  dissect/
│
├── backend/
│   ├── main.py                # FastAPI entry point
│   ├── webhook.py             # GitHub webhook handler
│   ├── repo_processor.py      # Clone repo + filter files
│   ├── diff_analyzer.py       # Extract git diffs
│   │
│   ├── ai_engine/
│   │   ├── llm_analyzer.py    # Calls OpenRouter
│   │   ├── prompt_builder.py  # Builds structured prompts
│   │   ├── report_parser.py   # Convert LLM output → JSON
│   │
│   ├── ml_model/
│   │   ├── model.py           # RandomForest/XGBoost model
│   │   ├── feature_extractor.py
│   │   ├── train.py
│   │   ├── predict.py
│   │
│   ├── graph_engine/
│   │   ├── graph_builder.py   # Code → function call graph
│   │   ├── graph_utils.py
│   │
│   ├── simulation/
│   │   ├── attack_simulator.py    # Main simulation controller
│   │   ├── sql_injection.py       # SQL attack animation logic
│   │   ├── buffer_overflow.py     # Memory simulation
│   │   ├── propagation.py         # Graph spread simulation
│   │
│   ├── opencv_engine/
│   │   ├── renderer.py        # OpenCV drawing canvas
│   │   ├── animations.py      # Movement logic (dots, flows)
│   │   ├── heatmap.py         # Risk heatmap overlay
│   │
│   ├── utils/
│   │   ├── file_utils.py
│   │   ├── constants.py
│   │
│   └── tasks/
│       ├── background_tasks.py  # async processing
│
├── frontend/
│   ├── index.html
│   ├── dashboard.html
│   ├── report.html
│   │
│   ├── css/
│   ├── js/
│   │   ├── api.js           # backend calls
│   │   ├── dashboard.js     # UI updates
│   │   ├── simulation.js    # controls simulation playback
│   │
│   ├── assets/
│
│
├── scripts/
│   ├── run_server.sh
│   ├── start_ngrok.sh
│
└── README.md



- Use Google Stitch to scaffold a modern, dark-themed UI with three states: 
  1. A landing area with an input field for a GitHub Repo URL.
  2. A loading/processing dashboard.
  3. A clean report viewing area.
- Set up FastAPI to mount and serve the `/frontend` static files on the root (`/`) route.

### Phase 2: The Webhook Receiver (FastAPI)
- Create a `/webhook` POST endpoint to receive GitHub push events.
- CRITICAL: Webhooks time out fast. The endpoint must instantly return a `200 OK` and pass the actual payload processing to a `FastAPI.BackgroundTasks` function.

### Phase 3: The AI Engine (OpenRouter)
- Implement a utility function to fetch repo contents (for primary analysis) and `git diff` outputs (for secondary analysis).
- Integrate the OpenRouter API.
- Create two distinct pipeline functions:
  1. `analyze_primary(repo_data)`: Prompts the LLM for a full attack surface trace.
  2. `analyze_diff(previous_report, git_diff)`: Prompts the LLM to update the existing threat model based only on the new code changes.
- Save the LLM outputs as Markdown files.

### Phase 4: Integration & Browser Verification
- Wire up `app.js` to send the repo URL to the backend, handle the loading state, and render the resulting Markdown report.
- Use your built-in browser to launch the local FastAPI server (`uvicorn main:app --reload`).
- Navigate to the local URL, verify the UI renders correctly, and take a screenshot Artifact to prove the frontend is active.