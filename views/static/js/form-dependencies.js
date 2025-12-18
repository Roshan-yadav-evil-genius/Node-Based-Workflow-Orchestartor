/**
 * Node Engine POC - Form Dependencies
 * Handles cascading dropdown field updates
 */

/**
 * Set up change listeners for parent fields with dependencies
 */
function setupDependencyListeners() {
    Object.keys(currentFormDependencies).forEach(function(parentField) {
        var parentElement = document.querySelector('[data-field-name="' + parentField + '"]');
        if (parentElement) {
            parentElement.addEventListener('change', function() {
                handleParentFieldChange(parentField, this.value);
            });
        }
    });
}

/**
 * Handle parent field value change
 * Fetches new options for dependent fields
 */
function handleParentFieldChange(parentField, parentValue) {
    var dependentFields = currentFormDependencies[parentField] || [];
    
    dependentFields.forEach(function(dependentField) {
        // Clear and disable dependent field while loading
        var dependentElement = document.querySelector('[data-field-name="' + dependentField + '"]');
        if (dependentElement && dependentElement.tagName === 'SELECT') {
            dependentElement.innerHTML = '<option value="">Loading...</option>';
            dependentElement.disabled = true;
            
            // Also clear any fields that depend on this field (cascade)
            clearDependentFields(dependentField);
        }
        
        // Fetch new options from API
        fetch('/api/node/' + encodeURIComponent(currentNodeIdentifier) + '/form/field-options', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                parent_field: parentField,
                parent_value: parentValue,
                dependent_field: dependentField
            })
        })
        .then(function(response) { return response.json(); })
        .then(function(data) {
            var selectElement = document.querySelector('[data-field-name="' + dependentField + '"]');
            if (selectElement && selectElement.tagName === 'SELECT') {
                selectElement.innerHTML = '<option value="">-- Select --</option>';
                if (data.options && data.options.length > 0) {
                    data.options.forEach(function(opt) {
                        var option = document.createElement('option');
                        option.value = opt.value;
                        option.textContent = opt.text;
                        selectElement.appendChild(option);
                    });
                }
                selectElement.disabled = false;
            }
        })
        .catch(function(error) {
            console.error('Error fetching field options:', error);
            var selectElement = document.querySelector('[data-field-name="' + dependentField + '"]');
            if (selectElement) {
                selectElement.innerHTML = '<option value="">Error loading options</option>';
                selectElement.disabled = false;
            }
        });
    });
}

/**
 * Recursively clear dependent fields
 */
function clearDependentFields(parentField) {
    var dependentFields = currentFormDependencies[parentField] || [];
    dependentFields.forEach(function(dependentField) {
        var element = document.querySelector('[data-field-name="' + dependentField + '"]');
        if (element && element.tagName === 'SELECT') {
            element.innerHTML = '<option value="">-- Select --</option>';
        }
        // Recursively clear children
        clearDependentFields(dependentField);
    });
}

