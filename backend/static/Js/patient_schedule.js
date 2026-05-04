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
document.querySelectorAll(".mark-taken-btn").forEach(button => {
    button.addEventListener("click", async () => {
        const time = button.dataset.time;
        try {
            const res = await fetch("/log-dose", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ time })
            });
            if (!res.ok) throw new Error();
            // reload page to update UI
            location.reload();
        } catch (err) {
            alert("Failed to log dose");
        }
    });
});