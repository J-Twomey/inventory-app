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

// Function to initialise existing rows
function initExistingRows() {
  document.querySelectorAll('tr').forEach(row => {
    // Populate cached data
    const input = row.querySelector('.item-id-input');
    if (input.value) updateRowFromItemId(input);

    setupRow(row);
  });
};

// Function to create a new table row
function createRow() {
  const newRow = document.createElement('tr');
  newRow.innerHTML = `
    <td><input type="number" name="item_ids" class="item-id-input" required></td>
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
    item_ids: Array.from(document.querySelectorAll('.item-id-input')).map(input => input.value)
  };
  localStorage.setItem('submissionForm', JSON.stringify(formState));
}

function restoreFormState() {
  const saved = localStorage.getItem('submissionForm');
  if (!saved) return;

  const formState = JSON.parse(saved);

  // Restore top-level fields
  const numInput = document.querySelector('[name="submission_number"]');
  const companySelect = document.querySelector('[name="submission_company"]');
  if (numInput) numInput.value = formState.submission_number || '';
  if (companySelect) companySelect.value = formState.submission_company || '';

  // Clear existing rows
  tableBody.innerHTML = '';

  // Rebuild rows and attach listeners immediately
  formState.item_ids.forEach(() => {
    const row = createRow(true); // true = attach listeners immediately
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
  restoreFormState();

  // Save whenever inputs change
  document.addEventListener('input', saveFormState);
});
