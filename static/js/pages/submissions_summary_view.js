document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('td.editable-date').forEach(cell => {
    cell.addEventListener('click', () => {
      // Avoid multiple active inputs in the same cell
      if (cell.querySelector('input')) return;

      const oldValue = cell.textContent.trim();

      // Create the date input
      const input = document.createElement('input');
      input.type = 'date';
      input.classList.add('inline-input-date');
      input.value = oldValue || ''; // expects YYYY-MM-DD format
      cell.textContent = '';
      cell.appendChild(input);
      input.focus();

      // Function to save and restore cell text
      const save = () => {
        const newValue = input.value;
        cell.textContent = newValue;
        if (newValue !== oldValue) {
          // Send update to backend
          fetch('/submissions_summary_edit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              submission_number: cell.dataset.id,
              field: cell.dataset.field,
              value: newValue
            })
          });
        }
      };

      // Save on blur or Enter
      input.addEventListener('blur', save);
      input.addEventListener('keydown', e => {
        if (e.key === 'Enter') input.blur();
      });
    });
  });
});
