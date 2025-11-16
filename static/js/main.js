// Main JavaScript for DCF Tool

let currentData = null;
let currentDCFResults = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    initializeTabs();
});

function initializeEventListeners() {
    // Company form submission
    document.getElementById('companyForm').addEventListener('submit', handleCompanyFetch);
    
    // DCF form submission
    document.getElementById('dcfForm').addEventListener('submit', handleDCFCalculation);
    
    // Export buttons
    document.getElementById('exportExcelBtn').addEventListener('click', handleExcelExport);
    document.getElementById('exportCsvBtn').addEventListener('click', handleCsvExport);
}

function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');
            
            // Remove active class from all buttons and panes
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));
            
            // Add active class to clicked button and corresponding pane
            button.classList.add('active');
            document.getElementById(targetTab + 'Tab').classList.add('active');
        });
    });
}

async function handleCompanyFetch(e) {
    e.preventDefault();
    const identifier = document.getElementById('companyIdentifier').value.trim();
    
    if (!identifier) {
        showError('Please enter a company ticker or CIK');
        return;
    }
    
    showLoading(true);
    hideError();
    
    try {
        const response = await fetch('/api/fetch-company', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ identifier: identifier })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentData = data;
            displayCompanyInfo(data);
            document.getElementById('calculateBtn').disabled = false;
        } else {
            showError(data.error || 'Failed to fetch company data');
        }
    } catch (error) {
        showError('Error fetching company data: ' + error.message);
    } finally {
        showLoading(false);
    }
}

function displayCompanyInfo(data) {
    document.getElementById('companyName').textContent = data.company_name || 'Unknown Company';
    document.getElementById('companyCIK').textContent = `CIK: ${data.cik || 'N/A'}`;
    document.getElementById('companyInfo').style.display = 'block';
}

async function handleDCFCalculation(e) {
    e.preventDefault();
    
    if (!currentData) {
        showError('Please fetch company data first');
        return;
    }
    
    const formData = new FormData(e.target);
    const assumptions = {
        projection_years: parseInt(formData.get('projection_years')),
        risk_free_rate: parseFloat(formData.get('risk_free_rate')) / 100,
        beta: parseFloat(formData.get('beta')),
        market_risk_premium: parseFloat(formData.get('market_risk_premium')) / 100,
        cost_of_debt: parseFloat(formData.get('cost_of_debt')) / 100,
        tax_rate: parseFloat(formData.get('tax_rate')) / 100,
        debt_to_equity: parseFloat(formData.get('debt_to_equity')),
        terminal_growth_rate: parseFloat(formData.get('terminal_growth_rate')) / 100,
        revenue_growth: formData.get('revenue_growth') && formData.get('revenue_growth').trim() !== '' ? parseFloat(formData.get('revenue_growth')) / 100 : null,
        gross_margin: formData.get('gross_margin') && formData.get('gross_margin').trim() !== '' ? parseFloat(formData.get('gross_margin')) / 100 : null,
        sga_percent: formData.get('sga_percent') && formData.get('sga_percent').trim() !== '' ? parseFloat(formData.get('sga_percent')) / 100 : null
    };
    
    showLoading(true);
    hideError();
    
    try {
        const response = await fetch('/api/calculate-dcf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                company_data: currentData,
                assumptions: assumptions
            })
        });
        
        // Check if response is ok
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
            showError(errorData.error || `HTTP Error: ${response.status}`);
            return;
        }
        
        // Parse JSON response
        let data;
        try {
            const text = await response.text();
            console.log('Response text (first 500 chars):', text.substring(0, 500));
            data = JSON.parse(text);
        } catch (parseError) {
            console.error('JSON Parse Error:', parseError);
            showError('Error parsing server response: ' + parseError.message);
            return;
        }
        
        // Validate response structure
        if (!data || !data.dcf_results || !data.operating_model) {
            console.error('Invalid response structure:', data);
            showError('Invalid response from server. Please try again.');
            return;
        }
        
        currentDCFResults = data;
        try {
            displayResults(data);
        } catch (displayError) {
            console.error('Error displaying results:', displayError);
            showError('Error displaying results: ' + displayError.message);
        }
    } catch (error) {
        console.error('DCF Calculation Error:', error);
        showError('Error calculating DCF: ' + error.message);
    } finally {
        showLoading(false);
    }
}

function displayResults(data) {
    try {
        // Display DCF Summary
        const dcfResults = data.dcf_results;
        if (!dcfResults) {
            throw new Error('DCF results not found in response');
        }
        
        document.getElementById('waccValue').textContent = formatPercent(dcfResults.wacc || 0);
        document.getElementById('enterpriseValue').textContent = formatCurrency(dcfResults.enterprise_value || 0);
        document.getElementById('equityValue').textContent = formatCurrency(dcfResults.equity_value || 0);
        document.getElementById('terminalValue').textContent = formatCurrency(dcfResults.terminal_value || 0);
        
        // Display Income Statement
        if (data.operating_model && data.operating_model.income_statement) {
            displayFinancialTable('incomeTable', data.operating_model.income_statement);
        } else {
            console.error('Income statement data not found');
        }
        
        // Display Balance Sheet
        if (data.operating_model && data.operating_model.balance_sheet) {
            displayFinancialTable('balanceTable', data.operating_model.balance_sheet);
        } else {
            console.error('Balance sheet data not found');
        }
        
        // Display Cash Flow
        if (data.operating_model && data.operating_model.cash_flow) {
            displayFinancialTable('cashflowTable', data.operating_model.cash_flow);
        } else {
            console.error('Cash flow data not found');
        }
        
        // Display DCF Details
        displayDCFDetails('dcfDetailsTable', dcfResults);
        
        // Show results section
        document.getElementById('resultsSection').style.display = 'block';
    } catch (error) {
        console.error('Error in displayResults:', error);
        throw error;
    }
}

function displayFinancialTable(tableId, data) {
    const table = document.getElementById(tableId);
    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody');
    
    // Clear existing content
    thead.innerHTML = '';
    tbody.innerHTML = '';
    
    if (!data || Object.keys(data).length === 0) {
        tbody.innerHTML = '<tr><td colspan="2">No data available</td></tr>';
        return;
    }
    
    // Get all years
    const years = Object.keys(data).sort();
    if (years.length === 0) return;
    
    // Get all line items from first year
    const firstYear = years[0];
    const lineItems = Object.keys(data[firstYear]);
    
    // Create header row
    const headerRow = document.createElement('tr');
    headerRow.appendChild(createHeaderCell('Line Item'));
    years.forEach(year => {
        headerRow.appendChild(createHeaderCell(year));
    });
    thead.appendChild(headerRow);
    
    // Create data rows
    lineItems.forEach(lineItem => {
        const row = document.createElement('tr');
        row.appendChild(createCell(formatLineItemName(lineItem)));
        years.forEach(year => {
            const value = data[year][lineItem] || 0;
            row.appendChild(createCell(formatNumber(value)));
        });
        tbody.appendChild(row);
    });
}

function displayDCFDetails(tableId, dcfResults) {
    const table = document.getElementById(tableId);
    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody');
    
    thead.innerHTML = '';
    tbody.innerHTML = '';
    
    // Header
    const headerRow = document.createElement('tr');
    headerRow.appendChild(createHeaderCell('Year'));
    headerRow.appendChild(createHeaderCell('Free Cash Flow (millions)'));
    thead.appendChild(headerRow);
    
    // FCF data
    const fcf = dcfResults.free_cash_flows || {};
    const years = Object.keys(fcf).sort();
    years.forEach(year => {
        const row = document.createElement('tr');
        row.appendChild(createCell(year));
        row.appendChild(createCell(formatCurrency(fcf[year])));
        tbody.appendChild(row);
    });
    
    // Add summary rows
    const summaryRow1 = document.createElement('tr');
    summaryRow1.classList.add('summary-row');
    summaryRow1.appendChild(createCell('PV of FCFs', true));
    summaryRow1.appendChild(createCell(formatCurrency(dcfResults.total_pv_fcf), true));
    tbody.appendChild(summaryRow1);
    
    const summaryRow2 = document.createElement('tr');
    summaryRow2.classList.add('summary-row');
    summaryRow2.appendChild(createCell('PV of Terminal Value', true));
    summaryRow2.appendChild(createCell(formatCurrency(dcfResults.present_value_terminal), true));
    tbody.appendChild(summaryRow2);
}

function createHeaderCell(text) {
    const cell = document.createElement('th');
    cell.textContent = text;
    return cell;
}

function createCell(text, bold = false) {
    const cell = document.createElement('td');
    cell.textContent = text;
    if (bold) {
        cell.style.fontWeight = 'bold';
    }
    return cell;
}

function formatLineItemName(name) {
    // Convert camelCase to readable format
    return name
        .replace(/([A-Z])/g, ' $1')
        .replace(/^./, str => str.toUpperCase())
        .trim();
}

function formatNumber(value) {
    if (value === null || value === undefined || isNaN(value)) {
        return '0.00';
    }
    return (value / 1_000_000).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function formatCurrency(value) {
    if (value === null || value === undefined || isNaN(value)) {
        return '$0.00';
    }
    return '$' + (value / 1_000_000).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }) + 'M';
}

function formatPercent(value) {
    if (value === null || value === undefined || isNaN(value)) {
        return '0.00%';
    }
    return (value * 100).toFixed(2) + '%';
}

async function handleExcelExport() {
    if (!currentDCFResults) {
        showError('Please calculate DCF first');
        return;
    }
    
    try {
        const response = await fetch('/api/export-excel', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                operating_model: currentDCFResults.operating_model,
                dcf_results: currentDCFResults.dcf_results,
                company_name: currentData.company_name || 'Company'
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${currentData.company_name || 'Company'}_DCF_Model.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            const data = await response.json();
            showError(data.error || 'Failed to export Excel file');
        }
    } catch (error) {
        showError('Error exporting Excel: ' + error.message);
    }
}

async function handleCsvExport() {
    if (!currentDCFResults) {
        showError('Please calculate DCF first');
        return;
    }
    
    try {
        const response = await fetch('/api/export-csv', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                operating_model: currentDCFResults.operating_model,
                dcf_results: currentDCFResults.dcf_results,
                company_name: currentData.company_name || 'Company'
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${currentData.company_name || 'Company'}_DCF_Model.zip`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            const data = await response.json();
            showError(data.error || 'Failed to export CSV files');
        }
    } catch (error) {
        showError('Error exporting CSV: ' + error.message);
    }
}

function showLoading(show) {
    document.getElementById('loadingIndicator').style.display = show ? 'block' : 'none';
}

function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

function hideError() {
    document.getElementById('errorMessage').style.display = 'none';
}

