/**
 * Main JavaScript file for the Crypto Trading Agent web interface
 */

// Initialize when the document is ready
$(document).ready(function() {
    // Initialize Socket.IO
    const socket = io();
    
    // Listen for agent updates
    socket.on('agent_update', function(data) {
        console.log('Received agent update:', data);
        
        // Update last update time
        if (data.timestamp) {
            updateLastUpdateTime(data.timestamp);
        }
        
        // Update agent status in the navbar
        if (data.agent_running !== undefined) {
            updateAgentStatus(data.agent_running);
        }
    });
    
    // Start agent button in navbar
    $('#start-agent-btn').click(function() {
        startAgent();
    });
    
    // Stop agent button in navbar
    $('#stop-agent-btn').click(function() {
        stopAgent();
    });
    
    // Check agent status on page load
    checkAgentStatus();
    
    // Set up tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();
});

/**
 * Check the current status of the trading agent
 */
function checkAgentStatus() {
    $.ajax({
        url: '/api/status',
        type: 'GET',
        success: function(response) {
            // Update agent status
            updateAgentStatus(response.agent_running);
            
            // Update last update time
            if (response.last_update) {
                updateLastUpdateTime(response.last_update);
            }
        },
        error: function() {
            console.error('Error checking agent status');
            updateAgentStatus(false);
        }
    });
}

/**
 * Update the agent status in the UI
 * @param {boolean} isRunning - Whether the agent is running
 */
function updateAgentStatus(isRunning) {
    if (isRunning) {
        // Update navbar status
        $('#agent-status').html('<i class="fas fa-circle text-success me-1"></i>Agent Running');
        
        // Show/hide buttons
        $('#start-agent-btn').hide();
        $('#stop-agent-btn').show();
        
        // Update dashboard status if on dashboard page
        if ($('#dashboard-agent-status').length) {
            $('#dashboard-agent-status').removeClass('bg-danger').addClass('bg-success').text('Running');
            $('#dashboard-start-btn').hide();
            $('#dashboard-stop-btn').show();
        }
    } else {
        // Update navbar status
        $('#agent-status').html('<i class="fas fa-circle text-danger me-1"></i>Agent Stopped');
        
        // Show/hide buttons
        $('#start-agent-btn').show();
        $('#stop-agent-btn').hide();
        
        // Update dashboard status if on dashboard page
        if ($('#dashboard-agent-status').length) {
            $('#dashboard-agent-status').removeClass('bg-success').addClass('bg-danger').text('Stopped');
            $('#dashboard-start-btn').show();
            $('#dashboard-stop-btn').hide();
        }
    }
}

/**
 * Update the last update time in the UI
 * @param {string} timestamp - ISO timestamp string
 */
function updateLastUpdateTime(timestamp) {
    const formattedTime = formatDateTime(timestamp);
    $('#last-update').text('Last update: ' + formattedTime);
    
    // Update dashboard last update if on dashboard page
    if ($('#dashboard-last-update').length) {
        $('#dashboard-last-update').text(formattedTime);
    }
}

/**
 * Start the trading agent
 * @param {number} interval - Interval in minutes between runs (default: 60)
 */
function startAgent(interval = 60) {
    $.ajax({
        url: '/api/start',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ interval: interval }),
        success: function(response) {
            if (response.status === 'success') {
                updateAgentStatus(true);
                showAlert('success', 'Agent started successfully');
            } else {
                showAlert('danger', 'Error starting agent: ' + response.message);
            }
        },
        error: function() {
            showAlert('danger', 'Error starting agent');
        }
    });
}

/**
 * Stop the trading agent
 */
function stopAgent() {
    $.ajax({
        url: '/api/stop',
        type: 'POST',
        contentType: 'application/json',
        success: function(response) {
            if (response.status === 'success') {
                updateAgentStatus(false);
                showAlert('success', 'Agent stopped successfully');
            } else {
                showAlert('danger', 'Error stopping agent: ' + response.message);
            }
        },
        error: function() {
            showAlert('danger', 'Error stopping agent');
        }
    });
}

/**
 * Format a datetime string
 * @param {string} isoString - ISO timestamp string
 * @returns {string} Formatted datetime string
 */
function formatDateTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString();
}

/**
 * Show an alert message
 * @param {string} type - Alert type (success, danger, warning, info)
 * @param {string} message - Alert message
 * @param {number} duration - Duration in milliseconds (default: 5000)
 */
function showAlert(type, message, duration = 5000) {
    // Create alert element
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    // Create container if it doesn't exist
    if ($('#alert-container').length === 0) {
        $('body').append('<div id="alert-container" style="position: fixed; top: 20px; right: 20px; z-index: 9999;"></div>');
    }
    
    // Add alert to container
    const alert = $(alertHtml).appendTo('#alert-container');
    
    // Auto-dismiss after duration
    setTimeout(function() {
        alert.alert('close');
    }, duration);
}

/**
 * Format a number as currency
 * @param {number} value - Number to format
 * @returns {string} Formatted currency string
 */
function formatCurrency(value) {
    return '$' + value.toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

/**
 * Format a number as percentage
 * @param {number} value - Number to format (0.1 = 10%)
 * @returns {string} Formatted percentage string
 */
function formatPercentage(value) {
    return (value * 100).toFixed(2) + '%';
}

/**
 * Get CSS class for technical signal
 * @param {string} signal - Technical signal (strong_buy, buy, neutral, sell, strong_sell)
 * @returns {string} CSS class
 */
function getTechnicalSignalClass(signal) {
    switch (signal) {
        case 'strong_buy':
        case 'buy':
            return 'bg-success';
        case 'strong_sell':
        case 'sell':
            return 'bg-danger';
        default:
            return 'bg-secondary';
    }
}

/**
 * Get CSS class for sentiment
 * @param {string} sentiment - Sentiment (positive, neutral, negative)
 * @returns {string} CSS class
 */
function getSentimentClass(sentiment) {
    switch (sentiment) {
        case 'positive':
            return 'bg-success';
        case 'negative':
            return 'bg-danger';
        default:
            return 'bg-secondary';
    }
}

/**
 * Format a signal string for display
 * @param {string} signal - Signal string (e.g., strong_buy, strong_sell)
 * @returns {string} Formatted signal string
 */
function formatSignal(signal) {
    return signal.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}
