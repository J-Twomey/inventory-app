const trackedInputTypes = ['text', 'number', 'hidden', 'date'];

export function getOriginalFormValues(form) {
    const values = {};
    for (const input of form.elements) {
        if (!input.name) continue;

        if (trackedInputTypes.includes(input.type) ||
            input.tagName.toLowerCase() === 'select') {
        values[input.name] = input.value;
        } else if (input.type === 'checkbox') {
        values[input.name] = input.checked;
        }
    }
    return values;
}

export function disableUnchangedFields(form, originalValues) {
    for (const input of form.elements) {
        const name = input.name;
        if (!name) continue;

        if (trackedInputTypes.includes(input.type) ||
            input.tagName.toLowerCase() === 'select') {
        if (input.value === originalValues[name]) {
            input.disabled = true;
        }
        } else if (input.type === 'checkbox') {
        if (input.checked === originalValues[name]) {
            input.disabled = true;
        }
        }
    }
}
