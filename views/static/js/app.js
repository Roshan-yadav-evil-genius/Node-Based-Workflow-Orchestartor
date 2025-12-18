/**
 * Node Engine POC - Main Application
 * Global state, initialization, and utility functions
 */

// ==========================================================================
// Global State
// ==========================================================================

var currentNodeIdentifier = null;
var currentNodeFormFields = [];
var currentFormDependencies = {};

// Default input JSON template
var defaultInputJson = {
    "url": "https://www.freelancer.in/projects/git/web-development-intern-with-react.html",
    "title": "Web Development Intern with React Skills",
    "budget": "Budget ₹1,500 – 12,500 INR",
    "parsed_budget": {
        "min": "1500",
        "max": "12500",
        "currency_symbol": "₹",
        "currency": "INR",
        "per_hour": false
    },
    "description": "I'm seeking an intern for a web development position who is eager to learn and contribute to our projects.",
    "skills": ["Documentation", "Frontend Development", "Git", "HTML", "HTML5"],
    "ClientRating": 5,
    "ClientReviews": 27,
    "timestamp": new Date().toISOString()
};

// ==========================================================================
// Initialization
// ==========================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltips = [].slice.call(document.querySelectorAll('[title]'));
    tooltips.forEach(function(el) {
        new bootstrap.Tooltip(el);
    });
    
    // Set up event listeners
    setupGlobalEventListeners();
});

function setupGlobalEventListeners() {
    // Close execution popup on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            var overlay = document.getElementById('executionOverlay');
            if (overlay && overlay.classList.contains('show')) {
                closeExecutionPopup();
            }
        }
    });
    
    // Close popup on clicking overlay background
    var executionOverlay = document.getElementById('executionOverlay');
    if (executionOverlay) {
        executionOverlay.addEventListener('click', function(e) {
            if (e.target === this) {
                closeExecutionPopup();
            }
        });
    }
}

// ==========================================================================
// Utility Functions
// ==========================================================================

/**
 * Escape HTML special characters to prevent XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Syntax highlight JSON for display
 */
function syntaxHighlight(json) {
    json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
        var cls = 'color: #b5cea8;'; // number
        if (/^"/.test(match)) {
            if (/:$/.test(match)) {
                cls = 'color: #9cdcfe;'; // key
                match = match.replace(/"/g, '');
                match = '"' + match;
            } else {
                cls = 'color: #ce9178;'; // string
            }
        } else if (/true|false/.test(match)) {
            cls = 'color: #569cd6;'; // boolean
        } else if (/null/.test(match)) {
            cls = 'color: #569cd6;'; // null
        }
        return '<span style="' + cls + '">' + match + '</span>';
    });
}

/**
 * Select node from modal and show details
 */
function selectNode(id, name) {
    showNodeDetails(id);
    var modal = bootstrap.Modal.getInstance(document.getElementById('nodeModal'));
    if (modal) {
        modal.hide();
    }
}

