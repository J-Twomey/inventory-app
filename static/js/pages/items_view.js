document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.details-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const id = btn.dataset.itemId;
      const row = document.getElementById(`details-${id}`);
      row.style.display = row.style.display === 'none' ? 'table-row' : 'none';
    });
  });
});

document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn = document.getElementById('toggle-search');
  const searchSection = document.getElementById('search-section');

  function setSearchVisible(visible) {
    if (visible) {
      searchSection.classList.add('visible');
      toggleBtn.textContent = 'Hide Search Options';
    } else {
      searchSection.classList.remove('visible');
      toggleBtn.textContent = 'Show Search Options';
    }
  }

  toggleBtn.addEventListener('click', () => {
    const isVisible = searchSection.classList.contains('visible');
    setSearchVisible(!isVisible);
  });

  const params = new URLSearchParams(window.location.search);
  params.delete('show_limit');
  params.delete('skip');

  if (params.size > 0) {
    setSearchVisible(true);
  }
});
