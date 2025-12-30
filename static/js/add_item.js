document.addEventListener('DOMContentLoaded', () => {
  const purchaseDateInput = document.getElementById('purchase_date');
  const today = new Date().toISOString().split('T')[0];
  purchaseDateInput.value = today;

  const changeDateBy = (days) => {
    if (!purchaseDateInput.value) return;
    const currentDate = new Date(purchaseDateInput.value);
    currentDate.setDate(currentDate.getDate() + days);
    purchaseDateInput.value = currentDate.toISOString().split('T')[0];
  };

  document.getElementById('date-decrease').addEventListener('click', () => changeDateBy(-1));
  document.getElementById('date-increase').addEventListener('click', () => changeDateBy(1));
});
