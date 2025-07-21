document.addEventListener('DOMContentLoaded', function() {
    const entryForm = document.getElementById('entryForm');
    const entryType = document.getElementById('entryType');
    const timeLogSection = document.getElementById('timeLogSection');
    const applyToRange = document.getElementById('applyToRange');
    const rangeInputs = document.getElementById('rangeInputs');
    const fromDate = document.getElementById('fromDate');
    const toDate = document.getElementById('toDate');
    const rangePreview = document.getElementById('rangePreview');

    function updateTimeLogVisibility() {
        if (entryType.value === 'work') {
            timeLogSection.removeAttribute('hidden');
        } else {
            timeLogSection.setAttribute('hidden', '');
        }
    }

    function updateRangeVisibility() {
        if (applyToRange.checked) {
            rangeInputs.removeAttribute('hidden');
            updateRangePreview();
        } else {
            rangeInputs.setAttribute('hidden', '');
        }
    }

    function updateRangePreview() {
        if (!fromDate.value || !toDate.value) {
            rangePreview.textContent = '';
            return;
        }

        const dates = generateDateRange(new Date(fromDate.value), new Date(toDate.value));
        const filteredDates = entryType.value === 'work' ? dates.filter(d => !isWeekend(d)) : dates;

        if (filteredDates.length === 0) {
            rangePreview.innerHTML = '<span class="preview-warning">No valid dates in range</span>';
        } else if (filteredDates.length > 10) {
            rangePreview.innerHTML = `<span class="preview-info">Will create ${filteredDates.length} entries</span>`;
        } else {
            const datesList = filteredDates.map(d => d.toLocaleDateString()).join(', ');
            rangePreview.innerHTML = `<span class="preview-info">Dates: ${datesList}</span>`;
        }
    }

    function generateDateRange(start, end) {
        const dates = [];
        const current = new Date(start);
        while (current <= end) {
            dates.push(new Date(current));
            current.setDate(current.getDate() + 1);
        }
        return dates;
    }

    function isWeekend(date) {
        const day = date.getDay();
        return day === 0 || day === 6; // Sunday or Saturday
    }

    entryType.addEventListener('change', () => {
        updateTimeLogVisibility();
        if (applyToRange.checked) {
            updateRangePreview();
        }
    });

    if (applyToRange) {
        applyToRange.addEventListener('change', updateRangeVisibility);
        fromDate.addEventListener('change', updateRangePreview);
        toDate.addEventListener('change', updateRangePreview);
    }

    updateTimeLogVisibility();

    function getMinutesFromTimeInput(timeInput) {
        if (!timeInput.value) return 0;
        const [hours, minutes] = timeInput.value.split(':').map(Number);
        return (hours * 60) + minutes;
    }

    function calculateDuration(row) {
        const startInput = row.querySelector('input[name$="].start"]');
        const endInput = row.querySelector('input[name$="].end"]');
        const pauseInput = row.querySelector('input[name$="].pause"]');
        const durationCell = row.querySelector('.duration');

        if (startInput.value && endInput.value) {
            const start = new Date(`1970-01-01T${startInput.value}`);
            const end = new Date(`1970-01-01T${endInput.value}`);
            let diffMinutes = (end - start) / 1000 / 60;

            const pauseMinutes = getMinutesFromTimeInput(pauseInput);
            diffMinutes -= pauseMinutes;

            if (diffMinutes < 0) {
                diffMinutes += 24 * 60;
            }

            const hours = Math.floor(diffMinutes / 60);
            const minutes = Math.floor(diffMinutes % 60);
            durationCell.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
        } else {
            durationCell.textContent = '';
        }
    }

    function addTimeLogListeners(row) {
        const timeInputs = row.querySelectorAll('.time-input, .pause-input');
        timeInputs.forEach(input => {
            input.addEventListener('change', () => calculateDuration(row));
        });
    }

    // Add listeners to existing rows
    document.querySelectorAll('#timeLogBody tr').forEach(row => {
        addTimeLogListeners(row);
    });

    window.addTimeLog = function() {
        const tbody = document.getElementById('timeLogBody');
        const newIndex = tbody.children.length;
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <div class="time-log" data-index="${newIndex}">
                    <input type="hidden" name="logs[${newIndex}].id" value="">
                    <select name="logs[${newIndex}].type" class="log-type-select">
                        <option value="work">Work</option>
                        <option value="travel">Travel</option>
                    </select>
                </div>
            </td>
            <td><input type="time" name="logs[${newIndex}].start" class="time-input" required></td>
            <td><input type="time" name="logs[${newIndex}].end" class="time-input" required></td>
            <td><input type="time" name="logs[${newIndex}].pause" class="time-input"></td>
            <td class="duration"></td>
            <td>
                <button type="button" class="remove-log-btn" onclick="removeTimeLog(this)">×</button>
            </td>
        `;
        tbody.appendChild(row);
        addTimeLogListeners(row);
    };

    window.removeTimeLog = function(button) {
        const row = button.closest('tr');
        row.remove();
    };

    const isExistingEntry = entryForm.dataset.entryExists === 'true';

    const collectFormData = () => {
        const logs = Array.from(document.querySelectorAll('#timeLogBody tr')).map(row => {
            const index = row.querySelector('.time-log').dataset.index;
            const id = row.querySelector(`input[name="logs[${index}].id"]`).value;
            return {
                id: id ? parseInt(id) : null,
                type: row.querySelector(`select[name="logs[${index}].type"]`).value,
                start: row.querySelector(`input[name="logs[${index}].start"]`).value,
                end: row.querySelector(`input[name="logs[${index}].end"]`).value,
                pause: row.querySelector(`input[name="logs[${index}].pause"]`).value || "00:00"
            };
        });

        const date = window.location.pathname.split('/').filter(Boolean)[1];

        return {
            day: date,
            type: entryType.value,
            logs: entryType.value === 'work' ? logs : []
        };
    };

    function formatErrorMessage(data) {
        if (data.error) {
            return `${data.error.code}: ${data.error.message}`;
        }
        return 'An unexpected error occurred';
    }

    const getReturnPath = () => {
        const urlParams = new URLSearchParams(window.location.search);
        return decodeURIComponent(urlParams.get('return_to') || `/calendar/${new Date().getFullYear()}/${new Date().getMonth() + 1}/view`);
    };

    const returnPath = getReturnPath();

    async function createProgressIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'progressIndicator';
        indicator.innerHTML = `
            <div class="progress-backdrop">
                <div class="progress-modal">
                    <div class="progress-header">Creating entries...</div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                    <div class="progress-text" id="progressText">Starting...</div>
                    <div class="progress-results" id="progressResults"></div>
                </div>
            </div>
        `;
        document.body.appendChild(indicator);
        return indicator;
    }

    function updateProgress(current, total, results) {
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const progressResults = document.getElementById('progressResults');

        const percentage = Math.round((current / total) * 100);
        progressFill.style.width = `${percentage}%`;
        progressText.textContent = `${current} of ${total} entries created`;

        const successful = results.filter(r => r.success).length;
        const failed = results.filter(r => !r.success).length;

        if (current === total) {
            progressResults.innerHTML = `
                <div class="results-summary">
                    <div class="success-count">✓ ${successful} created</div>
                    ${failed > 0 ? `<div class="error-count">✗ ${failed} failed</div>` : ''}
                </div>
                ${failed > 0 ? `<div class="error-details">
                    ${results.filter(r => !r.success).map(r =>
                        `<div class="error-item">${r.date}: ${r.error}</div>`
                    ).join('')}
                </div>` : ''}
                <button onclick="document.getElementById('progressIndicator').remove(); window.location.href='${returnPath}'" class="continue-btn">Continue</button>
            `;
        }
    }

    async function createRangeEntries() {
        const dates = generateDateRange(new Date(fromDate.value), new Date(toDate.value));
        const filteredDates = entryType.value === 'work' ? dates.filter(d => !isWeekend(d)) : dates;

        if (filteredDates.length === 0) {
            throw new Error('No valid dates in range');
        }

        const progressIndicator = await createProgressIndicator();
        const results = [];

        for (let i = 0; i < filteredDates.length; i++) {
            const date = filteredDates[i];
            const dateStr = date.toISOString().split('T')[0];

            try {
                const response = await fetch(`/api/v1/entries/${dateStr}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        day: dateStr,
                        type: entryType.value,
                        logs: entryType.value === 'work' ? collectFormData().logs : []
                    })
                });

                const data = await response.json();
                if (response.ok) {
                    results.push({ date: dateStr, success: true });
                } else {
                    results.push({ date: dateStr, success: false, error: formatErrorMessage(data) });
                }
            } catch (error) {
                results.push({ date: dateStr, success: false, error: 'Network error' });
            }

            updateProgress(i + 1, filteredDates.length, results);
        }

        return results;
    }

    entryForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const errorMessage = document.getElementById('errorMessage');
        errorMessage.setAttribute('hidden', '');

        try {
            if (applyToRange && applyToRange.checked) {
                await createRangeEntries();
            } else {
                const apiPath = `/api/v1${window.location.pathname.replace('/view', '')}`;
                const method = isExistingEntry ? 'PATCH' : 'POST';
                const response = await fetch(apiPath, {
                    method,
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(collectFormData())
                });

                const data = await response.json();
                if (response.ok) {
                    window.location.href = returnPath;
                } else {
                    errorMessage.textContent = formatErrorMessage(data);
                    errorMessage.removeAttribute('hidden');
                }
            }
        } catch (error) {
            console.error('Error submitting form:', error);
            errorMessage.textContent = typeof error === 'string' ? error : 'NETWORK_ERROR: Unable to connect to the server. Please try again.';
            errorMessage.removeAttribute('hidden');
        }
    });
});
