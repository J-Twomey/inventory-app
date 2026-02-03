import { initDetailsToggle } from '../helpers/toggles.js';


// Function to fetch item info via AJAX
async function fetchItemInfo(itemId) {
  const response = await fetch(`/item_info_for_submission_form/${itemId}`);
  if (!response.ok) return { name: '', purchase_price: '' };
  return await response.json();
}

// Function to update the values for a row given an item id
async function updateRowFromItemId(inputRow) {
  const row = inputRow.closest('tr');
  const itemId = inputRow.value;
  if (!itemId) return;
  const data = await fetchItemInfo(itemId);
  row.querySelector('.item-name').textContent = data.name || '';
  row.querySelector('.item-set').textContent = data.set_name || '';
  row.querySelector('.item-type').textContent = data.category || '';
  row.querySelector('.item-language').textContent = data.language || '';
  row.querySelector('.item-intent').textContent = data.intent || '';
  row.querySelector('.item-purchase-date').textContent = data.purchase_date || '';
  row.querySelector('.item-purchase-price').textContent = data.purchase_price != null
    ? Number(data.purchase_price).toLocaleString('ja-JP', {
        style: 'currency',
        currency: 'JPY',
      })
    : '';
  row.querySelector('.item-status').textContent = data.status || '';
  row.querySelector('.item-qualifiers').textContent = (data.qualifiers || []).join(', ');
  row.querySelector('.item-details').textContent = data.details || '';
}

// Function to attach event listener to a row's item_id input
function attachItemIdListener(input) {
  input.addEventListener('change', () => {
    updateRowFromItemId(input);
  });
}

function setupRow(row) {
  // Attach item-id listener
  const input = row.querySelector('.item-id-input');
  attachItemIdListener(input);

  // Attach delete button
  const deleteBtn = row.querySelector('.delete-row-btn');
  deleteBtn.addEventListener('click', () => {
    row.remove();
    saveFormState();
  });

  // Attach insert button
  const insertBtn = row.querySelector('.insert-row-btn');
  insertBtn.addEventListener('click', () => {
    const newRow = createRow();
    row.parentNode.insertBefore(newRow, row);
    saveFormState();
  });
}

// Function to create a new table row
function createRow() {
  const newRow = document.createElement('tr');
  newRow.innerHTML = `
    <td>
      <button type="button" class="open-item-search">Select</button>
    </td>
    <td>
      <input type="number" name="item_ids" class="item-id-input" required>
    </td>
    <td class="item-name"></td>
    <td class="item-set"></td>
    <td class="item-type"></td>
    <td class="item-language"></td>
    <td class="item-intent"></td>
    <td class="item-purchase-date"></td>
    <td class="item-purchase-price"></td>
    <td class="item-status"></td>
    <td class="item-qualifiers"></td>
    <td class="item-details"></td>
    <td class="functions-col">
      <button type="button" class="insert-row-btn">↑</button>
      <button type="button" class="delete-row-btn">Del</button>
    </td>
  `;
  setupRow(newRow);
  return newRow;
}

// Save form state into localStorage
function saveFormState() {
  const formState = {
    submission_number: document.querySelector('[name="submission_number"]').value,
    submission_company: document.querySelector('[name="submission_company"]').value,
    submission_date: document.querySelector('[name="submission_date"]').value,
    item_ids: Array.from(document.querySelectorAll('.item-id-input')).map(input => input.value)
  };
  localStorage.setItem('submissionForm', JSON.stringify(formState));
}

function restoreFormState() {
  const saved = localStorage.getItem('submissionForm');
  if (!saved) return;

  const formState = JSON.parse(saved);

  // Restore top-level fields
  const companySelect = document.querySelector('[name="submission_company"]');
  if (companySelect) companySelect.value = formState.submission_company || '';

  const numInput = document.querySelector('[name="submission_number"]');
  if (numInput && formState?.submission_number !== undefined) {
    numInput.value = formState.submission_number;
  }

  const subDate = document.querySelector('[name="submission_date"]')
  if (subDate) subDate.value = formState.submission_date || '';

  // Clear existing rows
  tableBody.innerHTML = '';

  // Rebuild rows and attach listeners
  formState.item_ids.forEach(() => {
    const row = createRow(true);
    tableBody.appendChild(row);
  });

  // Fill in input values and update rows
  const itemInputs = document.querySelectorAll('.item-id-input');
  itemInputs.forEach((input, idx) => {
    input.value = formState.item_ids[idx] || '';
    if (input.value) {
      updateRowFromItemId(input);
    }
  });

  // Ensure at least one empty row exists
  if (tableBody.children.length === 0) {
    tableBody.appendChild(createRow(true));
  }
  return true;
}

const addRowBtn = document.getElementById('add-row');
const tableBody = document.querySelector('#submissions-table tbody');

// Add new row dynamically
addRowBtn.addEventListener('click', () => {
  const newRow = createRow();
  tableBody.appendChild(newRow);
  saveFormState();
});

document.addEventListener('DOMContentLoaded', () => {
  // Restore state on load
  const restored = restoreFormState();

  // If no restored state then set-up existing rows
  if (!restored) {
    document.querySelectorAll('#submissions-table tbody tr').forEach(row => {
      setupRow(row);
    });
  }

  // Save whenever inputs change
  document.addEventListener('input', saveFormState);
});

// Dialog box for item ID search
const dialog = document.getElementById('item-selection-dialog');
const content = document.getElementById('item-selection-content');

let activeRow = null;

// Open the selection dialog (per-row Select button)
document.addEventListener('click', async (e) => {
  const openBtn = e.target.closest('.open-item-search');
  if (!openBtn) return;

  activeRow = openBtn.closest('tr');

  const response = await fetch('/items_lookup?selection_mode=1');
  content.innerHTML = await response.text();
  initDetailsToggle(content);
  dialog.showModal();
});

// Close the dialog when click outside the modal
dialog.addEventListener('click', (e) => {
  const panel = dialog.querySelector('.dialog-panel');
  if (!panel) return;

  if (!panel.contains(e.target)) {
    dialog.close();
    activeRow = null;
  }
});

// Handle item selection inside the dialog
document.addEventListener('click', (e) => {
  const selectBtn = e.target.closest('.select-item');
  if (!selectBtn || !activeRow) return;

  const itemId = selectBtn.dataset.itemId;

  const input = activeRow.querySelector('.item-id-input');
  if (input) {
    input.value = itemId;
    updateRowFromItemId(input);
  }

  dialog.close();
  activeRow = null;
  saveFormState();
});

// Change page
document.addEventListener('click', async (e) => {
  if (!dialog.open) return;

  const link = e.target.closest('a');
  if (!link) return;

  const href = link.getAttribute('href');
  if (!href || href === 'none' || href.startsWith('#')) return;

  const url = new URL(href, window.location.origin);
  if (url.pathname !== '/items_lookup') return;

  e.preventDefault();

  const response = await fetch(url.toString());
  content.innerHTML = await response.text();
});

// Item search submit
document.addEventListener('submit', async (e) => {
  if (!dialog.open) return;

  const form = e.target.closest('form');
  if (!form) return;
  if (form.id !== 'items-lookup-form') return;

  e.preventDefault();

  const url = form.action + '?' + new URLSearchParams(new FormData(form));
  const response = await fetch(url);
  content.innerHTML = await response.text();
});
