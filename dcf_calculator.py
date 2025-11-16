"""
DCF Calculator
Calculates WACC, Free Cash Flow, Terminal Value, and Enterprise/Equity Valuation
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional

class DCFCalculator:
    """Calculate DCF valuation from operating model projections"""
    
    def __init__(self, operating_model_data: Dict, assumptions: Dict):
        """
        Initialize DCF calculator
        
        Args:
            operating_model_data: Dict with projected financial statements
            assumptions: Dict with DCF assumptions (risk_free_rate, beta, etc.)
        """
        self.operating_model_data = operating_model_data
        self.assumptions = assumptions
        self.wacc = None
        self.free_cash_flows = None
        self.terminal_value = None
        self.enterprise_value = None
        self.equity_value = None
    
    def calculate_wacc(self) -> float:
        """
        Calculate Weighted Average Cost of Capital
        
        WACC = (E/(E+D)) × Re + (D/(E+D)) × Rd × (1 - Tax Rate)
        where:
        - Re = Cost of Equity = Risk-free rate + Beta × Market Risk Premium
        - Rd = Cost of Debt
        - E = Market value of equity
        - D = Market value of debt
        """
        risk_free_rate = self.assumptions.get('risk_free_rate', 0.03)
        beta = self.assumptions.get('beta', 1.0)
        market_risk_premium = self.assumptions.get('market_risk_premium', 0.06)
        cost_of_debt = self.assumptions.get('cost_of_debt', 0.05)
        tax_rate = self.assumptions.get('tax_rate', 0.25)
        debt_to_equity = self.assumptions.get('debt_to_equity', 0.3)
        
        # Cost of Equity (CAPM)
        cost_of_equity = risk_free_rate + (beta * market_risk_premium)
        
        # Calculate weights
        # If debt_to_equity = D/E, then D/(D+E) = (D/E) / (1 + D/E)
        debt_weight = debt_to_equity / (1 + debt_to_equity)
        equity_weight = 1 / (1 + debt_to_equity)
        
        # WACC
        wacc = (equity_weight * cost_of_equity) + (debt_weight * cost_of_debt * (1 - tax_rate))
        
        self.wacc = wacc
        return wacc
    
    def calculate_free_cash_flow(self) -> pd.Series:
        """
        Calculate Free Cash Flow for each projection year
        
        FCF = Operating Cash Flow - Capital Expenditures
        or
        FCF = EBIT × (1 - Tax Rate) + D&A - Capital Expenditures - Change in Working Capital
        """
        cash_flow = pd.DataFrame(self.operating_model_data.get('cash_flow', {}))
        income_statement = pd.DataFrame(self.operating_model_data.get('income_statement', {}))
        
        if cash_flow.empty or income_statement.empty:
            return pd.Series()
        
        # Get projection years (exclude historical)
        latest_year = self.operating_model_data.get('latest_year', 2023)
        projection_years = self.operating_model_data.get('projection_years', 5)
        
        fcf_data = {}
        
        for year_offset in range(1, projection_years + 1):
            year = latest_year + year_offset
            year_str = str(year)
            
            # Method 1: From Cash Flow Statement
            operating_cf = cash_flow.loc[year_str, 'OperatingCashFlow'] if year_str in cash_flow.index else 0
            capex = abs(cash_flow.loc[year_str, 'CapitalExpenditures']) if year_str in cash_flow.index else 0
            
            # FCF = Operating CF - CapEx
            fcf = operating_cf - capex
            
            # Alternative method using Income Statement (if cash flow not available)
            if fcf == 0 and year_str in income_statement.index:
                ebit = income_statement.loc[year_str, 'OperatingIncome'] if 'OperatingIncome' in income_statement.columns else 0
                da = abs(income_statement.loc[year_str, 'D&A']) if 'D&A' in income_statement.columns else 0
                tax_rate = self.assumptions.get('tax_rate', 0.25)
                
                # NOPAT = EBIT × (1 - Tax Rate)
                nopat = ebit * (1 - tax_rate)
                
                # Change in Working Capital
                if year_offset == 1:
                    change_wc = cash_flow.loc[year_str, 'ChangeInWorkingCapital'] if 'ChangeInWorkingCapital' in cash_flow.columns else 0
                else:
                    prev_year_str = str(year - 1)
                    change_wc = cash_flow.loc[year_str, 'ChangeInWorkingCapital'] if year_str in cash_flow.index and 'ChangeInWorkingCapital' in cash_flow.columns else 0
                
                # FCF = NOPAT + D&A - CapEx - Change in WC
                fcf = nopat + da - capex - change_wc
            
            fcf_data[year] = fcf
        
        self.free_cash_flows = pd.Series(fcf_data)
        return self.free_cash_flows
    
    def calculate_terminal_value(self) -> float:
        """
        Calculate Terminal Value using Gordon Growth Model
        
        Terminal Value = FCF_final × (1 + g) / (WACC - g)
        where g is the terminal growth rate
        """
        if self.free_cash_flows is None or self.free_cash_flows.empty:
            self.calculate_free_cash_flow()
        
        if self.wacc is None:
            self.calculate_wacc()
        
        terminal_growth = self.assumptions.get('terminal_growth_rate', 0.03)
        
        # Get final year FCF
        final_fcf = self.free_cash_flows.iloc[-1]
        
        # Terminal Value
        if self.wacc > terminal_growth:
            terminal_value = final_fcf * (1 + terminal_growth) / (self.wacc - terminal_growth)
        else:
            # If WACC <= growth rate, use a different approach
            terminal_value = final_fcf * 10  # Simple multiple fallback
        
        self.terminal_value = terminal_value
        return terminal_value
    
    def calculate_present_values(self) -> Dict:
        """
        Calculate present values of projected FCFs and terminal value
        """
        if self.free_cash_flows is None or self.free_cash_flows.empty:
            self.calculate_free_cash_flow()
        
        if self.wacc is None:
            self.calculate_wacc()
        
        if self.terminal_value is None:
            self.calculate_terminal_value()
        
        latest_year = self.operating_model_data.get('latest_year', 2023)
        
        # Present value of projected FCFs
        pv_fcf = {}
        for year, fcf in self.free_cash_flows.items():
            years_ahead = year - latest_year
            pv = fcf / ((1 + self.wacc) ** years_ahead)
            pv_fcf[year] = pv
        
        # Present value of terminal value
        projection_years = self.operating_model_data.get('projection_years', 5)
        terminal_year = latest_year + projection_years
        years_to_terminal = projection_years
        pv_terminal = self.terminal_value / ((1 + self.wacc) ** years_to_terminal)
        
        return {
            'pv_fcf': pv_fcf,
            'pv_terminal': pv_terminal,
            'total_pv_fcf': sum(pv_fcf.values())
        }
    
    def calculate_enterprise_value(self) -> float:
        """
        Calculate Enterprise Value
        
        Enterprise Value = Sum of PV of FCFs + PV of Terminal Value
        Includes debug statements for traceability.
        """
        pv_data = self.calculate_present_values()
        
        enterprise_value = pv_data['total_pv_fcf'] + pv_data['pv_terminal']
        
        self.enterprise_value = enterprise_value
        return enterprise_value
    
    def calculate_equity_value(self) -> float:
        """
        Calculate Equity Value
        
        Equity Value = Enterprise Value - Net Debt
        Net Debt = Total Debt - Cash and Cash Equivalents
        """
        if self.enterprise_value is None:
            self.calculate_enterprise_value()
        
        # Get latest balance sheet data
        balance_sheet = pd.DataFrame(self.operating_model_data.get('balance_sheet', {}))
        latest_year = self.operating_model_data.get('latest_year', 2023)
        latest_year_str = str(latest_year)
        
        if not balance_sheet.empty and latest_year_str in balance_sheet.index:
            # Total Debt
            long_term_debt = balance_sheet.loc[latest_year_str, 'LongTermDebt'] if 'LongTermDebt' in balance_sheet.columns else 0
            short_term_debt = 0  # Assume included in short-term liabilities
            total_debt = long_term_debt + short_term_debt
            
            # Cash and Cash Equivalents
            cash = balance_sheet.loc[latest_year_str, 'Cash'] if 'Cash' in balance_sheet.columns else 0
            short_term_investments = balance_sheet.loc[latest_year_str, 'ShortTermInvestments'] if 'ShortTermInvestments' in balance_sheet.columns else 0
            total_cash = cash + short_term_investments
            
            # Net Debt
            net_debt = total_debt - total_cash
        else:
            net_debt = 0
        
        # Equity Value
        equity_value = self.enterprise_value - net_debt
        
        self.equity_value = equity_value
        return equity_value
    
    def calculate_all(self) -> Dict:
        """
        Calculate all DCF metrics and return summary
        """
        wacc = self.calculate_wacc()
        fcf = self.calculate_free_cash_flow()
        terminal_value = self.calculate_terminal_value()
        enterprise_value = self.calculate_enterprise_value()
        equity_value = self.calculate_equity_value()
        pv_data = self.calculate_present_values()
        
        # Get shares outstanding (if available) to calculate price per share
        # For now, we'll return equity value
        shares_outstanding = self.assumptions.get('shares_outstanding', None)
        price_per_share = equity_value / shares_outstanding if shares_outstanding else None
        
        return {
            'wacc': wacc,
            'free_cash_flows': fcf.to_dict() if isinstance(fcf, pd.Series) else {},
            'terminal_value': terminal_value,
            'present_value_fcf': pv_data['pv_fcf'],
            'present_value_terminal': pv_data['pv_terminal'],
            'total_pv_fcf': pv_data['total_pv_fcf'],
            'enterprise_value': enterprise_value,
            'equity_value': equity_value,
            'price_per_share': price_per_share,
            'assumptions': {
                'risk_free_rate': self.assumptions.get('risk_free_rate'),
                'beta': self.assumptions.get('beta'),
                'market_risk_premium': self.assumptions.get('market_risk_premium'),
                'cost_of_debt': self.assumptions.get('cost_of_debt'),
                'tax_rate': self.assumptions.get('tax_rate'),
                'debt_to_equity': self.assumptions.get('debt_to_equity'),
                'terminal_growth_rate': self.assumptions.get('terminal_growth_rate')
            }
        }

