# DCF Valuation Tool

A comprehensive Discounted Cash Flow (DCF) valuation tool that fetches financial data from SEC XBRL API and builds operating models with DCF calculations.

## Features

- **SEC XBRL Integration**: Automatically fetches 10-K financial data from SEC EDGAR database
- **Operating Model Builder**: Projects Income Statement, Balance Sheet, and Cash Flow Statement forward
- **DCF Calculations**: Calculates WACC, Free Cash Flow, Terminal Value, and Enterprise/Equity Valuation
- **Interactive Web Interface**: Clean, modern UI for inputting assumptions and viewing results
- **Export Functionality**: Download results in Excel (multi-sheet) or CSV format

## Setup

1. **Activate Virtual Environment**
   ```bash
   source .venv/bin/activate
   ```

2. **Install Dependencies** (if not already installed)
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**
   ```bash
   python app.py
   ```

4. **Access the Tool**
   Open your browser and navigate to: `http://localhost:5001`

## Usage

### Step 1: Fetch Company Data
1. Enter a company ticker symbol (e.g., "AAPL") or CIK number (e.g., "0000320193")
2. Click "Fetch Company Data"
3. The tool will retrieve historical financial statements from SEC filings

### Step 2: Enter DCF Assumptions
Fill in the following assumptions:
- **Projection Period**: Number of years to project (default: 5)
- **Risk-Free Rate**: Typically 10-year Treasury yield (default: 3%)
- **Beta**: Stock's beta coefficient (default: 1.0)
- **Market Risk Premium**: Expected market return minus risk-free rate (default: 6%)
- **Cost of Debt**: Company's cost of debt (default: 5%)
- **Tax Rate**: Corporate tax rate (default: 25%)
- **Debt-to-Equity Ratio**: Company's debt-to-equity ratio (default: 0.3)
- **Terminal Growth Rate**: Long-term growth rate (default: 3%)
- **Revenue Growth**: Annual revenue growth (optional - uses historical average if blank)
- **Gross Margin**: Target gross margin (optional - uses historical average if blank)
- **SG&A %**: SG&A as percentage of revenue (optional - uses historical average if blank)

### Step 3: Calculate DCF
Click "Calculate DCF" to generate:
- Operating model projections
- WACC calculation
- Free Cash Flow projections
- Terminal value
- Enterprise value and equity value

### Step 4: View Results
Review the results in the interactive tables:
- Income Statement (historical + projections)
- Balance Sheet (historical + projections)
- Cash Flow Statement (historical + projections)
- DCF Details (FCF breakdown and valuation summary)

### Step 5: Export
Download results in:
- **Excel Format**: Multi-sheet workbook with all statements and DCF summary
- **CSV Format**: ZIP file containing separate CSV files for each statement

## Project Structure

```
/
├── app.py                 # Flask application with API routes
├── sec_client.py          # SEC XBRL API client
├── operating_model.py     # Operating model builder
├── dcf_calculator.py      # DCF calculations (WACC, FCF, valuation)
├── export_handler.py     # Excel/CSV export functionality
├── requirements.txt       # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css     # Styling
│   └── js/
│       └── main.js       # Frontend JavaScript
├── templates/
│   └── index.html        # Main HTML template
└── README.md            # This file
```

## API Endpoints

- `GET /` - Serve main landing page
- `POST /api/fetch-company` - Fetch company data from SEC API
- `POST /api/calculate-dcf` - Calculate DCF valuation
- `POST /api/export-excel` - Export results to Excel
- `POST /api/export-csv` - Export results to CSV

## Notes

- The SEC API has rate limiting. The tool includes delays to comply with SEC guidelines.
- Some companies may have incomplete data in SEC filings. The tool handles missing values gracefully.
- DCF assumptions significantly impact valuation results. Adjust carefully based on your analysis.
- Historical averages are used for projections when specific assumptions are not provided.

## License

This tool is for educational and analytical purposes.

