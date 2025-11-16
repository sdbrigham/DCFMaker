"""
Export Handler
Handles Excel and CSV export of financial statements and DCF results
"""
import pandas as pd
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from io import BytesIO
import os
import re
from typing import Dict, Optional

class ExportHandler:
    """Handle exports to Excel and CSV formats"""
    
    def __init__(self, operating_model_data: Dict, dcf_results: Dict, company_name: str = "Company"):
        """
        Initialize export handler
        
        Args:
            operating_model_data: Dict with financial statements
            dcf_results: Dict with DCF calculation results
            company_name: Name of the company
        """
        self.operating_model_data = operating_model_data
        self.dcf_results = dcf_results
        # Sanitize company name for filenames
        self.company_name = re.sub(r'[<>:"/\\|?*]', '_', company_name)
    
    def format_number(self, value, format_type='millions'):
        """Format number for display"""
        if pd.isna(value) or value == 0:
            return 0.0
        
        if format_type == 'millions':
            return value / 1_000_000
        elif format_type == 'thousands':
            return value / 1_000
        else:
            return value
    
    def create_excel_workbook(self) -> BytesIO:
        """
        Create Excel workbook with multiple sheets:
        - Income Statement
        - Balance Sheet
        - Cash Flow Statement
        - DCF Summary
        """
        wb = Workbook()
        
        # Remove default sheet
        if 'Sheet' in wb.sheetnames:
            wb.remove(wb['Sheet'])
        
        # Create sheets
        self._create_income_statement_sheet(wb)
        self._create_balance_sheet_sheet(wb)
        self._create_cash_flow_sheet(wb)
        self._create_dcf_summary_sheet(wb)
        
        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output
    
    def _create_income_statement_sheet(self, wb: Workbook):
        """Create Income Statement sheet"""
        ws = wb.create_sheet("Income Statement")
        
        income_data = pd.DataFrame(self.operating_model_data.get('income_statement', {}))
        if income_data.empty:
            ws['A1'] = "No data available"
            return
        
        # Headers
        headers = ['Line Item'] + list(income_data.index)
        ws.append(headers)
        
        # Style header row
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        for col in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Income Statement line items (in order)
        line_items = [
            ('Revenue', 'Revenue'),
            ('COGS', 'COGS'),
            ('Gross Profit', 'GrossProfit'),
            ('SG&A', 'SG&A'),
            ('Other Operating Expenses', 'OtherOperatingExpenses'),
            ('EBITDA', 'EBITDA'),
            ('D&A', 'D&A'),
            ('Operating Income', 'OperatingIncome'),
            ('Interest Expense', 'InterestExpense'),
            ('Other Unusual Items', 'OtherUnusualItems'),
            ('EBT', 'EBT'),
            ('Tax Expense', 'TaxExpense'),
            ('Net Income', 'NetIncome')
        ]
        
        row = 2
        for label, key in line_items:
            if key in income_data.columns:
                ws.cell(row=row, column=1, value=label)
                col = 2
                for year in income_data.index:
                    value = self.format_number(income_data.loc[year, key])
                    ws.cell(row=row, column=col, value=value)
                    col += 1
                row += 1
        
        # Format columns
        for col in range(2, len(headers) + 1):
            for row in range(2, ws.max_row + 1):
                cell = ws.cell(row=row, column=col)
                if cell.value is not None:
                    cell.number_format = '#,##0.00'
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 25
        for col in range(2, len(headers) + 1):
            ws.column_dimensions[get_column_letter(col)].width = 15
    
    def _create_balance_sheet_sheet(self, wb: Workbook):
        """Create Balance Sheet sheet"""
        ws = wb.create_sheet("Balance Sheet")
        
        balance_data = pd.DataFrame(self.operating_model_data.get('balance_sheet', {}))
        if balance_data.empty:
            ws['A1'] = "No data available"
            return
        
        # Headers
        headers = ['Line Item'] + list(balance_data.index)
        ws.append(headers)
        
        # Style header row
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        for col in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Balance Sheet line items
        line_items = [
            ('Cash', 'Cash'),
            ('Short Term Investments', 'ShortTermInvestments'),
            ('Current Assets', 'CurrentAssets'),
            ('PPE', 'PPE'),
            ('Other Long Term Assets', 'OtherLongTermAssets'),
            ('Total Assets', 'TotalAssets'),
            ('Short Term Liabilities', 'ShortTermLiabilities'),
            ('Long Term Debt', 'LongTermDebt'),
            ('Long Term Leases', 'LongTermLeases'),
            ('Other Long Term Liabilities', 'OtherLongTermLiabilities'),
            ('Total Liabilities', 'TotalLiabilities'),
            ('Retained Earnings', 'RetainedEarnings'),
            ('Common Stock', 'CommonStock'),
            ('Paid-in Capital', 'PaidInCapital'),
            ('Total Equity', 'TotalEquity')
        ]
        
        row = 2
        for label, key in line_items:
            if key in balance_data.columns:
                ws.cell(row=row, column=1, value=label)
                col = 2
                for year in balance_data.index:
                    value = self.format_number(balance_data.loc[year, key])
                    ws.cell(row=row, column=col, value=value)
                    col += 1
                row += 1
        
        # Format columns
        for col in range(2, len(headers) + 1):
            for row in range(2, ws.max_row + 1):
                cell = ws.cell(row=row, column=col)
                if cell.value is not None:
                    cell.number_format = '#,##0.00'
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 25
        for col in range(2, len(headers) + 1):
            ws.column_dimensions[get_column_letter(col)].width = 15
    
    def _create_cash_flow_sheet(self, wb: Workbook):
        """Create Cash Flow Statement sheet"""
        ws = wb.create_sheet("Cash Flow Statement")
        
        cashflow_data = pd.DataFrame(self.operating_model_data.get('cash_flow', {}))
        if cashflow_data.empty:
            ws['A1'] = "No data available"
            return
        
        # Headers
        headers = ['Line Item'] + list(cashflow_data.index)
        ws.append(headers)
        
        # Style header row
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        for col in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Cash Flow line items
        line_items = [
            ('Net Income', 'NetIncome'),
            ('D&A', 'D&A'),
            ('Change in Working Capital', 'ChangeInWorkingCapital'),
            ('Operating Cash Flow', 'OperatingCashFlow'),
            ('Capital Expenditures', 'CapitalExpenditures'),
            ('Investing Cash Flow', 'InvestingCashFlow'),
            ('Financing Cash Flow', 'FinancingCashFlow'),
            ('Net Cash Flow', 'NetCashFlow')
        ]
        
        row = 2
        for label, key in line_items:
            if key in cashflow_data.columns:
                ws.cell(row=row, column=1, value=label)
                col = 2
                for year in cashflow_data.index:
                    value = self.format_number(cashflow_data.loc[year, key])
                    ws.cell(row=row, column=col, value=value)
                    col += 1
                row += 1
        
        # Format columns
        for col in range(2, len(headers) + 1):
            for row in range(2, ws.max_row + 1):
                cell = ws.cell(row=row, column=col)
                if cell.value is not None:
                    cell.number_format = '#,##0.00'
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 25
        for col in range(2, len(headers) + 1):
            ws.column_dimensions[get_column_letter(col)].width = 15
    
    def _create_dcf_summary_sheet(self, wb: Workbook):
        """Create DCF Summary sheet"""
        ws = wb.create_sheet("DCF Summary")
        
        # Title
        ws['A1'] = "DCF Valuation Summary"
        ws['A1'].font = Font(bold=True, size=14)
        ws.merge_cells('A1:B1')
        
        row = 3
        
        # Assumptions
        ws.cell(row=row, column=1, value="Assumptions").font = Font(bold=True, size=12)
        row += 1
        
        assumptions = self.dcf_results.get('assumptions', {})
        assumption_labels = {
            'risk_free_rate': 'Risk-Free Rate',
            'beta': 'Beta',
            'market_risk_premium': 'Market Risk Premium',
            'cost_of_debt': 'Cost of Debt',
            'tax_rate': 'Tax Rate',
            'debt_to_equity': 'Debt-to-Equity Ratio',
            'terminal_growth_rate': 'Terminal Growth Rate'
        }
        
        for key, label in assumption_labels.items():
            value = assumptions.get(key, 'N/A')
            ws.cell(row=row, column=1, value=label)
            if isinstance(value, (int, float)):
                ws.cell(row=row, column=2, value=value).number_format = '0.00%' if key != 'beta' else '0.00'
            else:
                ws.cell(row=row, column=2, value=value)
            row += 1
        
        row += 1
        
        # WACC
        ws.cell(row=row, column=1, value="WACC").font = Font(bold=True)
        wacc = self.dcf_results.get('wacc', 0)
        ws.cell(row=row, column=2, value=wacc).number_format = '0.00%'
        row += 2
        
        # Free Cash Flows
        ws.cell(row=row, column=1, value="Free Cash Flows (in millions)").font = Font(bold=True, size=12)
        row += 1
        ws.cell(row=row, column=1, value="Year")
        ws.cell(row=row, column=2, value="FCF")
        row += 1
        
        fcf = self.dcf_results.get('free_cash_flows', {})
        for year, value in sorted(fcf.items()):
            ws.cell(row=row, column=1, value=str(year))
            ws.cell(row=row, column=2, value=self.format_number(value)).number_format = '#,##0.00'
            row += 1
        
        row += 1
        
        # Terminal Value
        ws.cell(row=row, column=1, value="Terminal Value (in millions)").font = Font(bold=True)
        terminal_value = self.dcf_results.get('terminal_value', 0)
        ws.cell(row=row, column=2, value=self.format_number(terminal_value)).number_format = '#,##0.00'
        row += 2
        
        # Valuation Summary
        ws.cell(row=row, column=1, value="Valuation Summary (in millions)").font = Font(bold=True, size=12)
        row += 1
        
        pv_fcf = self.dcf_results.get('total_pv_fcf', 0)
        pv_terminal = self.dcf_results.get('present_value_terminal', 0)
        enterprise_value = self.dcf_results.get('enterprise_value', 0)
        equity_value = self.dcf_results.get('equity_value', 0)
        
        ws.cell(row=row, column=1, value="PV of FCFs")
        ws.cell(row=row, column=2, value=self.format_number(pv_fcf)).number_format = '#,##0.00'
        row += 1
        
        ws.cell(row=row, column=1, value="PV of Terminal Value")
        ws.cell(row=row, column=2, value=self.format_number(pv_terminal)).number_format = '#,##0.00'
        row += 1
        
        ws.cell(row=row, column=1, value="Enterprise Value").font = Font(bold=True)
        ws.cell(row=row, column=2, value=self.format_number(enterprise_value)).number_format = '#,##0.00'
        row += 1
        
        ws.cell(row=row, column=1, value="Equity Value").font = Font(bold=True)
        ws.cell(row=row, column=2, value=self.format_number(equity_value)).number_format = '#,##0.00'
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 20
    
    def export_to_csv(self, output_dir: str = ".") -> Dict[str, str]:
        """
        Export financial statements to separate CSV files
        
        Returns:
            Dict with file paths
        """
        files = {}
        
        # Income Statement
        income_data = pd.DataFrame(self.operating_model_data.get('income_statement', {}))
        if not income_data.empty:
            income_data_formatted = income_data / 1_000_000  # Convert to millions
            filepath = os.path.join(output_dir, f"{self.company_name}_Income_Statement.csv")
            income_data_formatted.to_csv(filepath)
            files['income_statement'] = filepath
        
        # Balance Sheet
        balance_data = pd.DataFrame(self.operating_model_data.get('balance_sheet', {}))
        if not balance_data.empty:
            balance_data_formatted = balance_data / 1_000_000  # Convert to millions
            filepath = os.path.join(output_dir, f"{self.company_name}_Balance_Sheet.csv")
            balance_data_formatted.to_csv(filepath)
            files['balance_sheet'] = filepath
        
        # Cash Flow
        cashflow_data = pd.DataFrame(self.operating_model_data.get('cash_flow', {}))
        if not cashflow_data.empty:
            cashflow_data_formatted = cashflow_data / 1_000_000  # Convert to millions
            filepath = os.path.join(output_dir, f"{self.company_name}_Cash_Flow.csv")
            cashflow_data_formatted.to_csv(filepath)
            files['cash_flow'] = filepath
        
        # DCF Summary
        dcf_summary = pd.DataFrame({
            'Metric': ['WACC', 'Terminal Value', 'PV of FCFs', 'PV of Terminal Value', 
                      'Enterprise Value', 'Equity Value'],
            'Value (millions)': [
                self.dcf_results.get('wacc', 0) * 100,  # Convert to percentage
                self.format_number(self.dcf_results.get('terminal_value', 0)),
                self.format_number(self.dcf_results.get('total_pv_fcf', 0)),
                self.format_number(self.dcf_results.get('present_value_terminal', 0)),
                self.format_number(self.dcf_results.get('enterprise_value', 0)),
                self.format_number(self.dcf_results.get('equity_value', 0))
            ]
        })
        filepath = os.path.join(output_dir, f"{self.company_name}_DCF_Summary.csv")
        dcf_summary.to_csv(filepath, index=False)
        files['dcf_summary'] = filepath
        
        return files

