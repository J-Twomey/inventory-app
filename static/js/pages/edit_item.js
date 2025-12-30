import { getOriginalFormValues, disableUnchangedFields } from '../helpers/form_utils.js';

document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('form');
  if (!form) return;

  const originalValues = getOriginalFormValues(form);

  form.addEventListener('submit', () => {
    disableUnchangedFields(form, originalValues);
  });
});
