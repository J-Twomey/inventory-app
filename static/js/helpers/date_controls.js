export function attachDateControls({
  inputId,
  decreaseBtnId,
  increaseBtnId,
  setTodayByDefault = true,
}) {
  const input = document.getElementById(inputId);
  const decBtn = document.getElementById(decreaseBtnId);
  const incBtn = document.getElementById(increaseBtnId);

  if (!input || !decBtn || !incBtn) return;

  if (setTodayByDefault && !input.value) {
    input.value = new Date().toISOString().split('T')[0];
  }

  const changeDateBy = (days) => {
    if (!input.value) return;
    const date = new Date(input.value);
    date.setDate(date.getDate() + days);
    input.value = date.toISOString().split('T')[0];
  };

  decBtn.addEventListener('click', () => changeDateBy(-1));
  incBtn.addEventListener('click', () => changeDateBy(1));
}
