export function initDetailsToggle(root = document) {
  root.querySelectorAll('.details-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const id = btn.dataset.itemId;
      const row = document.getElementById(`details-${id}`);
      if (!row) return;

      row.style.display =
        row.style.display === 'none' ? 'table-row' : 'none';
    });
  });
}
