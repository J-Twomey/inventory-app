import { addNewGradingFeeRow } from './grading_fees_container.js';
import { getOriginalFormValues, disableUnchangedFields } from './form_utils.js';

document.getElementById('grading-fees-container').addEventListener('input', addNewGradingFeeRow);

document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('form');
  if (!form) return;

  const originalValues = getOriginalFormValues(form);

  form.addEventListener('submit', () => {
    disableUnchangedFields(form, originalValues);
  });
});
