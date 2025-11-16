"""
SEC XBRL API Client
Fetches and parses financial data from SEC EDGAR database
"""
import requests
import pandas as pd
from typing import Dict, List, Optional, Tuple
import time

class SECClient:
    """Client for fetching financial data from SEC XBRL API"""
    
    BASE_URL = "https://data.sec.gov"
    HEADERS = {
        'User-Agent': 'DCF Tool (contact@example.com)',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'data.sec.gov'
    }
    
    # XBRL concept mappings for financial statements
    INCOME_STATEMENT_CONCEPTS = {
        'Revenue': ['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 
                   'SalesRevenueNet', 'RevenuesNetOfInterestExpense'],
        'COGS': ['CostOfGoodsAndServicesSold', 'CostOfRevenue', 'CostOfSales'],
        'SG&A': ['SellingGeneralAndAdministrativeExpense', 'OperatingExpenses'],
        'EBITDA': ['EarningsBeforeInterestTaxesDepreciationAndAmortization'],
        'D&A': ['DepreciationAndAmortization', 'DepreciationDepletionAndAmortization'],
        'OperatingIncome': ['OperatingIncomeLoss', 'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest'],
        'InterestExpense': ['InterestExpense', 'InterestAndDebtExpense'],
        'InterestIncome': ['InterestIncome', 'InvestmentIncomeInterest'],
        'TaxExpense': ['IncomeTaxExpenseBenefit', 'ProvisionForIncomeTaxes'],
        'NetIncome': ['NetIncomeLoss', 'ProfitLoss']
    }
    
    BALANCE_SHEET_CONCEPTS = {
        'Cash': ['CashAndCashEquivalentsAtCarryingValue', 'CashCashEquivalentsAndShortTermInvestments'],
        'ShortTermInvestments': ['ShortTermInvestments', 'AvailableForSaleSecuritiesCurrent'],
        'CurrentAssets': ['AssetsCurrent', 'CurrentAssets'],
        'PPE': ['PropertyPlantAndEquipmentNet', 'PropertyPlantAndEquipment'],
        'OtherLongTermAssets': ['AssetsNoncurrent', 'OtherAssetsNoncurrent'],
        'TotalAssets': ['Assets', 'AssetsTotal'],
        'ShortTermLiabilities': ['LiabilitiesCurrent', 'CurrentLiabilities'],
        'LongTermDebt': ['LongTermDebt', 'LongTermDebtAndCapitalLeaseObligations'],
        'LongTermLeases': ['OperatingLeaseLiabilityNoncurrent', 'LeaseLiabilityNoncurrent'],
        'OtherLongTermLiabilities': ['LiabilitiesNoncurrent', 'OtherLiabilitiesNoncurrent'],
        'TotalLiabilities': ['Liabilities', 'LiabilitiesTotal'],
        'RetainedEarnings': ['RetainedEarningsAccumulatedDeficit', 'RetainedEarnings'],
        'CommonStock': ['CommonStockValue', 'CommonStocksIncludingAdditionalPaidInCapital'],
        'PaidInCapital': ['AdditionalPaidInCapital', 'CommonStockAndAdditionalPaidInCapital'],
        'TotalEquity': ['Equity', 'StockholdersEquity']
    }
    
    CASH_FLOW_CONCEPTS = {
        'OperatingCashFlow': ['NetCashProvidedByUsedInOperatingActivities', 'CashFlowFromOperatingActivities'],
        'InvestingCashFlow': ['NetCashProvidedByUsedInInvestingActivities', 'CashFlowFromInvestingActivities'],
        'FinancingCashFlow': ['NetCashProvidedByUsedInFinancingActivities', 'CashFlowFromFinancingActivities'],
        'CapitalExpenditures': ['PaymentsToAcquirePropertyPlantAndEquipment', 'CapitalExpenditures'],
        'NetCashFlow': ['CashCashEquivalentsAndShortTermInvestments', 'CashAndCashEquivalentsAtCarryingValue']
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def get_cik_from_ticker(self, ticker: str) -> Optional[str]:
        """Convert ticker symbol to CIK number"""
        try:
            # SEC company tickers JSON
            url = f"{self.BASE_URL}/files/company_tickers.json"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            ticker_upper = ticker.upper()
            for entry in data['data']:
                if entry[0].upper() == ticker_upper:
                    cik = str(entry[2])
                    # Pad CIK to 10 digits
                    return cik.zfill(10)
            return None
        except Exception as e:
            print(f"Error fetching CIK for ticker {ticker}: {e}")
            return None
    
    def get_company_facts(self, cik: str) -> Optional[Dict]:
        """Fetch company facts (XBRL data) for a given CIK"""
        try:
            url = f"{self.BASE_URL}/api/xbrl/companyfacts/CIK{cik.zfill(10)}.json"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            time.sleep(0.1)  # Rate limiting
            return response.json()
        except Exception as e:
            print(f"Error fetching company facts for CIK {cik}: {e}")
            return None
    
    def extract_concept_value(self, facts: Dict, concept_list: List[str], 
                             namespace: str = 'us-gaap') -> Optional[float]:
        """Extract the most recent value for a concept from XBRL facts"""
        if 'facts' not in facts:
            return None
        
        facts_data = facts['facts']
        if namespace not in facts_data:
            return None
        
        namespace_facts = facts_data[namespace]
        
        for concept_name in concept_list:
            if concept_name in namespace_facts:
                concept_data = namespace_facts[concept_name]
                if 'units' in concept_data:
                    # Get the most recent value (usually in USD)
                    for unit, data_list in concept_data['units'].items():
                        if data_list and len(data_list) > 0:
                            # Sort by end date, get most recent
                            sorted_data = sorted(data_list, 
                                                key=lambda x: x.get('end', ''), 
                                                reverse=True)
                            if sorted_data:
                                return float(sorted_data[0].get('val', 0))
        return None
    
    def extract_historical_data(self, facts: Dict, concept_list: List[str],
                               namespace: str = 'us-gaap', years: int = 5) -> Dict[str, float]:
        """Extract historical values for a concept over multiple years"""
        if 'facts' not in facts:
            return {}
        
        facts_data = facts['facts']
        if namespace not in facts_data:
            return {}
        
        namespace_facts = facts_data[namespace]
        result = {}
        
        for concept_name in concept_list:
            if concept_name in namespace_facts:
                concept_data = namespace_facts[concept_name]
                if 'units' in concept_data:
                    for unit, data_list in concept_data['units'].items():
                        if data_list:
                            # Group by year
                            for item in data_list:
                                end_date = item.get('end', '')
                                if end_date and len(end_date) >= 4:
                                    year = end_date[:4]
                                    val = float(item.get('val', 0))
                                    # Take the most recent value for each year
                                    if year not in result or end_date > result.get(f'{year}_date', ''):
                                        result[year] = val
                                        result[f'{year}_date'] = end_date
        return result
    
    def parse_income_statement(self, facts: Dict) -> pd.DataFrame:
        """Parse Income Statement data from XBRL facts"""
        income_data = {}
        
        for key, concept_list in self.INCOME_STATEMENT_CONCEPTS.items():
            historical = self.extract_historical_data(facts, concept_list)
            income_data[key] = historical
        
        # Convert to DataFrame
        years = set()
        for key, values in income_data.items():
            years.update([k for k in values.keys() if not k.endswith('_date')])
        
        if not years:
            return pd.DataFrame()
        
        df_data = {}
        for year in sorted(years):
            row = {}
            for key in self.INCOME_STATEMENT_CONCEPTS.keys():
                row[key] = income_data.get(key, {}).get(year, 0)
            df_data[year] = row
        
        return pd.DataFrame(df_data).T
    
    def parse_balance_sheet(self, facts: Dict) -> pd.DataFrame:
        """Parse Balance Sheet data from XBRL facts"""
        balance_data = {}
        
        for key, concept_list in self.BALANCE_SHEET_CONCEPTS.items():
            historical = self.extract_historical_data(facts, concept_list)
            balance_data[key] = historical
        
        # Convert to DataFrame
        years = set()
        for key, values in balance_data.items():
            years.update([k for k in values.keys() if not k.endswith('_date')])
        
        if not years:
            return pd.DataFrame()
        
        df_data = {}
        for year in sorted(years):
            row = {}
            for key in self.BALANCE_SHEET_CONCEPTS.keys():
                row[key] = balance_data.get(key, {}).get(year, 0)
            df_data[year] = row
        
        return pd.DataFrame(df_data).T
    
    def parse_cash_flow(self, facts: Dict) -> pd.DataFrame:
        """Parse Cash Flow Statement data from XBRL facts"""
        cashflow_data = {}
        
        for key, concept_list in self.CASH_FLOW_CONCEPTS.items():
            historical = self.extract_historical_data(facts, concept_list)
            cashflow_data[key] = historical
        
        # Convert to DataFrame
        years = set()
        for key, values in cashflow_data.items():
            years.update([k for k in values.keys() if not k.endswith('_date')])
        
        if not years:
            return pd.DataFrame()
        
        df_data = {}
        for year in sorted(years):
            row = {}
            for key in self.CASH_FLOW_CONCEPTS.keys():
                row[key] = cashflow_data.get(key, {}).get(year, 0)
            df_data[year] = row
        
        return pd.DataFrame(df_data).T
    
    def fetch_company_data(self, identifier: str) -> Dict:
        """
        Main method to fetch all financial data for a company
        identifier can be either a ticker symbol or CIK number
        """
        # Determine if identifier is ticker or CIK
        if identifier.isdigit():
            cik = identifier.zfill(10)
        else:
            cik = self.get_cik_from_ticker(identifier)
            if not cik:
                return {'error': f'Could not find CIK for ticker {identifier}'}
        
        facts = self.get_company_facts(cik)
        if not facts:
            return {'error': f'Could not fetch data for CIK {cik}'}
        
        # Extract company name
        company_name = facts.get('entityName', 'Unknown Company')
        
        # Parse financial statements
        income_statement = self.parse_income_statement(facts)
        balance_sheet = self.parse_balance_sheet(facts)
        cash_flow = self.parse_cash_flow(facts)
        
        return {
            'company_name': company_name,
            'cik': cik,
            'income_statement': income_statement.to_dict('index') if not income_statement.empty else {},
            'balance_sheet': balance_sheet.to_dict('index') if not balance_sheet.empty else {},
            'cash_flow': cash_flow.to_dict('index') if not cash_flow.empty else {}
        }

