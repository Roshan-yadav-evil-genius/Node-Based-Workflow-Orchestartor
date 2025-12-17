/**
 * Node Engine POC - Node Details Modal
 * Handles showing node details and form preview
 */

/**
 * Show node details in modal
 */
function showNodeDetails(identifier) {
    var modal = new bootstrap.Modal(document.getElementById('nodeDetailsModal'));
    var contentEl = document.getElementById('nodeDetailsContent');
    
    // Show loading state
    contentEl.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
    
    modal.show();
    
    // Fetch node form data
    fetch('/api/node/' + encodeURIComponent(identifier) + '/form')
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            renderNodeDetails(data, contentEl);
        })
        .catch(function(error) {
            contentEl.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Error loading node details: ${error.message}
                </div>
            `;
        });
}

/**
 * Render node details content
 */
function renderNodeDetails(data, containerEl) {
    var node = data.node || {};
    var form = data.form;
    
    var html = `
        <div class="node-details-header">
            <h4>${escapeHtml(node.name) || 'Unknown Node'}</h4>
            <span class="badge bg-light text-dark">${escapeHtml(node.type) || 'Unknown Type'}</span>
            ${form ? '<span class="badge bg-success ms-2">Has Form</span>' : '<span class="badge bg-secondary ms-2">No Form</span>'}
            <div class="node-meta">
                <div class="node-meta-item">
                    <label>Identifier</label>
                    <span>${escapeHtml(node.identifier) || '-'}</span>
                </div>
                <div class="node-meta-item">
                    <label>Label</label>
                    <span>${escapeHtml(node.label) || '-'}</span>
                </div>
                <div class="node-meta-item">
                    <label>Description</label>
                    <span>${escapeHtml(node.description) || '-'}</span>
                </div>
                <div class="node-meta-item">
                    <label>Form Class</label>
                    <span>${escapeHtml(node.form_class) || '-'}</span>
                </div>
            </div>
        </div>
    `;
    
    if (form && form.fields && form.fields.length > 0) {
        html += `
            <ul class="nav nav-tabs form-tabs" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="rendered-tab" data-bs-toggle="tab" data-bs-target="#rendered-pane" type="button" role="tab">
                        <i class="bi bi-ui-checks me-2"></i>Rendered Form
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="json-tab" data-bs-toggle="tab" data-bs-target="#json-pane" type="button" role="tab">
                        <i class="bi bi-braces me-2"></i>JSON Schema
                    </button>
                </li>
            </ul>
            
            <div class="tab-content">
                <div class="tab-pane fade show active" id="rendered-pane" role="tabpanel">
                    <div class="rendered-form">
                        ${renderFormFields(form.fields)}
                    </div>
                </div>
                <div class="tab-pane fade" id="json-pane" role="tabpanel">
                    <div class="json-container">
                        <pre>${syntaxHighlight(JSON.stringify(form, null, 2))}</pre>
                    </div>
                </div>
            </div>
        `;
    } else {
        html += `
            <div class="no-form-message">
                <i class="bi bi-file-earmark-x d-block"></i>
                <h5>No Form Configuration</h5>
                <p class="text-muted mb-0">${escapeHtml(data.message) || 'This node does not have a form definition.'}</p>
            </div>
        `;
    }
    
    containerEl.innerHTML = html;
}

/**
 * Render form fields for preview
 */
function renderFormFields(fields) {
    var html = '';
    
    fields.forEach(function(field) {
        var fieldHtml = '<div class="form-field">';
        
        // Label
        var label = field.label || field.name || 'Field';
        var isRequired = field.required === true;
        fieldHtml += '<label>' + escapeHtml(label);
        if (isRequired) {
            fieldHtml += '<span class="field-required">*</span>';
        }
        fieldHtml += '</label>';
        
        // Render input based on tag type
        if (field.tag === 'select' && field.options) {
            fieldHtml += '<select class="form-select">';
            field.options.forEach(function(opt) {
                var selected = opt.selected ? ' selected' : '';
                fieldHtml += '<option value="' + escapeHtml(opt.value) + '"' + selected + '>' + escapeHtml(opt.text) + '</option>';
            });
            fieldHtml += '</select>';
        } else if (field.tag === 'textarea') {
            fieldHtml += '<textarea rows="3" placeholder="' + escapeHtml(field.placeholder || '') + '"></textarea>';
        } else if (field.type === 'checkbox') {
            fieldHtml += '<div><input type="checkbox"> <span>' + escapeHtml(label) + '</span></div>';
        } else {
            var inputType = field.type || 'text';
            if (inputType === 'number') {
                var min = field.min !== undefined ? ' min="' + field.min + '"' : '';
                var max = field.max !== undefined ? ' max="' + field.max + '"' : '';
                fieldHtml += '<input type="number"' + min + max + ' placeholder="' + escapeHtml(field.placeholder || '') + '">';
            } else {
                fieldHtml += '<input type="' + inputType + '" placeholder="' + escapeHtml(field.placeholder || '') + '">';
            }
        }
        
        // Field metadata badges
        fieldHtml += '<div class="field-meta">';
        if (isRequired) {
            fieldHtml += '<span class="field-meta-badge required">Required</span>';
        }
        if (field.type) {
            fieldHtml += '<span class="field-meta-badge type">' + escapeHtml(field.type) + '</span>';
        }
        if (field.tag) {
            fieldHtml += '<span class="field-meta-badge">' + escapeHtml(field.tag) + '</span>';
        }
        fieldHtml += '</div>';
        
        // Help text
        if (field.help_text) {
            fieldHtml += '<div class="form-help">' + escapeHtml(field.help_text) + '</div>';
        }
        
        fieldHtml += '</div>';
        html += fieldHtml;
    });
    
    return html;
}

