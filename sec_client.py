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
    
    BASE_URL = "https://www.sec.gov"
    HEADERS = {
        'User-Agent': 'DCF Tool (contact@example.com)',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'data.sec.gov'
    }
    
    # XBRL concept mappings for financial statements
    # Comprehensive list of XBRL tags used in SEC filings
    INCOME_STATEMENT_CONCEPTS = {
        'Revenue': [
            'Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 
            'SalesRevenueNet', 'RevenuesNetOfInterestExpense', 
            'RevenueFromContractWithCustomerIncludingAssessedTax',
            'SalesRevenueGoodsNet', 'SalesRevenueServicesNet', 
            'RevenueFromContractWithCustomerBeforeReassessment',
            'TotalRevenue', 'RevenueFromContractWithCustomerExcludingAssessedTax',
            'SalesRevenueServicesAndOther', 'ProductRevenueNet', 'ServiceRevenueNet',
            'RevenueFromContractWithCustomer', 'NetSales', 'SalesAndOtherOperatingRevenue'
        ],
        'COGS': [
            'CostOfGoodsAndServicesSold', 'CostOfRevenue', 'CostOfSales', 'CostOfGoodsSold',
            'CostOfProductsSold', 'CostOfServices', 
            'CostOfGoodsAndServicesSoldExcludingDepreciationDepletionAndAmortization',
            'CostOfRevenueExcludingDepreciationAndAmortization', 'CostOfSalesExcludingDepreciationAndAmortization',
            'CostOfGoodsAndServicesSoldIncludingDepreciationAndAmortization', 'CostOfRevenueIncludingDepreciationAndAmortization'
        ],
        'SG&A': [
            'SellingGeneralAndAdministrativeExpense', 
            'SellingAndMarketingExpense', 'GeneralAndAdministrativeExpense',
            'SellingGeneralAndAdministrativeExpenseExcludingOther',
            'SellingGeneralAndAdministrativeExpenseIncludingOther',
            'OperatingExpenses', 'OperatingExpensesExcludingCostOfGoodsSold',
            'SellingExpense', 'MarketingExpense', 'GeneralAndAdministrativeExpenseExcludingOther',
            'ResearchAndDevelopmentExpense',  # Some companies include R&D in SG&A
            'SellingGeneralAndAdministrativeAndOtherExpenses',
            'OperatingExpensesExcludingDepreciationAndAmortization',
            'OperatingExpensesIncludingDepreciationAndAmortization'
        ],
        'EBITDA': [
            'EarningsBeforeInterestTaxesDepreciationAndAmortization', 
            'EarningsBeforeInterestTaxesDepreciationAndAmortizationIncludingEquityInEarningsOfUnconsolidatedEntities',
            'EarningsBeforeInterestTaxesDepreciationAndAmortizationExcludingEquityInEarningsOfUnconsolidatedEntities'
        ],
        'D&A': [
            'DepreciationAndAmortization', 'DepreciationDepletionAndAmortization',
            'Depreciation', 'Amortization', 'DepreciationAndAmortizationIncludingImpairment',
            'DepreciationAndAmortizationExcludingImpairment', 'DepreciationOfPropertyPlantAndEquipment',
            'AmortizationOfIntangibleAssets', 'DepreciationAmortizationAndAccretionNet'
        ],
        'OperatingIncome': [
            'OperatingIncomeLoss', 
            'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest',
            'OperatingIncome', 
            'IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments',
            'IncomeLossFromContinuingOperationsBeforeIncomeTaxes',
            'OperatingIncomeLossExcludingOther', 'OperatingIncomeLossIncludingOther'
        ],
        'InterestExpense': [
            'InterestExpense', 'InterestAndDebtExpense', 'InterestExpenseDebt',
            'InterestExpenseIncludingAmortizationOfDebtDiscount', 'InterestExpenseBorrowings',
            'InterestExpenseExcludingAmortizationOfDebtDiscount', 'InterestExpenseLongTermDebt',
            'InterestExpenseShortTermDebt', 'InterestExpenseOnDebt'
        ],
        'InterestIncome': [
            'InterestIncome', 'InvestmentIncomeInterest', 'InterestAndDividendIncomeOperating',
            'InterestIncomeOperating', 'InterestAndInvestmentIncome', 'InterestIncomeExcludingAmortization'
        ],
        'TaxExpense': [
            'IncomeTaxExpenseBenefit', 'ProvisionForIncomeTaxes', 'IncomeTaxExpense',
            'IncomeTaxExpenseContinuingOperations', 'IncomeTaxExpenseBenefitContinuingOperations',
            'ProvisionForIncomeTaxesContinuingOperations', 'IncomeTaxExpenseBenefitExcludingOther'
        ],
        'NetIncome': [
            'NetIncomeLoss', 'ProfitLoss', 'NetIncomeLossAvailableToCommonStockholdersBasic',
            'NetIncomeLossAttributableToParent', 'NetIncomeLossIncludingPortionAttributableToNoncontrollingInterest',
            'NetIncomeLossAvailableToCommonStockholdersDiluted', 'NetIncomeLossAttributableToControllingInterest'
        ]
    }
    
    BALANCE_SHEET_CONCEPTS = {
        'Cash': [
            'CashAndCashEquivalentsAtCarryingValue', 'CashCashEquivalentsAndShortTermInvestments',
            'Cash', 'CashAndCashEquivalents', 'CashCashEquivalentsAndRestrictedCash',
            'CashCashEquivalentsAndRestrictedCashRestrictedCash', 'CashAndShortTermInvestments'
        ],
        'ShortTermInvestments': [
            'ShortTermInvestments', 'AvailableForSaleSecuritiesCurrent',
            'MarketableSecuritiesCurrent', 'ShortTermInvestmentsAvailableForSale',
            'TradingSecuritiesCurrent', 'ShortTermInvestmentsAtCarryingValue'
        ],
        'CurrentAssets': [
            'AssetsCurrent', 'CurrentAssets', 'TotalCurrentAssets',
            'AssetsCurrentExcludingOtherAssets', 'AssetsCurrentIncludingOtherAssets'
        ],
        'PPE': [
            'PropertyPlantAndEquipmentNet', 'PropertyPlantAndEquipment',
            'PropertyPlantAndEquipmentNetOfAccumulatedDepreciation', 'PropertyPlantAndEquipmentGross',
            'PropertyPlantAndEquipmentNetIncludingLeaseRightOfUseAsset',
            'PropertyPlantAndEquipmentNetExcludingLeaseRightOfUseAsset'
        ],
        'OtherLongTermAssets': [
            'AssetsNoncurrent', 'OtherAssetsNoncurrent', 'NoncurrentAssets',
            'OtherAssets', 'OtherNoncurrentAssets', 'AssetsNoncurrentExcludingOtherAssets',
            'LongTermInvestments', 'IntangibleAssetsNetExcludingGoodwill', 'Goodwill'
        ],
        'TotalAssets': [
            'Assets', 'AssetsTotal', 'TotalAssets',
            'AssetsIncludingOtherAssets', 'AssetsExcludingOtherAssets'
        ],
        'ShortTermLiabilities': [
            'LiabilitiesCurrent', 'CurrentLiabilities', 'TotalCurrentLiabilities',
            'LiabilitiesCurrentExcludingOtherLiabilities', 'AccountsPayableCurrent',
            'AccruedLiabilitiesCurrent', 'ShortTermDebt'
        ],
        'LongTermDebt': [
            'LongTermDebt', 'LongTermDebtAndCapitalLeaseObligations',
            'LongTermDebtExcludingCurrentMaturities', 'LongTermDebtNetOfCurrentMaturities',
            'LongTermDebtAndCapitalLeaseObligationsExcludingCurrentMaturities',
            'LongTermDebtIncludingCurrentMaturities'
        ],
        'LongTermLeases': [
            'OperatingLeaseLiabilityNoncurrent', 'LeaseLiabilityNoncurrent',
            'LongTermOperatingLeaseLiability', 'FinanceLeaseLiabilityNoncurrent',
            'OperatingLeaseRightOfUseAsset', 'FinanceLeaseRightOfUseAsset'
        ],
        'OtherLongTermLiabilities': [
            'LiabilitiesNoncurrent', 'OtherLiabilitiesNoncurrent',
            'OtherNoncurrentLiabilities', 'TotalNoncurrentLiabilities',
            'LiabilitiesNoncurrentExcludingOtherLiabilities', 'DeferredTaxLiabilitiesNoncurrent'
        ],
        'TotalLiabilities': [
            'Liabilities', 'LiabilitiesTotal', 'TotalLiabilities',
            'LiabilitiesIncludingOtherLiabilities', 'LiabilitiesExcludingOtherLiabilities'
        ],
        'RetainedEarnings': [
            'RetainedEarningsAccumulatedDeficit', 'RetainedEarnings',
            'RetainedEarningsAppropriated', 'AccumulatedDeficit',
            'RetainedEarningsUnappropriated', 'AccumulatedOtherComprehensiveIncomeLossNetOfTax'
        ],
        'CommonStock': [
            'CommonStockValue', 'CommonStocksIncludingAdditionalPaidInCapital',
            'CommonStockSharesOutstanding', 'CommonStockParOrStatedValuePerShare',
            'CommonStockSharesAuthorized', 'CommonStockParValue'
        ],
        'PaidInCapital': [
            'AdditionalPaidInCapital', 'CommonStockAndAdditionalPaidInCapital',
            'AdditionalPaidInCapitalCommonStock', 'PaidInCapital',
            'AdditionalPaidInCapitalAndRetainedEarnings'
        ],
        'TotalEquity': [
            'Equity', 'StockholdersEquity', 'EquityAttributableToParent',
            'StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest',
            'EquityExcludingOtherEquity', 'EquityIncludingOtherEquity'
        ]
    }
    
    CASH_FLOW_CONCEPTS = {
        'OperatingCashFlow': [
            'NetCashProvidedByUsedInOperatingActivities', 'CashFlowFromOperatingActivities',
            'CashProvidedByUsedInOperatingActivities', 'NetCashFlowFromOperatingActivities',
            'CashFlowFromOperatingActivitiesContinuingOperations'
        ],
        'InvestingCashFlow': [
            'NetCashProvidedByUsedInInvestingActivities', 'CashFlowFromInvestingActivities',
            'CashProvidedByUsedInInvestingActivities', 'NetCashFlowFromInvestingActivities',
            'CashFlowFromInvestingActivitiesContinuingOperations'
        ],
        'FinancingCashFlow': [
            'NetCashProvidedByUsedInFinancingActivities', 'CashFlowFromFinancingActivities',
            'CashProvidedByUsedInFinancingActivities', 'NetCashFlowFromFinancingActivities',
            'CashFlowFromFinancingActivitiesContinuingOperations'
        ],
        'CapitalExpenditures': [
            'PaymentsToAcquirePropertyPlantAndEquipment', 'CapitalExpenditures',
            'PaymentsForPropertyPlantAndEquipment', 'CapitalExpendituresIncurredButNotYetPaid',
            'PaymentsToAcquirePropertyPlantAndEquipmentAndOtherIntangibleAssets',
            'PaymentsToAcquireProductiveAssets'
        ],
        'NetCashFlow': [
            'CashCashEquivalentsAndShortTermInvestments', 'CashAndCashEquivalentsAtCarryingValue',
            'NetIncreaseDecreaseInCashAndCashEquivalents', 'CashAndCashEquivalentsPeriodIncreaseDecrease',
            'CashCashEquivalentsAndRestrictedCashPeriodIncreaseDecreaseIncludingExchangeRateEffect'
        ]
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def get_cik_from_ticker(self, ticker: str) -> Optional[str]:
        """Convert ticker symbol to CIK number"""
        try:
            # SEC company tickers JSON - new format is a dict with numeric keys
            # Use www.sec.gov for this endpoint (not data.sec.gov)
            url = f"https://www.sec.gov/files/company_tickers.json"
            # Create a new request with proper headers (don't use session headers for this endpoint)
            headers = {
                'User-Agent': 'DCF Tool contact@example.com',
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip, deflate'
            }
            # Use requests directly instead of session to avoid header conflicts
            import requests as req_lib
            response = req_lib.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            ticker_upper = ticker.upper().strip()
            
            # New SEC API structure: dict with numeric keys, each value is:
            # {'cik_str': 1234567, 'ticker': 'AAPL', 'title': 'COMPANY NAME'}
            if isinstance(data, dict):
                for key, company_info in data.items():
                    if isinstance(company_info, dict):
                        entry_ticker = str(company_info.get('ticker', '')).upper().strip()
                        if entry_ticker == ticker_upper:
                            cik = str(company_info.get('cik_str', ''))
                            if cik:
                                # Pad CIK to 10 digits
                                return cik.zfill(10)
            
            print(f"Ticker {ticker} not found in SEC database")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Network error fetching CIK for ticker {ticker}: {e}")
            return None
        except Exception as e:
            print(f"Error fetching CIK for ticker {ticker}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_company_facts(self, cik: str) -> Optional[Dict]:
        """Fetch company facts (XBRL data) for a given CIK"""
        try:
            # Company facts API uses data.sec.gov, not www.sec.gov
            url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik.zfill(10)}.json"
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
        
        # Try multiple namespaces if us-gaap doesn't work
        namespaces_to_try = [namespace]
        if namespace == 'us-gaap':
            namespaces_to_try.extend(['ifrs-full', 'dei'])  # Try IFRS and DEI namespaces too
        
        result = {}
        
        for ns in namespaces_to_try:
            if ns not in facts_data:
                continue
            
            namespace_facts = facts_data[ns]
            
            for concept_name in concept_list:
                if concept_name in namespace_facts:
                    concept_data = namespace_facts[concept_name]
                    if 'units' in concept_data:
                        # Prefer USD units, but use any available
                        preferred_units = ['USD', 'usd', 'shares', 'USD/shares']
                        unit_to_use = None
                        
                        # Find preferred unit
                        for pref_unit in preferred_units:
                            if pref_unit in concept_data['units']:
                                unit_to_use = pref_unit
                                break
                        
                        # If no preferred unit, use the first available
                        if unit_to_use is None and concept_data['units']:
                            unit_to_use = list(concept_data['units'].keys())[0]
                        
                        if unit_to_use and concept_data['units'][unit_to_use]:
                            data_list = concept_data['units'][unit_to_use]
                            # Filter for annual data (not quarterly) and get most recent years
                            annual_data = []
                            for item in data_list:
                                # Check if this is annual data (typically ends in -12-31 or is marked as annual)
                                end_date = item.get('end', '')
                                start_date = item.get('start', '')
                                # Annual data typically spans a full year or ends in December
                                if end_date and len(end_date) >= 4:
                                    # Check if it's annual (ends in -12-31 or spans full year)
                                    if end_date.endswith('-12-31') or (start_date and end_date[:4] != start_date[:4] and len(start_date) >= 4):
                                        annual_data.append(item)
                            
                            # If no annual data found, use all data but prefer later dates
                            if not annual_data:
                                annual_data = data_list
                            
                            # Sort by end date (most recent first)
                            annual_data.sort(key=lambda x: x.get('end', ''), reverse=True)
                            
                            # Group by year, taking the most recent value for each year
                            years_seen = set()
                            for item in annual_data:
                                end_date = item.get('end', '')
                                if end_date and len(end_date) >= 4:
                                    year = end_date[:4]
                                    # Only take one value per year (the most recent one, which comes first after sorting)
                                    if year not in years_seen:
                                        val = float(item.get('val', 0))
                                        
                                        # Handle unit conversion if needed (some are in thousands)
                                        # Check if unit indicates thousands
                                        if 'thousand' in unit_to_use.lower() or 'thousands' in unit_to_use.lower():
                                            val = val * 1000
                                        
                                        result[year] = val
                                        result[f'{year}_date'] = end_date
                                        years_seen.add(year)
                                        
                                        # Limit to most recent N years
                                        if len(years_seen) >= years:
                                            break
                    
                    # If we found data, break out of concept loop (use first matching concept)
                    if result:
                        break
            
            # If we found data in this namespace, break
            if result:
                break
        
        return result
    
    def parse_income_statement(self, facts: Dict) -> pd.DataFrame:
        """Parse Income Statement data from XBRL facts"""
        income_data = {}
        
        # Extract last 10 years of data to ensure we have enough, then filter to 3 most recent
        for key, concept_list in self.INCOME_STATEMENT_CONCEPTS.items():
            historical = self.extract_historical_data(facts, concept_list, years=10)
            income_data[key] = historical
            # Debug: print what we found
            if historical:
                years_found = [k for k in historical.keys() if not k.endswith('_date')]
                print(f"DEBUG: Found {key} for years: {sorted(years_found, reverse=True)[:3]}")
            else:
                print(f"DEBUG: No data found for {key} (tried {len(concept_list)} concepts)")
        
        # Convert to DataFrame
        years = set()
        for key, values in income_data.items():
            years.update([k for k in values.keys() if not k.endswith('_date')])
        
        if not years:
            print("DEBUG: No years found in income statement data")
            return pd.DataFrame()
        
        # Sort years and take only the most recent 3 years
        sorted_years = sorted([int(y) for y in years if y.isdigit()], reverse=True)
        recent_years = sorted_years[:3]  # Only 3 most recent years
        
        df_data = {}
        for year in recent_years:
            year_str = str(year)
            row = {}
            for key in self.INCOME_STATEMENT_CONCEPTS.keys():
                row[key] = income_data.get(key, {}).get(year_str, 0)
            df_data[year_str] = row
        
        # Return with years in ascending order (oldest to newest)
        return pd.DataFrame(df_data).T.sort_index()
    
    def parse_balance_sheet(self, facts: Dict) -> pd.DataFrame:
        """Parse Balance Sheet data from XBRL facts"""
        balance_data = {}
        
        # Extract last 10 years of data to ensure we have enough, then filter to 3 most recent
        for key, concept_list in self.BALANCE_SHEET_CONCEPTS.items():
            historical = self.extract_historical_data(facts, concept_list, years=10)
            balance_data[key] = historical
        
        # Convert to DataFrame
        years = set()
        for key, values in balance_data.items():
            years.update([k for k in values.keys() if not k.endswith('_date')])
        
        if not years:
            return pd.DataFrame()
        
        # Sort years and take only the most recent 3 years
        sorted_years = sorted([int(y) for y in years if y.isdigit()], reverse=True)
        recent_years = sorted_years[:3]  # Only 3 most recent years
        
        df_data = {}
        for year in recent_years:
            year_str = str(year)
            row = {}
            for key in self.BALANCE_SHEET_CONCEPTS.keys():
                row[key] = balance_data.get(key, {}).get(year_str, 0)
            df_data[year_str] = row
        
        return pd.DataFrame(df_data).T.sort_index()
    
    def parse_cash_flow(self, facts: Dict) -> pd.DataFrame:
        """Parse Cash Flow Statement data from XBRL facts"""
        cashflow_data = {}
        
        # Extract last 10 years of data to ensure we have enough, then filter to 3 most recent
        for key, concept_list in self.CASH_FLOW_CONCEPTS.items():
            historical = self.extract_historical_data(facts, concept_list, years=10)
            cashflow_data[key] = historical
            # Debug: print what we found
            if historical:
                years_found = [k for k in historical.keys() if not k.endswith('_date')]
                print(f"DEBUG: Found {key} for years: {sorted(years_found, reverse=True)[:3]}")
            else:
                print(f"DEBUG: No data found for {key} (tried {len(concept_list)} concepts)")
        
        # Convert to DataFrame
        years = set()
        for key, values in cashflow_data.items():
            years.update([k for k in values.keys() if not k.endswith('_date')])
        
        if not years:
            return pd.DataFrame()
        
        # Sort years and take only the most recent 3 years
        sorted_years = sorted([int(y) for y in years if y.isdigit()], reverse=True)
        recent_years = sorted_years[:3]  # Only 3 most recent years
        
        df_data = {}
        for year in recent_years:
            year_str = str(year)
            row = {}
            for key in self.CASH_FLOW_CONCEPTS.keys():
                row[key] = cashflow_data.get(key, {}).get(year_str, 0)
            df_data[year_str] = row
        
        return pd.DataFrame(df_data).T.sort_index()
    
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
        
        # Debug: Print sample data
        if not income_statement.empty:
            print(f"DEBUG: Income statement shape: {income_statement.shape}")
            print(f"DEBUG: Sample revenue values: {income_statement['Revenue'].head() if 'Revenue' in income_statement.columns else 'No Revenue column'}")
        if not balance_sheet.empty:
            print(f"DEBUG: Balance sheet shape: {balance_sheet.shape}")
        if not cash_flow.empty:
            print(f"DEBUG: Cash flow shape: {cash_flow.shape}")
        
        return {
            'company_name': company_name,
            'cik': cik,
            'income_statement': income_statement.to_dict('index') if not income_statement.empty else {},
            'balance_sheet': balance_sheet.to_dict('index') if not balance_sheet.empty else {},
            'cash_flow': cash_flow.to_dict('index') if not cash_flow.empty else {}
        }

