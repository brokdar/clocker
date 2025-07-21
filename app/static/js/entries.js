document.addEventListener('DOMContentLoaded', function() {
    const entryForm = document.getElementById('entryForm');
    const entryType = document.getElementById('entryType');
    const timeLogSection = document.getElementById('timeLogSection');

    function updateTimeLogVisibility() {
        if (entryType.value === 'work') {
            timeLogSection.removeAttribute('hidden');
        } else {
            timeLogSection.setAttribute('hidden', '');
        }
    }

    entryType.addEventListener('change', updateTimeLogVisibility);
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

    entryForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const errorMessage = document.getElementById('errorMessage');
        errorMessage.setAttribute('hidden', '');

        try {
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
        } catch (error) {
            console.error('Error submitting form:', error);
            errorMessage.textContent = 'NETWORK_ERROR: Unable to connect to the server. Please try again.';
            errorMessage.removeAttribute('hidden');
        }
    });
});
