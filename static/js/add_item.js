function addNewGradingFeeRow() {
    const container = document.getElementById('grading-fees-container');
    const rows = container.querySelectorAll('.grading-fee-row');
    const lastRow = rows[rows.length - 1];
    const key = lastRow.querySelector('input[name="submission_numbers"]').value;
    const value = lastRow.querySelector('input[name="grading_fees"]').value;

    if (key !== '' && value !== '') {
        const newRow = document.createElement('div');
        newRow.className = 'grading-fee-row';
        newRow.innerHTML = `
            <input type="number" name="submission_numbers" placeholder="Sub#" />
            <input type="number" name="grading_fees" placeholder="Fee" />
        `;
        container.appendChild(newRow);
    }
}

document.getElementById('grading-fees-container').addEventListener('input', addNewGradingFeeRow);
