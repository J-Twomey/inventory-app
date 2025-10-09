function toggleDetails(id) {
  const row = document.getElementById(`details-${id}`);
  row.style.display = row.style.display === 'none' ? 'table-row' : 'none';
}

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

  // Auto-show if there are query parameters in the URL
  const params = new URLSearchParams(window.location.search);
  if ([...params.values()].some(v => v.trim() !== '')) {
    setSearchVisible(true);
  }
});

