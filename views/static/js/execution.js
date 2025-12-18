/**
 * Node Engine POC - Execution Popup
 * Handles node execution with input/output panels
 */

/**
 * Open execution popup for a node
 */
function openExecutionPopup(identifier, nodeName) {
    currentNodeIdentifier = identifier;
    
    // Update popup header
    document.getElementById('executionNodeName').textContent = nodeName;
    
    // Set default input JSON
    document.getElementById('executionInput').value = JSON.stringify(defaultInputJson, null, 2);
    
    // Reset output
    document.getElementById('executionOutput').innerHTML = `
        <div class="output-placeholder">
            <i class="bi bi-play-circle"></i>
            <p>Click Execute to run the node and see the output</p>
        </div>
    `;
    
    // Show popup
    document.getElementById('executionOverlay').classList.add('show');
    
    // Load form fields
    loadExecutionForm(identifier);
}

/**
 * Close execution popup
 */
function closeExecutionPopup() {
    document.getElementById('executionOverlay').classList.remove('show');
    currentNodeIdentifier = null;
    currentNodeFormFields = [];
    currentFormDependencies = {};
}

/**
 * Load form fields for execution
 */
function loadExecutionForm(identifier) {
    var formContent = document.getElementById('executionFormContent');
    formContent.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
    
    fetch('/api/node/' + encodeURIComponent(identifier) + '/form')
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.form && data.form.fields && data.form.fields.length > 0) {
                currentNodeFormFields = data.form.fields;
                currentFormDependencies = data.form.dependencies || {};
                formContent.innerHTML = renderExecutionFormFields(data.form.fields);
                // Set up dependency listeners after rendering
                setupDependencyListeners();
            } else {
                currentNodeFormFields = [];
                currentFormDependencies = {};
                formContent.innerHTML = `
                    <div class="output-placeholder">
                        <i class="bi bi-file-earmark-x"></i>
                        <p>This node has no form fields</p>
                    </div>
                `;
            }
        })
        .catch(function(error) {
            formContent.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Error loading form: ${error.message}
                </div>
            `;
        });
}

/**
 * Render form fields for execution
 */
function renderExecutionFormFields(fields) {
    var html = '';
    
    fields.forEach(function(field, index) {
        var fieldId = 'exec_field_' + index;
        var fieldName = field.name || 'field_' + index;
        var label = field.label || field.name || 'Field';
        var isRequired = field.required === true;
        
        html += '<div class="form-field">';
        html += '<label for="' + fieldId + '">' + escapeHtml(label);
        if (isRequired) {
            html += '<span class="field-required" style="color: #dc3545; margin-left: 2px;">*</span>';
        }
        html += '</label>';
        
        // Render input based on field type
        if (field.tag === 'select') {
            html += '<select class="form-select" id="' + fieldId + '" data-field-name="' + fieldName + '">';
            var options = field.options || [];
            if (options.length === 0) {
                html += '<option value="">-- Select --</option>';
            }
            options.forEach(function(opt) {
                var selected = opt.selected ? ' selected' : '';
                html += '<option value="' + escapeHtml(opt.value) + '"' + selected + '>' + escapeHtml(opt.text) + '</option>';
            });
            html += '</select>';
        } else if (field.tag === 'textarea') {
            html += '<textarea id="' + fieldId + '" data-field-name="' + fieldName + '" rows="3" placeholder="' + escapeHtml(field.placeholder || '') + '"></textarea>';
        } else if (field.type === 'checkbox') {
            html += '<div><input type="checkbox" id="' + fieldId + '" data-field-name="' + fieldName + '"> <span>' + escapeHtml(label) + '</span></div>';
        } else {
            var inputType = field.type || 'text';
            if (inputType === 'number') {
                var min = field.min !== undefined ? ' min="' + field.min + '"' : '';
                var max = field.max !== undefined ? ' max="' + field.max + '"' : '';
                html += '<input type="number" id="' + fieldId + '" data-field-name="' + fieldName + '"' + min + max + ' placeholder="' + escapeHtml(field.placeholder || '') + '">';
            } else {
                html += '<input type="' + inputType + '" id="' + fieldId + '" data-field-name="' + fieldName + '" placeholder="' + escapeHtml(field.placeholder || '') + '">';
            }
        }
        
        html += '</div>';
    });
    
    return html;
}

/**
 * Collect form data from execution form
 */
function collectFormData() {
    var formData = {};
    
    currentNodeFormFields.forEach(function(field, index) {
        var fieldId = 'exec_field_' + index;
        var fieldName = field.name || 'field_' + index;
        var element = document.getElementById(fieldId);
        
        if (element) {
            if (element.type === 'checkbox') {
                formData[fieldName] = element.checked;
            } else {
                formData[fieldName] = element.value;
            }
        }
    });
    
    return formData;
}

/**
 * Execute the current node
 */
function executeNode() {
    if (!currentNodeIdentifier) {
        alert('No node selected');
        return;
    }
    
    var btn = document.getElementById('btnExecute');
    var outputEl = document.getElementById('executionOutput');
    
    // Get input JSON
    var inputText = document.getElementById('executionInput').value;
    var inputData;
    
    try {
        inputData = JSON.parse(inputText);
    } catch (e) {
        outputEl.innerHTML = `
            <div class="output-error">
                <pre>Error: Invalid input JSON\n${e.message}</pre>
            </div>
        `;
        return;
    }
    
    // Get form data
    var formData = collectFormData();
    
    // Show loading state
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Executing...';
    outputEl.innerHTML = `
        <div class="output-placeholder">
            <div class="spinner-border text-light" role="status">
                <span class="visually-hidden">Executing...</span>
            </div>
            <p>Executing node...</p>
        </div>
    `;
    
    // Call execute API
    fetch('/api/node/' + encodeURIComponent(currentNodeIdentifier) + '/execute', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            input_data: inputData,
            form_data: formData
        })
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        btn.disabled = false;
        btn.innerHTML = 'Execute';
        
        if (data.error) {
            outputEl.innerHTML = `
                <div class="output-error">
                    <pre>${syntaxHighlight(JSON.stringify(data, null, 2))}</pre>
                </div>
            `;
        } else {
            outputEl.innerHTML = `<pre>${syntaxHighlight(JSON.stringify(data.output || data, null, 2))}</pre>`;
        }
    })
    .catch(function(error) {
        btn.disabled = false;
        btn.innerHTML = 'Execute';
        outputEl.innerHTML = `
            <div class="output-error">
                <pre>Error: ${error.message}</pre>
            </div>
        `;
    });
}

