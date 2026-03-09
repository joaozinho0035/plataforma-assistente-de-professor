/**
 * Canal Educação v3.0 — WebSocket Client for Grade Horária
 * Connects to ws://host/ws/grade?token=JWT
 * Handles: SLOT_LOCKED, SLOT_RELEASED, USER_CONNECTED, USER_DISCONNECTED, GRADE_UPDATED
 */

let ws = null;
let reconnectAttempts = 0;
const MAX_RECONNECT = 5;

function initGradeWebSocket(token) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/grade?token=${token}`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('[WS] Conectado à grade em tempo real');
        reconnectAttempts = 0;
        updateWsIndicator(true);
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWsMessage(data);
    };

    ws.onclose = (event) => {
        console.log('[WS] Desconectado:', event.code, event.reason);
        updateWsIndicator(false);

        if (reconnectAttempts < MAX_RECONNECT) {
            reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
            console.log(`[WS] Reconectando em ${delay / 1000}s... (tentativa ${reconnectAttempts})`);
            setTimeout(() => initGradeWebSocket(token), delay);
        }
    };

    ws.onerror = (error) => {
        console.error('[WS] Erro:', error);
    };
}

function handleWsMessage(data) {
    switch (data.type) {
        case 'INITIAL_STATE':
            // Apply existing locked slots
            Object.entries(data.locked_slots || {}).forEach(([key, info]) => {
                markSlotLocked(key, info.user_name);
            });
            updateOnlineCount(data.connected_users);
            break;

        case 'SLOT_LOCKED':
            markSlotLocked(data.slot_key, data.user_name);
            break;

        case 'SLOT_RELEASED':
            markSlotReleased(data.slot_key);
            break;

        case 'SLOT_LOCK_DENIED':
            showToast(data.message, 'error');
            break;

        case 'USER_CONNECTED':
            updateOnlineCount(data.connected_users);
            break;

        case 'USER_DISCONNECTED':
            updateOnlineCount(data.connected_users);
            (data.released_slots || []).forEach(key => markSlotReleased(key));
            break;

        case 'GRADE_UPDATED':
            showToast(`Grade atualizada por ${data.updated_by}`, 'info');
            break;

        case 'ERROR':
            console.error('[WS] Server error:', data.message);
            break;
    }
}

function markSlotLocked(slotKey, userName) {
    const [estudio, horario] = slotKey.split(':');
    const slot = document.querySelector(
        `.grade-slot[data-studio="${estudio}"][data-time="${horario}"]`
    );
    if (slot) {
        slot.classList.add('locked');
        slot.title = `Bloqueado por ${userName}`;
    }
}

function markSlotReleased(slotKey) {
    const [estudio, horario] = slotKey.split(':');
    const slot = document.querySelector(
        `.grade-slot[data-studio="${estudio}"][data-time="${horario}"]`
    );
    if (slot) {
        slot.classList.remove('locked');
        slot.title = '';
    }
}

function updateOnlineCount(count) {
    const el = document.getElementById('ws-count');
    if (el) el.textContent = count || 0;

    const indicator = document.getElementById('ws-indicator');
    if (indicator) indicator.style.display = 'inline-flex';
}

function updateWsIndicator(connected) {
    const indicator = document.getElementById('ws-indicator');
    if (!indicator) return;
    indicator.style.display = 'inline-flex';

    const dot = indicator.querySelector('.dot');
    if (dot) {
        dot.style.background = connected ? 'var(--status-green)' : 'var(--status-red)';
    }
}

// Send lock/release messages
function lockSlot(estudio, horario, data) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            action: 'LOCK_SLOT',
            estudio: estudio,
            horario: horario,
            data: data,
        }));
    }
}

function releaseSlot(estudio, horario, data) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            action: 'RELEASE_SLOT',
            estudio: estudio,
            horario: horario,
            data: data,
        }));
    }
}
