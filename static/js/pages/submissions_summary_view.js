function showInlineError(cell, message) {
  const existing = cell.querySelector('.inline-error');
  if (existing) existing.remove();

  const tooltip = document.createElement('div');
  tooltip.className = 'inline-error';
  tooltip.textContent = message;

  document.body.appendChild(tooltip);

  const rect = cell.getBoundingClientRect();

  tooltip.style.left = rect.left + window.scrollX + 'px';
  tooltip.style.top = rect.bottom + window.scrollY + 4 + 'px';

  setTimeout(() => {
    tooltip.remove();
  }, 2000);
}


document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('td.editable').forEach(cell => {
    cell.addEventListener('click', () => {
      if (cell.querySelector('input, select')) return;

      const oldValue = cell.textContent.trim();
      const type = cell.dataset.type;
      let input;

      if (type === 'date') {
        input = document.createElement('input');
        input.type = 'date';
        input.value = oldValue || '';

      } else if (type === 'int') {
        input = document.createElement('input');
        input.type = 'number';
        input.step = '1';
        input.value = oldValue || '';

      } else if (type === 'select') {
        input = document.createElement('select');
        const options = cell.dataset.options.split(',');

        options.forEach(opt => {
          const option = document.createElement('option');
          option.value = opt;
          option.textContent = opt;
          if (opt === oldValue) option.selected = true;
          input.appendChild(option);
        });
      }

      input.classList.add('inline-input');
      cell.textContent = '';
      cell.appendChild(input);
      input.focus();

    const save = () => {
      const newValue = input.value;

      setTimeout(() => {
        cell.textContent = newValue;
      }, 0);

      if (newValue !== oldValue) {
        fetch(window.location.origin + '/submissions_summary_edit', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            submission_id: cell.dataset.id,
            field: cell.dataset.field,
            value: newValue
          })
        })
        .then(res => {
          return res.json();
        })
        .then(data => {
          if (!data.success) {
            cell.textContent = oldValue;
            showInlineError(cell, data.error_message);
          }
        })
      }
    };

      input.addEventListener('blur', save);
      input.addEventListener('keydown', e => {
        if (e.key === 'Enter') input.blur();
        if (e.key === 'Escape') cell.textContent = oldValue;
      });
    });
  });
});
