import { attachDateControls } from '../helpers/date_controls.js';

document.addEventListener('DOMContentLoaded', () => {
  attachDateControls({
    inputId: 'purchase_date',
    decreaseBtnId: 'date-decrease',
    increaseBtnId: 'date-increase',
  });
});
