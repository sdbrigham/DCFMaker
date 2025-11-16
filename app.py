from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import zipfile
import tempfile
from sec_client import SECClient
from operating_model import OperatingModel
from dcf_calculator import DCFCalculator
from export_handler import ExportHandler

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)  # Enable CORS for API calls

# Initialize SEC client
sec_client = SECClient()

@app.route('/')
def index():
    """Serve the main landing page"""
    return render_template('index.html')

@app.route('/api/fetch-company', methods=['POST'])
def fetch_company():
    """Fetch company data from SEC API"""
    try:
        data = request.get_json()
        identifier = data.get('identifier')
        
        if not identifier:
            return jsonify({'error': 'Company identifier (ticker or CIK) is required'}), 400
        
        identifier = identifier.strip()
        print(f"DEBUG: Fetching company data for identifier: {identifier}")
        
        # Fetch company data
        company_data = sec_client.fetch_company_data(identifier)
        
        if 'error' in company_data:
            print(f"DEBUG: Error fetching company data: {company_data['error']}")
            return jsonify(company_data), 400
        
        # Check if we got any financial data
        has_data = bool(company_data.get('income_statement') or 
                       company_data.get('balance_sheet') or 
                       company_data.get('cash_flow'))
        
        if not has_data:
            return jsonify({
                'error': 'No financial statement data found for this company. The company may not have filed XBRL data with the SEC, or the data format may be different.'
            }), 400
        
        print(f"DEBUG: Successfully fetched data for {company_data.get('company_name', 'Unknown')}")
        return jsonify(company_data), 200
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"DEBUG: Exception in fetch_company: {error_details}")
        return jsonify({'error': f'Error fetching company data: {str(e)}'}), 500

@app.route('/api/calculate-dcf', methods=['POST'])
def calculate_dcf():
    """Calculate DCF valuation based on inputs"""
    try:
        data = request.get_json()
        company_data = data.get('company_data')
        assumptions = data.get('assumptions')
        
        print(f"DEBUG: Received assumptions: {assumptions}")
        print(f"DEBUG: Company data keys: {company_data.keys() if company_data else 'None'}")
        
        if not company_data:
            return jsonify({'error': 'Company data is required'}), 400
        
        if not assumptions:
            return jsonify({'error': 'DCF assumptions are required'}), 400
        
        # Check if company data has financial statements
        has_income = bool(company_data.get('income_statement'))
        has_balance = bool(company_data.get('balance_sheet'))
        has_cashflow = bool(company_data.get('cash_flow'))
        
        print(f"DEBUG: Has income statement: {has_income}, Has balance sheet: {has_balance}, Has cash flow: {has_cashflow}")
        
        if not has_income and not has_balance:
            return jsonify({'error': 'Company data does not contain financial statements. Please fetch company data first.'}), 400
        
        # Build operating model
        projection_years = assumptions.get('projection_years', 5)
        operating_model = OperatingModel(company_data, projection_years=projection_years)
        
        # Prepare assumptions for operating model
        # Convert None to actual None (not string "None")
        revenue_growth = assumptions.get('revenue_growth')
        gross_margin = assumptions.get('gross_margin')
        sga_percent = assumptions.get('sga_percent')
        
        # Handle string "null" or "None"
        if revenue_growth == "null" or revenue_growth == "None":
            revenue_growth = None
        if gross_margin == "null" or gross_margin == "None":
            gross_margin = None
        if sga_percent == "null" or sga_percent == "None":
            sga_percent = None
        
        operating_assumptions = {
            'revenue_growth': revenue_growth,
            'gross_margin': gross_margin,
            'sga_percent': sga_percent,
            'tax_rate': assumptions.get('tax_rate', 0.25)
        }
        
        print(f"DEBUG: Operating assumptions: {operating_assumptions}")
        
        # Build model
        operating_model_data = operating_model.build_model(operating_assumptions)
        
        if 'error' in operating_model_data:
            return jsonify(operating_model_data), 400
        
        # Calculate DCF
        dcf_calculator = DCFCalculator(operating_model_data, assumptions)
        dcf_results = dcf_calculator.calculate_all()
        
        return jsonify({
            'operating_model': operating_model_data,
            'dcf_results': dcf_results
        }), 200
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"DCF Calculation Error: {error_details}")
        return jsonify({'error': f'Error calculating DCF: {str(e)}'}), 500

@app.route('/api/export-excel', methods=['POST'])
def export_excel():
    """Export results to Excel format"""
    try:
        data = request.get_json()
        operating_model_data = data.get('operating_model')
        dcf_results = data.get('dcf_results')
        company_name = data.get('company_name', 'Company')
        
        if not operating_model_data or not dcf_results:
            return jsonify({'error': 'Operating model and DCF results are required'}), 400
        
        # Create export handler
        export_handler = ExportHandler(operating_model_data, dcf_results, company_name)
        
        # Generate Excel file
        excel_file = export_handler.create_excel_workbook()
        
        # Send file
        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'{company_name}_DCF_Model.xlsx'
        )
        
    except Exception as e:
        return jsonify({'error': f'Error exporting Excel: {str(e)}'}), 500

@app.route('/api/export-csv', methods=['POST'])
def export_csv():
    """Export results to CSV format"""
    try:
        data = request.get_json()
        operating_model_data = data.get('operating_model')
        dcf_results = data.get('dcf_results')
        company_name = data.get('company_name', 'Company')
        
        if not operating_model_data or not dcf_results:
            return jsonify({'error': 'Operating model and DCF results are required'}), 400
        
        # Create export handler
        export_handler = ExportHandler(operating_model_data, dcf_results, company_name)
        
        # Create temporary directory for CSV files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Export CSV files
            csv_files = export_handler.export_to_csv(temp_dir)
            
            # Create ZIP file
            zip_path = os.path.join(temp_dir, f'{company_name}_DCF_Model.zip')
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file_type, file_path in csv_files.items():
                    if os.path.exists(file_path):
                        zipf.write(file_path, os.path.basename(file_path))
            
            # Send ZIP file
            return send_file(
                zip_path,
                mimetype='application/zip',
                as_attachment=True,
                download_name=f'{company_name}_DCF_Model.zip'
            )
        
    except Exception as e:
        return jsonify({'error': f'Error exporting CSV: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
