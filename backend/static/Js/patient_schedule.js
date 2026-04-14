const filterInputs = document.querySelectorAll('input[name="medication-filter"]');
const scheduleRows = document.querySelectorAll('.schedule-row');

filterInputs.forEach(input => {
    input.addEventListener('change', () => {
        const selectedValue = input.value;

        scheduleRows.forEach(row => {
            const medicationName = row.dataset.medication;

            if (selectedValue === 'all' || medicationName === selectedValue) {
                row.style.display = 'grid';
            } else {
                row.style.display = 'none';
            }
        });
    });
});