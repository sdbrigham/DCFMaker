"""
Operating Model Builder
Projects financial statements forward based on historical data and assumptions
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional

class OperatingModel:
    """Builds operating model projections from historical financial data"""
    
    def __init__(self, historical_data: Dict, projection_years: int = 5):
        """
        Initialize with historical financial data
        
        Args:
            historical_data: Dict with 'income_statement', 'balance_sheet', 'cash_flow'
            projection_years: Number of years to project forward
        """
        self.historical_data = historical_data
        self.projection_years = projection_years
        self.income_statement = None
        self.balance_sheet = None
        self.cash_flow = None
        
    def prepare_historical_data(self) -> bool:
        """Convert historical data dictionaries to DataFrames"""
        try:
            # Income Statement
            if self.historical_data.get('income_statement'):
                income_dict = self.historical_data['income_statement']
                print(f"DEBUG: Income statement data type: {type(income_dict)}, keys: {list(income_dict.keys())[:5] if income_dict else 'empty'}")
                
                if not income_dict:
                    print("DEBUG: Income statement is empty")
                    return False
                
                self.income_statement = pd.DataFrame(income_dict).T
                print(f"DEBUG: Income statement shape: {self.income_statement.shape}, columns: {list(self.income_statement.columns)}")
                
                # Convert to numeric, handling any non-numeric values
                for col in self.income_statement.columns:
                    try:
                        self.income_statement[col] = pd.to_numeric(
                            self.income_statement[col], errors='coerce'
                        ).fillna(0)
                    except Exception as e:
                        print(f"DEBUG: Error converting column {col}: {e}")
                        self.income_statement[col] = 0
            
            # Balance Sheet
            if self.historical_data.get('balance_sheet'):
                balance_dict = self.historical_data['balance_sheet']
                if not balance_dict:
                    print("DEBUG: Balance sheet is empty")
                else:
                    self.balance_sheet = pd.DataFrame(balance_dict).T
                    for col in self.balance_sheet.columns:
                        try:
                            self.balance_sheet[col] = pd.to_numeric(
                                self.balance_sheet[col], errors='coerce'
                            ).fillna(0)
                        except Exception as e:
                            print(f"DEBUG: Error converting balance sheet column {col}: {e}")
                            self.balance_sheet[col] = 0
            
            # Cash Flow
            if self.historical_data.get('cash_flow'):
                cashflow_dict = self.historical_data['cash_flow']
                if not cashflow_dict:
                    print("DEBUG: Cash flow is empty")
                else:
                    self.cash_flow = pd.DataFrame(cashflow_dict).T
                    for col in self.cash_flow.columns:
                        try:
                            self.cash_flow[col] = pd.to_numeric(
                                self.cash_flow[col], errors='coerce'
                            ).fillna(0)
                        except Exception as e:
                            print(f"DEBUG: Error converting cash flow column {col}: {e}")
                            self.cash_flow[col] = 0
            
            return True
        except Exception as e:
            print(f"Error preparing historical data: {e}")
            return False
    
    def get_latest_year(self) -> str:
        """Get the most recent year from historical data"""
        if self.income_statement is not None and not self.income_statement.empty:
            years = []
            for y in self.income_statement.index:
                y_str = str(y)
                # Extract year from string (handles both "2023" and "2023-12-31" formats)
                if y_str.isdigit():
                    years.append(int(y_str))
                elif '-' in y_str:
                    # Extract year from date string
                    year_part = y_str.split('-')[0]
                    if year_part.isdigit():
                        years.append(int(year_part))
            if years:
                return str(max(years))
        return None
    
    def calculate_average_growth_rate(self, series: pd.Series) -> float:
        """Calculate average growth rate from historical series"""
        if len(series) < 2:
            return 0.0
        
        values = series.dropna().values
        if len(values) < 2:
            return 0.0
        
        growth_rates = []
        for i in range(1, len(values)):
            if values[i-1] != 0:
                growth_rate = (values[i] - values[i-1]) / abs(values[i-1])
                growth_rates.append(growth_rate)
        
        return np.mean(growth_rates) if growth_rates else 0.0
    
    def project_income_statement(self, revenue_growth: float = None, 
                                 gross_margin: float = None,
                                 sga_percent: float = None,
                                 tax_rate: float = 0.25) -> pd.DataFrame:
        """
        Project Income Statement forward
        
        Args:
            revenue_growth: Annual revenue growth rate (if None, uses historical average)
            gross_margin: Target gross margin (if None, uses historical average)
            sga_percent: SG&A as % of revenue (if None, uses historical average)
            tax_rate: Tax rate for projections
        """
        if self.income_statement is None or self.income_statement.empty:
            return pd.DataFrame()
        
        latest_year_str = self.get_latest_year()
        if latest_year_str is None:
            return pd.DataFrame()
        latest_year = int(latest_year_str)
        projection_data = []
        
        # Get historical averages
        if revenue_growth is None:
            revenue_series = self.income_statement.get('Revenue', pd.Series())
            revenue_growth = self.calculate_average_growth_rate(revenue_series)
        
        if gross_margin is None:
            revenue = self.income_statement.get('Revenue', pd.Series())
            cogs = self.income_statement.get('COGS', pd.Series())
            if not revenue.empty and not cogs.empty:
                gross_profits = revenue + cogs  # COGS is negative
                gross_margins = gross_profits / revenue
                gross_margin = gross_margins.mean()
            else:
                gross_margin = 0.5
        
        if sga_percent is None:
            revenue = self.income_statement.get('Revenue', pd.Series())
            sga = self.income_statement.get('SG&A', pd.Series())
            if not revenue.empty and not sga.empty:
                sga_percents = abs(sga) / revenue
                sga_percent = sga_percents.mean()
            else:
                sga_percent = 0.4
        
        # Get latest values
        latest_row = self.income_statement.loc[str(latest_year)]
        latest_revenue = latest_row.get('Revenue', 0)
        latest_da = latest_row.get('D&A', 0)
        
        # Project forward
        for year_offset in range(1, self.projection_years + 1):
            year = latest_year + year_offset
            
            # Revenue
            revenue = latest_revenue * ((1 + revenue_growth) ** year_offset)
            
            # COGS (negative)
            cogs = -revenue * (1 - gross_margin)
            
            # Gross Profit
            gross_profit = revenue + cogs
            
            # SG&A (negative)
            sga = -revenue * sga_percent
            
            # Other Operating Expenses (assume 0 for projections)
            other_opex = 0
            
            # EBITDA
            ebitda = gross_profit + sga + other_opex
            
            # D&A (assume constant as % of prior year PPE or use historical)
            da = abs(latest_da) * (1 + revenue_growth * 0.5)  # D&A grows slower than revenue
            
            # Operating Income
            operating_income = ebitda - da
            
            # Interest Expense (assume constant or small)
            interest_expense = latest_row.get('InterestExpense', 0) or -10.0
            
            # Other Unusual Items (assume 0)
            other_unusual = 0
            
            # EBT
            ebt = operating_income + interest_expense + other_unusual
            
            # Tax Expense
            tax_expense = -ebt * tax_rate
            
            # Net Income
            net_income = ebt + tax_expense
            
            projection_data.append({
                'Revenue': revenue,
                'COGS': cogs,
                'GrossProfit': gross_profit,
                'SG&A': sga,
                'OtherOperatingExpenses': other_opex,
                'EBITDA': ebitda,
                'D&A': -da,
                'OperatingIncome': operating_income,
                'InterestExpense': interest_expense,
                'OtherUnusualItems': other_unusual,
                'EBT': ebt,
                'TaxExpense': tax_expense,
                'NetIncome': net_income
            })
        
        return pd.DataFrame(projection_data, index=[str(latest_year + i) for i in range(1, self.projection_years + 1)])
    
    def project_balance_sheet(self, projected_income: pd.DataFrame,
                             working_capital_ratios: Dict = None) -> pd.DataFrame:
        """
        Project Balance Sheet forward
        
        Args:
            projected_income: Projected Income Statement
            working_capital_ratios: Dict with ratios for AR, Inventory, AP as % of revenue
        """
        if self.balance_sheet is None or self.balance_sheet.empty:
            return pd.DataFrame()
        
        latest_year_str = self.get_latest_year()
        if latest_year_str is None:
            return pd.DataFrame()
        latest_year = int(latest_year_str)
        
        # Default working capital ratios
        if working_capital_ratios is None:
            # Calculate from historical data
            revenue = self.income_statement.get('Revenue', pd.Series())
            if not revenue.empty:
                latest_revenue = revenue.loc[str(latest_year)]
                # Assume typical ratios if not available
                working_capital_ratios = {
                    'ar_days': 30,
                    'inventory_days': 60,
                    'ap_days': 45
                }
        
        projection_data = []
        latest_row = self.balance_sheet.loc[str(latest_year)]
        
        for year_offset in range(1, self.projection_years + 1):
            year = latest_year + year_offset
            year_str = str(year)
            
            # Get projected revenue
            projected_revenue = projected_income.loc[year_str, 'Revenue']
            
            # Cash (will be calculated from cash flow)
            cash = latest_row.get('Cash', 0)
            
            # Short Term Investments (assume constant or grow with revenue)
            st_investments = latest_row.get('ShortTermInvestments', 0)
            
            # Current Assets (simplified - assume grows with revenue)
            current_assets = latest_row.get('CurrentAssets', 0) * (projected_revenue / self.income_statement.loc[str(latest_year), 'Revenue'])
            
            # PPE (grows with capex, depreciates)
            ppe = latest_row.get('PPE', 0)
            # Assume capex is ~3-5% of revenue
            capex = projected_revenue * 0.04
            da = abs(projected_income.loc[year_str, 'D&A'])
            ppe = ppe + capex - da
            
            # Other Long Term Assets (grows with revenue)
            other_lt_assets = latest_row.get('OtherLongTermAssets', 0) * (1 + 0.02)  # 2% growth
            
            # Total Assets
            total_assets = current_assets + ppe + other_lt_assets
            
            # Short Term Liabilities (grows with revenue)
            st_liabilities = latest_row.get('ShortTermLiabilities', 0) * (projected_revenue / self.income_statement.loc[str(latest_year), 'Revenue'])
            
            # Long Term Debt (assume constant for now)
            lt_debt = latest_row.get('LongTermDebt', 0)
            
            # Long Term Leases (assume constant)
            lt_leases = latest_row.get('LongTermLeases', 0)
            
            # Other Long Term Liabilities (assume constant)
            other_lt_liabilities = latest_row.get('OtherLongTermLiabilities', 0)
            
            # Total Liabilities
            total_liabilities = st_liabilities + lt_debt + lt_leases + other_lt_liabilities
            
            # Equity components
            retained_earnings = latest_row.get('RetainedEarnings', 0)
            net_income = projected_income.loc[year_str, 'NetIncome']
            retained_earnings = retained_earnings + net_income
            
            common_stock = latest_row.get('CommonStock', 0)
            paid_in_capital = latest_row.get('PaidInCapital', 0)
            
            # Total Equity
            total_equity = retained_earnings + common_stock + paid_in_capital
            
            projection_data.append({
                'Cash': cash,
                'ShortTermInvestments': st_investments,
                'CurrentAssets': current_assets,
                'PPE': ppe,
                'OtherLongTermAssets': other_lt_assets,
                'TotalAssets': total_assets,
                'ShortTermLiabilities': st_liabilities,
                'LongTermDebt': lt_debt,
                'LongTermLeases': lt_leases,
                'OtherLongTermLiabilities': other_lt_liabilities,
                'TotalLiabilities': total_liabilities,
                'RetainedEarnings': retained_earnings,
                'CommonStock': common_stock,
                'PaidInCapital': paid_in_capital,
                'TotalEquity': total_equity
            })
        
        return pd.DataFrame(projection_data, index=[str(latest_year + i) for i in range(1, self.projection_years + 1)])
    
    def project_cash_flow(self, projected_income: pd.DataFrame,
                         projected_balance: pd.DataFrame) -> pd.DataFrame:
        """
        Project Cash Flow Statement from Income Statement and Balance Sheet changes
        """
        if self.cash_flow is None or self.cash_flow.empty:
            return pd.DataFrame()
        
        latest_year_str = self.get_latest_year()
        if latest_year_str is None:
            return pd.DataFrame()
        latest_year = int(latest_year_str)
        projection_data = []
        
        for year_offset in range(1, self.projection_years + 1):
            year = latest_year + year_offset
            year_str = str(year)
            prev_year_str = str(year - 1)
            
            # Net Income
            net_income = projected_income.loc[year_str, 'NetIncome']
            
            # D&A (add back)
            da = abs(projected_income.loc[year_str, 'D&A'])
            
            # Changes in Working Capital
            if year_offset == 1:
                prev_current_assets = self.balance_sheet.loc[str(latest_year), 'CurrentAssets']
                prev_st_liabilities = self.balance_sheet.loc[str(latest_year), 'ShortTermLiabilities']
            else:
                prev_current_assets = projected_balance.loc[prev_year_str, 'CurrentAssets']
                prev_st_liabilities = projected_balance.loc[prev_year_str, 'ShortTermLiabilities']
            
            curr_current_assets = projected_balance.loc[year_str, 'CurrentAssets']
            curr_st_liabilities = projected_balance.loc[year_str, 'ShortTermLiabilities']
            
            change_ca = prev_current_assets - curr_current_assets
            change_cl = curr_st_liabilities - prev_st_liabilities
            change_wc = change_ca + change_cl
            
            # Operating Cash Flow
            cfo = net_income + da + change_wc
            
            # Capital Expenditures (negative)
            revenue = projected_income.loc[year_str, 'Revenue']
            capex = -revenue * 0.04  # Assume 4% of revenue
            
            # Investing Cash Flow
            investing_cf = capex
            
            # Financing Cash Flow (simplified - assume no new debt/equity)
            financing_cf = 0
            
            # Net Cash Flow
            net_cf = cfo + investing_cf + financing_cf
            
            projection_data.append({
                'NetIncome': net_income,
                'D&A': da,
                'ChangeInWorkingCapital': change_wc,
                'ChangeInCurrentAssets': change_ca,
                'ChangeInCurrentLiabilities': change_cl,
                'OperatingCashFlow': cfo,
                'CapitalExpenditures': capex,
                'InvestingCashFlow': investing_cf,
                'FinancingCashFlow': financing_cf,
                'NetCashFlow': net_cf
            })
        
        return pd.DataFrame(projection_data, index=[str(latest_year + i) for i in range(1, self.projection_years + 1)])
    
    def build_model(self, assumptions: Dict) -> Dict:
        """
        Build complete operating model with projections
        
        Args:
            assumptions: Dict with projection assumptions (revenue_growth, gross_margin, etc.)
        
        Returns:
            Dict with historical and projected financial statements
        """
        if not self.prepare_historical_data():
            return {'error': 'Failed to prepare historical data'}
        
        # Project Income Statement
        revenue_growth = assumptions.get('revenue_growth')
        gross_margin = assumptions.get('gross_margin')
        sga_percent = assumptions.get('sga_percent')
        tax_rate = assumptions.get('tax_rate', 0.25)
        
        projected_income = self.project_income_statement(
            revenue_growth=revenue_growth,
            gross_margin=gross_margin,
            sga_percent=sga_percent,
            tax_rate=tax_rate
        )
        
        # Project Balance Sheet
        projected_balance = self.project_balance_sheet(projected_income)
        
        # Project Cash Flow
        projected_cashflow = self.project_cash_flow(projected_income, projected_balance)
        
        # Combine historical and projected
        latest_year_str = self.get_latest_year()
        if latest_year_str is None:
            return {'error': 'Could not determine latest year from historical data'}
        latest_year = int(latest_year_str)
        
        # Income Statement
        income_combined = pd.concat([self.income_statement, projected_income])
        
        # Balance Sheet
        balance_combined = pd.concat([self.balance_sheet, projected_balance])
        
        # Cash Flow
        cashflow_combined = pd.concat([self.cash_flow, projected_cashflow]) if not self.cash_flow.empty else projected_cashflow
        
        # Convert to dict and ensure all values are JSON-serializable (convert numpy types to native Python types)
        def convert_to_serializable(df_dict):
            """Convert DataFrame dict to JSON-serializable format"""
            import math
            result = {}
            for key, value in df_dict.items():
                if isinstance(value, dict):
                    row_dict = {}
                    for k, v in value.items():
                        # Handle NaN, inf, and other non-serializable values
                        if isinstance(v, (int, float, complex)):
                            if math.isnan(v) or math.isinf(v):
                                row_dict[str(k)] = 0.0
                            else:
                                row_dict[str(k)] = float(v)
                        else:
                            row_dict[str(k)] = v
                    result[str(key)] = row_dict
                else:
                    if isinstance(value, (int, float, complex)):
                        if math.isnan(value) or math.isinf(value):
                            result[str(key)] = 0.0
                        else:
                            result[str(key)] = float(value)
                    else:
                        result[str(key)] = value
            return result
        
        income_dict = income_combined.to_dict('index')
        balance_dict = balance_combined.to_dict('index')
        cashflow_dict = cashflow_combined.to_dict('index')
        
        return {
            'income_statement': convert_to_serializable(income_dict),
            'balance_sheet': convert_to_serializable(balance_dict),
            'cash_flow': convert_to_serializable(cashflow_dict),
            'latest_year': latest_year,
            'projection_years': self.projection_years
        }

