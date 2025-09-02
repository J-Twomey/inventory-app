let rowCount = 1;

const addRowBtn = document.getElementById('add-row');
const tableBody = document.querySelector('#submissions-table tbody');

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
  row.querySelector('.item-purchase-price').textContent = data.purchase_price || '';
  row.querySelector('.item-status').textContent = data.status || '';
  row.querySelector('.item-qualifiers').textContent = data.qualifiers || '';
  row.querySelector('.item-details').textContent = data.details || '';
}

// Function to attach event listener to a row's item_id input
function attachItemIdListener(input) {
  input.addEventListener('change', () => {
    updateRowFromItemId(input);
  });
}

// Repopulate rows with data if the form is reloaded
document.addEventListener('DOMContentLoaded', () => {
  const itemInputs = document.querySelectorAll('.item-id-input');

  itemInputs.forEach(input => {
    attachItemIdListener(input);

    if (input.value) {
      updateRowFromItemId(input);
    }
  });
});

// Attach listeners to the initial row
document.querySelectorAll('.item-id-input').forEach(attachItemIdListener);
document.querySelectorAll('.delete-row-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    btn.closest('tr').remove();
  });
});

// Add new row dynamically
addRowBtn.addEventListener('click', () => {
  rowCount += 1;

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
    <td class="del-col"><button type="button" class="delete-row-btn">Del</button></td>
  `;

  tableBody.appendChild(newRow);

  // Attach listener to the new input
  const newInput = newRow.querySelector('.item-id-input');
  attachItemIdListener(newInput);

  // Attach delete button handler
  const deleteBtn = newRow.querySelector('.delete-row-btn');
  deleteBtn.addEventListener('click', () => {
    newRow.remove();
  });
});
