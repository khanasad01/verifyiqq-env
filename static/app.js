/**
 * VerifyIQ Tactical Command - Neural Interface
 * v2.0.0-tactical
 */

const state = {
    taskId: '',
    timestep: 0,
    reward: 0.0,
    fraudCount: 0,
    done: false,
    selectedAction: 'reply_only',
    tasks: [],
    gridSize: 12
};

// ── ELEMENTS ───────────────────────────────────────────────────────────────
const terminal = document.getElementById('terminal');
const taskSelector = document.getElementById('task-selector');
const btnReset = document.getElementById('btn-reset');
const btnBaseline = document.getElementById('btn-baseline');
const btnScores = document.getElementById('btn-scores');
const btnSendAction = document.getElementById('btn-send-action');
const grid = document.getElementById('grid');
const progressBar = document.getElementById('progress-bar');
const statProgress = document.getElementById('stat-progress');

// ── INITIALIZATION ──────────────────────────────────────────────────────────
async function init() {
    generateGrid();
    await fetchTasks();
    
    // Polling for automated state updates
    setInterval(fetchState, 1500);

    // Re-bind Action Builder buttons since they are in the DOM now
    setupActionBuilder();
}

// ── CORE LOGIC ──────────────────────────────────────────────────────────────
function generateGrid() {
    grid.innerHTML = '';
    for (let i = 0; i < state.gridSize * state.gridSize; i++) {
        const cell = document.createElement('div');
        cell.className = 'grid-cell';
        cell.id = `cell-${i}`;
        grid.appendChild(cell);
    }
}

function updateGridEffects() {
    const cells = document.querySelectorAll('.grid-cell');
    cells.forEach(c => c.classList.remove('active', 'hit'));
    
    // Randomly activate 30 cells to simulate data processing
    for(let i=0; i<30; i++) {
        const idx = Math.floor(Math.random() * cells.length);
        cells[idx].classList.add('active');
    }
    
    // Highlight a few "hit" cells to simulate verification
    for(let i=0; i<3; i++) {
        const hitIdx = Math.floor(Math.random() * cells.length);
        cells[hitIdx].classList.add('hit');
    }
}

async function fetchTasks() {
    try {
        const response = await fetch('/tasks');
        const data = await response.json();
        state.tasks = data.tasks;
        taskSelector.innerHTML = data.tasks.map(t => 
            `<option value="${t.id}">${t.id.toUpperCase().replace(/_/g, ' ')}</option>`
        ).join('');
        state.taskId = taskSelector.value;
    } catch (err) {
        logToTerminal('AUTH ERROR: Could not connect to Task Server', 'agent');
    }
}

async function fetchState() {
    try {
        const response = await fetch('/state');
        const data = await response.json();
        
        document.getElementById('stat-timestep').innerText = data.resolved || 0;
        document.getElementById('stat-reward').innerText = (data.avg_csat || 0).toFixed(4);
        document.getElementById('stat-fraud').innerText = data.fraud_caught || 0;
        document.getElementById('stat-done').innerText = data.queue_remaining === 0 ? 'YES' : 'NO';
        
        // Match the "Wildfire" containment style bar
        const total = 40; // Max messages based on full_support_shift
        const progress = Math.min(100, ((data.resolved || 0) / total) * 100);
        progressBar.style.width = `${progress}%`;
        statProgress.innerText = progress.toFixed(1);
        
    } catch (err) {}
}

function logToTerminal(message, type = 'sys') {
    const line = document.createElement('div');
    line.className = `line ${type}`;
    const now = new Date();
    const ts = `[${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}] `;
    line.innerText = ts + message;
    
    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
}

function setupActionBuilder() {
    const actionButtons = document.querySelectorAll('.btn-action');
    actionButtons.forEach(btn => {
        btn.onclick = () => {
            actionButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.selectedAction = btn.dataset.type;
            logToTerminal(`COMMAND SELECTED: ${state.selectedAction.toUpperCase()}`, 'sys');
        };
    });
}

// ── EVENT HANDLERS ─────────────────────────────────────────────────────────
btnReset.onclick = async () => {
    logToTerminal('INITIATING ENVIRONMENT RESET...', 'agent');
    try {
        const response = await fetch('/reset', { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task_id: state.taskId })
        });
        const data = await response.json();
        logToTerminal('TACTICAL RESET COMPLETE. NEW OBSERVATION STREAM LOADED.', 'agent');
        logToTerminal(`MESSAGE: "${data.message}"`, 'user');
        updateGridEffects();
    } catch (err) {
        logToTerminal('CRITICAL FAILURE: Neural Link Reset Failed', 'agent');
    }
};

btnSendAction.onclick = async () => {
    logToTerminal(`EXECUTING ACTION: ${state.selectedAction.toUpperCase()}...`, 'agent');
    try {
        const payload = {
            action_type: state.selectedAction,
            reply_message: "Automated Tactical Response triggered via Command Center.",
            order_id: null,
            refund_amount: null
        };
        
        const response = await fetch('/step', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        
        logToTerminal(`ACTION SUCCESS. REWARD: ${data.reward.value.toFixed(2)}`, 'agent');
        if (data.observation && !data.done) {
            logToTerminal(`NEXT MESSAGE: "${data.observation.message}"`, 'user');
        } else if (data.done) {
            logToTerminal('EPISODE COMPLETE. ALL QUEUES CLEAR.', 'agent');
        }
        
        updateGridEffects();
    } catch (err) {
        logToTerminal('ACTION INTERRUPTED: Field Connection Lost', 'agent');
    }
};

btnBaseline.onclick = async () => {
    logToTerminal('LAUNCHING AUTONOMOUS BASELINE RUN...', 'agent');
    try {
        const response = await fetch('/baseline', { method: 'POST' });
        const data = await response.json();
        for (const [task, score] of Object.entries(data.baseline_scores)) {
            const idx = task === 'single_intent_triage' ? '1' : task === 'hinglish_fraud_detection' ? '2' : '3';
            const scoreEl = document.getElementById(`score-${idx}`);
            if (scoreEl) scoreEl.innerText = score.toFixed(2);
        }
        logToTerminal('BASELINE SCORES SYNCHRONIZED.', 'agent');
    } catch (err) {}
};

btnScores.onclick = async () => {
    logToTerminal('QUERYING MISSION EVALUATION DATABASE...', 'sys');
    try {
        const response = await fetch('/baseline', { method: 'POST' });
        const data = await response.json();
        const scores = data.baseline_scores;
        
        if (scores.single_intent_triage) document.getElementById('score-1').innerText = scores.single_intent_triage.toFixed(2);
        if (scores.hinglish_fraud_detection) document.getElementById('score-2').innerText = scores.hinglish_fraud_detection.toFixed(2);
        if (scores.full_support_shift) document.getElementById('score-3').innerText = scores.full_support_shift.toFixed(2);
        
        logToTerminal('MISSION SCORES RETRIEVED.', 'agent');
    } catch (err) {
        logToTerminal('QUERY ERROR: Evaluation server not responding.', 'agent');
    }
};

taskSelector.onchange = (e) => {
    state.taskId = e.target.value;
    logToTerminal(`ZONAL SHIFT: ${state.taskId.toUpperCase()}`, 'sys');
};

// BOOT
init();
