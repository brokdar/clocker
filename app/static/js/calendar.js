const toastContainer = document.createElement('div');
toastContainer.className = 'toast-container';
document.body.appendChild(toastContainer);

let copiedEntry = null;
let lastToast = null;

function showToast(message, type = 'info', duration = 3000) {
    if (lastToast) {
        lastToast.remove();
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span>
        <span>${message}</span>
        <button class="toast-close" aria-label="Close">×</button>
    `;

    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.onclick = () => toast.remove();

    toastContainer.appendChild(toast);
    lastToast = toast;

    if (duration > 0) {
        setTimeout(() => toast.remove(), duration);
    }
}

function showConfirmDialog(message) {
    return new Promise((resolve) => {
        const wrapper = document.createElement('div');
        wrapper.className = 'confirm-dialog';
        wrapper.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(0, 0, 0, 0.5);
            z-index: 9999;
        `;
        
        const dialog = document.createElement('div');
        dialog.style.cssText = `
            background: white;
            padding: 24px;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
            min-width: 300px;
            text-align: center;
        `;
        dialog.innerHTML = `
            <p style="margin: 0 0 20px 0">${message}</p>
            <div style="display: flex; gap: 10px; justify-content: center">
                <button class="confirm-yes" style="background: #ff4444; color: white; padding: 8px 20px; border: none; border-radius: 4px; cursor: pointer">Yes</button>
                <button class="confirm-no" style="background: #eee; padding: 8px 20px; border: none; border-radius: 4px; cursor: pointer">No</button>
            </div>
        `;

        wrapper.appendChild(dialog);
        document.body.appendChild(wrapper);

        const handleClose = (result) => {
            wrapper.remove();
            resolve(result);
        };

        dialog.querySelector('.confirm-yes').onclick = () => handleClose(true);
        dialog.querySelector('.confirm-no').onclick = () => handleClose(false);
        
        dialog.querySelector('.confirm-yes').focus();
        
        wrapper.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') handleClose(false);
        });
    });
}

function formatErrorMessage(data) {
    if (data.error) {
        return `${data.error.code}: ${data.error.message}`;
    }
    return 'An unexpected error occurred';
}

async function pasteEntry(targetDate) {  
    try {
        const response = await fetch(`/api/v1/entries/${targetDate}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                day: targetDate,
                type: copiedEntry.type,
                logs: copiedEntry.logs
            })
        });

        const data = await response.json();
        if (response.ok) {
            window.location.reload();
        } else {
            showToast(formatErrorMessage(data), 'error');
        }
    } catch (error) {
        showToast('NETWORK_ERROR: Unable to connect to the server', 'error');
        console.error('Error:', error);
    }
}

async function deleteEntry(dateStr) {
    const hoveredRow = document.querySelector('tr:hover');
    if (!hoveredRow) return;
    
    const entryType = hoveredRow.querySelector('.entry-type')?.textContent.trim() || 'entry';
    
    const confirmed = await showConfirmDialog(
        `Are you sure you want to delete this ${entryType} from ${dateStr}?`
    );
    
    if (!confirmed) return;
    
    try {
        const response = await fetch(`/api/v1/entries/${dateStr}`, {
            method: 'DELETE'
        });

        const data = await response.json();
        if (response.ok) {
            window.location.reload();
        } else {
            showToast(formatErrorMessage(data), 'error');
        }
    } catch (error) {
        showToast('NETWORK_ERROR: Unable to connect to the server', 'error');
        console.error('Error:', error);
    }
}

// Add keydown event listener to the document
document.addEventListener('keydown', async (e) => {
    const hoveredRow = document.querySelector('tr:hover');
    if (!hoveredRow) return;

    // Delete functionality (Delete key)
    if (e.key === 'Delete') {
        const entryJson = hoveredRow.dataset.entry;
        if (!entryJson) {
            showToast('VALIDATION_ERROR: No entry available to delete', 'error');
            return;
        }

        const date = hoveredRow.querySelector('td:nth-child(2)').textContent.trim();
        await deleteEntry(date);
        return;
    }

    // Copy functionality (Ctrl + C)
    if (e.ctrlKey && e.key === 'c') {
        const entryJson = hoveredRow.dataset.entry;

        if (!entryJson) {
            showToast('VALIDATION_ERROR: No entry available to copy', 'error');
            return;
        }

        try {
            copiedEntry = JSON.parse(entryJson);
            const date = hoveredRow.querySelector('td:nth-child(2)').textContent.trim();
            showToast(`Entry copied from ${date} (${copiedEntry.type})`, 'success', 5000);
        } catch (error) {
            console.error('Error parsing entry data:', error);
            showToast('PARSE_ERROR: Invalid entry data format', 'error');
        }
    }

    // Paste functionality (Ctrl + V)
    if (e.ctrlKey && e.key === 'v') {
        if (!copiedEntry) {
            showToast('VALIDATION_ERROR: No entry has been copied yet', 'error');
            return;
        }

        if (hoveredRow.dataset.entry) {
            showToast('ENTRY_EXISTS: Cannot paste over existing entry', 'error');
            return;
        }

        const targetDate = hoveredRow.querySelector('td:nth-child(2)').textContent.trim();
        await pasteEntry(targetDate);
    }
});
