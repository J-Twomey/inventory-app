document.addEventListener('DOMContentLoaded', () => {
  const params = new URLSearchParams(window.location.search);
  if (params.get('submitted') === '1') {
    localStorage.removeItem('submissionForm');
  }
});