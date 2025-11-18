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
        'R&D': [
            'ResearchAndDevelopmentExpense', 'ResearchAndDevelopmentExpenseNetOfReimbursements',
            'ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost',
            'ResearchAndDevelopmentExpenseIncludingAcquiredInProcessCost',
            'ResearchAndDevelopmentExpenseSoftwareExcludingAcquiredInProcessCost',
            'ResearchAndDevelopmentExpenseSoftwareIncludingAcquiredInProcessCost'
        ],
        'SG&A': [
            'SellingGeneralAndAdministrativeExpense', 
            'SellingAndMarketingExpense', 'GeneralAndAdministrativeExpense',
            'SellingGeneralAndAdministrativeExpenseExcludingOther',
            'SellingGeneralAndAdministrativeExpenseIncludingOther',
            'OperatingExpenses', 'OperatingExpensesExcludingCostOfGoodsSold',
            'SellingExpense', 'MarketingExpense', 'GeneralAndAdministrativeExpenseExcludingOther',
            'SellingGeneralAndAdministrativeAndOtherExpenses',
            'OperatingExpensesExcludingDepreciationAndAmortization',
            'OperatingExpensesIncludingDepreciationAndAmortization'
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
        'OtherIncomeExpenseNet': [
            'OtherIncomeExpenseNet', 'OtherIncomeExpense', 'NonoperatingIncomeExpense',
            'OtherIncomeLoss', 'IncomeLossFromOtherActivities', 'OtherNonoperatingIncomeExpense',
            'OtherIncomeExpenseNetOfInterest', 'OtherIncomeExpenseIncludingInterest',
            'OtherIncomeExpenseExcludingInterest', 'OtherIncomeExpenseNetOfInterestAndOther'
        ],
        'TaxExpense': [
            'IncomeTaxExpenseBenefit', 'ProvisionForIncomeTaxes', 'IncomeTaxExpense',
            'IncomeTaxExpenseContinuingOperations', 'IncomeTaxExpenseBenefitContinuingOperations',
            'ProvisionForIncomeTaxesContinuingOperations', 'IncomeTaxExpenseBenefitExcludingOther'
        ],
        'MinorityInterest': [
            'NetIncomeLossAttributableToNoncontrollingInterest', 'IncomeLossAttributableToNoncontrollingInterest',
            'NetIncomeLossIncludingPortionAttributableToNoncontrollingInterest',
            'IncomeLossFromContinuingOperationsAttributableToNoncontrollingInterest',
            'IncomeLossAttributableToNoncontrollingInterestAndParticipatingSecurities'
        ],
        'NetIncome': [
            'NetIncomeLoss', 'ProfitLoss', 'NetIncomeLossAvailableToCommonStockholdersBasic',
            'NetIncomeLossAttributableToParent', 'NetIncomeLossIncludingPortionAttributableToNoncontrollingInterest',
            'NetIncomeLossAvailableToCommonStockholdersDiluted', 'NetIncomeLossAttributableToControllingInterest'
        ]
    }
    
    BALANCE_SHEET_CONCEPTS = {
        # Current Assets
        'CashAndCashEquivalents': [
            'CashAndCashEquivalentsAtCarryingValue', 'CashCashEquivalentsAndShortTermInvestments',
            'Cash', 'CashAndCashEquivalents', 'CashCashEquivalentsAndRestrictedCash',
            'CashCashEquivalentsAndRestrictedCashRestrictedCash', 'CashAndShortTermInvestments'
        ],
        'MarketableSecuritiesCurrent': [
            'MarketableSecuritiesCurrent', 'ShortTermInvestments', 'AvailableForSaleSecuritiesCurrent',
            'ShortTermInvestmentsAvailableForSale', 'TradingSecuritiesCurrent', 'ShortTermInvestmentsAtCarryingValue'
        ],
        'AccountsReceivableNet': [
            'AccountsReceivableNetCurrent', 'AccountsReceivableNet', 'TradeAndOtherReceivablesNet',
            'AccountsReceivableNetOfAllowanceForDoubtfulAccounts', 'ReceivablesNetCurrent'
        ],
        'VendorNonTradeReceivables': [
            'NontradeReceivablesCurrent', 'VendorNonTradeReceivables', 'OtherReceivables', 
            'NonTradeReceivables', 'ReceivablesFromRelatedParties', 'OtherReceivablesCurrent'
        ],
        'Inventories': [
            'InventoryNet', 'Inventory', 'InventoriesNetOfReserves', 'InventoryAtLowerOfCostOrMarket',
            'InventoryFinishedGoods', 'InventoryRawMaterialsAndSupplies', 'InventoryWorkInProcess'
        ],
        'OtherCurrentAssets': [
            'OtherAssetsCurrent', 'OtherCurrentAssets', 'PrepaidExpensesCurrent',
            'DeferredCostsCurrent', 'AssetsCurrentOther'
        ],
        'TotalCurrentAssets': [
            'AssetsCurrent', 'CurrentAssets', 'TotalCurrentAssets',
            'AssetsCurrentExcludingOtherAssets', 'AssetsCurrentIncludingOtherAssets'
        ],
        # Non-Current Assets
        'MarketableSecuritiesNonCurrent': [
            'MarketableSecuritiesNoncurrent', 'AvailableForSaleSecuritiesNoncurrent',
            'LongTermInvestments', 'InvestmentsNoncurrent', 'SecuritiesNoncurrent'
        ],
        'PropertyPlantAndEquipmentNet': [
            'PropertyPlantAndEquipmentNet', 'PropertyPlantAndEquipment',
            'PropertyPlantAndEquipmentNetOfAccumulatedDepreciation', 'PropertyPlantAndEquipmentGross',
            'PropertyPlantAndEquipmentNetIncludingLeaseRightOfUseAsset',
            'PropertyPlantAndEquipmentNetExcludingLeaseRightOfUseAsset'
        ],
        'OtherNonCurrentAssets': [
            'OtherAssetsNoncurrent', 'OtherNoncurrentAssets', 'AssetsNoncurrent',
            'OtherAssets', 'AssetsNoncurrentExcludingOtherAssets',
            'IntangibleAssetsNetExcludingGoodwill', 'Goodwill'
        ],
        'TotalNonCurrentAssets': [
            'AssetsNoncurrent', 'NoncurrentAssets', 'TotalNoncurrentAssets',
            'AssetsNoncurrentExcludingOtherAssets', 'AssetsNoncurrentIncludingOtherAssets'
        ],
        'TotalAssets': [
            'Assets', 'AssetsTotal', 'TotalAssets',
            'AssetsIncludingOtherAssets', 'AssetsExcludingOtherAssets'
        ],
        # Current Liabilities
        'AccountsPayable': [
            'AccountsPayableCurrent', 'AccountsPayable', 'TradeAndOtherPayablesCurrent',
            'AccountsPayableTrade', 'PayablesCurrent'
        ],
        'OtherCurrentLiabilities': [
            'OtherLiabilitiesCurrent', 'OtherCurrentLiabilities', 'AccruedLiabilitiesCurrent',
            'AccruedLiabilities', 'LiabilitiesCurrentOther'
        ],
        'DeferredRevenue': [
            'ContractWithCustomerLiabilityCurrent', 'ContractWithCustomerLiability',
            'DeferredRevenueCurrent', 'DeferredRevenue', 'ContractWithCustomerAssetNet',
            'ContractWithCustomerLiabilityNet', 'UnearnedRevenueCurrent'
        ],
        'CommercialPaper': [
            'CommercialPaper', 'ShortTermDebt', 'ShortTermBorrowings',
            'DebtCurrent', 'CurrentMaturitiesOfLongTermDebt'
        ],
        'TermDebtCurrent': [
            'LongTermDebtCurrent', 'DebtCurrent', 'CurrentMaturitiesOfLongTermDebt',
            'LongTermDebtAndCapitalLeaseObligationsCurrent', 'ShortTermDebt'
        ],
        'TotalCurrentLiabilities': [
            'LiabilitiesCurrent', 'CurrentLiabilities', 'TotalCurrentLiabilities',
            'LiabilitiesCurrentExcludingOtherLiabilities'
        ],
        # Non-Current Liabilities
        'TermDebtNonCurrent': [
            'LongTermDebt', 'LongTermDebtAndCapitalLeaseObligations',
            'LongTermDebtExcludingCurrentMaturities', 'LongTermDebtNetOfCurrentMaturities',
            'LongTermDebtAndCapitalLeaseObligationsExcludingCurrentMaturities',
            'LongTermDebtIncludingCurrentMaturities'
        ],
        'OtherNonCurrentLiabilities': [
            'OtherLiabilitiesNoncurrent', 'OtherNoncurrentLiabilities', 'LiabilitiesNoncurrent',
            'OtherNoncurrentLiabilities', 'TotalNoncurrentLiabilities',
            'LiabilitiesNoncurrentExcludingOtherLiabilities', 'DeferredTaxLiabilitiesNoncurrent',
            'OperatingLeaseLiabilityNoncurrent', 'LeaseLiabilityNoncurrent'
        ],
        'TotalNonCurrentLiabilities': [
            'LiabilitiesNoncurrent', 'TotalNoncurrentLiabilities',
            'LiabilitiesNoncurrentExcludingOtherLiabilities'
        ],
        'TotalLiabilities': [
            'Liabilities', 'LiabilitiesTotal', 'TotalLiabilities',
            'LiabilitiesIncludingOtherLiabilities', 'LiabilitiesExcludingOtherLiabilities'
        ],
        # Shareholders' Equity
        'CommonStockAndPaidInCapital': [
            'CommonStocksIncludingAdditionalPaidInCapital', 'CommonStockAndAdditionalPaidInCapital',
            'AdditionalPaidInCapital', 'CommonStockValue', 'PaidInCapital',
            'AdditionalPaidInCapitalCommonStock'
        ],
        'AccumulatedDeficit': [
            'RetainedEarningsAccumulatedDeficit', 'AccumulatedDeficit', 'RetainedEarnings',
            'RetainedEarningsAppropriated', 'RetainedEarningsUnappropriated'
        ],
        'AccumulatedOtherComprehensiveLoss': [
            'AccumulatedOtherComprehensiveIncomeLossNetOfTax', 'AccumulatedOtherComprehensiveIncomeLoss',
            'AccumulatedOtherComprehensiveIncome', 'OtherComprehensiveIncomeLossNetOfTax'
        ],
        'TotalShareholdersEquity': [
            'StockholdersEquity', 'Equity', 'EquityAttributableToParent',
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
    
    def _determine_fiscal_year_end_pattern(self, facts: Dict) -> Optional[Dict]:
        """
        Determine the company's fiscal year end pattern by looking at recent annual data.
        Returns a dict mapping calendar year to fiscal year end date (YYYY-MM-DD).
        """
        if 'facts' not in facts:
            return None
        
        facts_data = facts['facts']
        us_gaap = facts_data.get('us-gaap', {})
        
        # Look for a common concept that should have recent annual data (e.g., Revenue, OperatingIncome)
        test_concepts = ['Revenues', 'OperatingIncomeLoss', 'NetIncomeLoss', 'Assets']
        fiscal_year_ends = {}  # Maps calendar year -> fiscal year end date
        
        for concept_name in test_concepts:
            if concept_name not in us_gaap:
                continue
            
            concept_data = us_gaap[concept_name]
            if 'units' not in concept_data:
                continue
            
            # Get USD units
            units = concept_data['units']
            unit_to_use = None
            for pref_unit in ['USD', 'usd']:
                if pref_unit in units:
                    unit_to_use = pref_unit
                    break
            
            if not unit_to_use and units:
                unit_to_use = list(units.keys())[0]
            
            if unit_to_use and unit_to_use in units:
                data_list = units[unit_to_use]
                
                # Find annual periods (spanning ~330-400 days)
                for item in data_list:
                    end_date = item.get('end', '')
                    start_date = item.get('start', '')
                    
                    if end_date and len(end_date) >= 10:
                        try:
                            from datetime import datetime
                            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                            calendar_year = end_dt.year
                            
                            # Check if this is an annual period - MUST span approximately a full year
                            is_annual = False
                            if start_date and len(start_date) >= 10:
                                try:
                                    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                                    days_diff = (end_dt - start_dt).days
                                    # Annual periods are typically 330-400 days (accounting for leap years)
                                    if 330 <= days_diff <= 400:
                                        is_annual = True
                                except:
                                    pass
                            
                            # Only use periods that actually span a full year (don't use quarterly/interim periods)
                            if is_annual:
                                # Only consider recent years (2020 and later) to determine pattern
                                if calendar_year >= 2020:
                                    # Store the fiscal year end date for this calendar year
                                    # Prefer September/October dates (common fiscal year ends)
                                    # If multiple annual periods exist for a year, prefer the one in Sep/Oct
                                    if calendar_year not in fiscal_year_ends:
                                        fiscal_year_ends[calendar_year] = end_date
                                    else:
                                        # Prefer Sep/Oct dates over Dec dates (Dec might be calendar year, not fiscal)
                                        existing_month = datetime.strptime(fiscal_year_ends[calendar_year], '%Y-%m-%d').month
                                        new_month = end_dt.month
                                        if new_month in [9, 10] and existing_month not in [9, 10]:
                                            fiscal_year_ends[calendar_year] = end_date
                                        elif new_month == existing_month and end_date > fiscal_year_ends[calendar_year]:
                                            # Same month, use more recent date
                                            fiscal_year_ends[calendar_year] = end_date
                        except:
                            pass
                
                # If we found fiscal year ends, return the pattern
                if fiscal_year_ends:
                    return fiscal_year_ends
        
        return None
    
    def extract_historical_data(self, facts: Dict, concept_list: List[str],
                               namespace: str = 'us-gaap', years: int = 5,
                               fiscal_year_ends: Optional[Dict] = None) -> Dict[str, float]:
        """Extract historical values for a concept over multiple years"""
        if 'facts' not in facts:
            return {}
        
        facts_data = facts['facts']
        
        # Determine fiscal year end pattern for consistency (cache it to avoid recalculating)
        if fiscal_year_ends is None:
            fiscal_year_ends = self._determine_fiscal_year_end_pattern(facts)
            if fiscal_year_ends:
                print(f"DEBUG: Determined fiscal year end pattern: {fiscal_year_ends}")
        
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
                            
                            # Filter for annual data: ONLY use periods that span a full year (330-400 days)
                            # OR point-in-time data (balance sheets) that match fiscal year end dates
                            # This ensures we only get 10-K annual data, never quarterly data
                            annual_data = []
                            for item in data_list:
                                end_date = item.get('end', '')
                                start_date = item.get('start', '')
                                form = item.get('form', '')
                                
                                if end_date and len(end_date) >= 10:
                                    try:
                                        from datetime import datetime
                                        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                                        calendar_year = end_dt.year
                                        
                                        # Check if this is a period (has start_date) or point-in-time (no start_date)
                                        is_period = start_date and len(start_date) >= 10
                                        is_point_in_time = not is_period
                                        
                                        if is_period:
                                            # Period data: must span approximately a full year (330-400 days)
                                            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                                            days_diff = (end_dt - start_dt).days
                                            
                                            # STRICT: Only include periods that span approximately a full year (330-400 days)
                                            # This ensures we only get annual 10-K data, never quarterly (which would be ~90 days)
                                            if 330 <= days_diff <= 400:
                                                # If we have a fiscal year end pattern, prefer exact match but also accept annual data from same calendar year
                                                if fiscal_year_ends and calendar_year in fiscal_year_ends:
                                                    expected_date = fiscal_year_ends[calendar_year]
                                                    if end_date == expected_date:
                                                        # Exact match - highest priority
                                                        annual_data.append(item)
                                                    # Also accept annual data from the same calendar year if it's a full year period
                                                    # This handles cases where a concept might have slightly different fiscal year ends
                                                    elif end_dt.month in [9, 10, 11, 12]:
                                                        # It's a full year period ending in a common fiscal year end month
                                                        annual_data.append(item)
                                                elif not fiscal_year_ends:
                                                    # No pattern available, use any full-year period
                                                    annual_data.append(item)
                                        elif is_point_in_time:
                                            # Point-in-time data (balance sheets): must match fiscal year end pattern
                                            # Only accept if it matches the fiscal year end date for that year
                                            if fiscal_year_ends and calendar_year in fiscal_year_ends:
                                                expected_date = fiscal_year_ends[calendar_year]
                                                if end_date == expected_date:
                                                    # Exact match to fiscal year end - this is annual balance sheet data
                                                    annual_data.append(item)
                                                # Also accept if it's in a common fiscal year end month (Sep/Oct/Nov/Dec)
                                                # and the form is 10-K (not 10-Q)
                                                elif end_dt.month in [9, 10, 11, 12] and form == '10-K':
                                                    annual_data.append(item)
                                            elif not fiscal_year_ends:
                                                # No pattern available, but accept point-in-time data if form is 10-K and in common fiscal year end months
                                                if form == '10-K' and end_dt.month in [9, 10, 11, 12]:
                                                    annual_data.append(item)
                                    except:
                                        # Skip items that can't be parsed
                                        pass
                            
                            # If no annual data found, don't fall back to quarterly data
                            # We only want 10-K annual data, so if we can't find it, return empty
                            
                            # Sort by end date (most recent first)
                            annual_data.sort(key=lambda x: x.get('end', ''), reverse=True)
                            
                            # Group by year, prioritizing values that match the fiscal year end pattern exactly
                            years_seen = set()
                            year_data = {}  # Store all candidates for each year, then pick best
                            
                            for item in annual_data:
                                end_date = item.get('end', '')
                                if end_date and len(end_date) >= 4:
                                    year = end_date[:4]
                                    val = float(item.get('val', 0))
                                    
                                    # Handle unit conversion if needed (some are in thousands)
                                    # Check if unit indicates thousands
                                    if 'thousand' in unit_to_use.lower() or 'thousands' in unit_to_use.lower():
                                        val = val * 1000
                                    
                                    # Store candidate for this year
                                    if year not in year_data:
                                        year_data[year] = []
                                    year_data[year].append({
                                        'val': val,
                                        'date': end_date,
                                        'matches_pattern': (fiscal_year_ends and year in fiscal_year_ends and 
                                                          end_date == fiscal_year_ends[year])
                                    })
                            
                            # For each year, pick the best candidate (prefer exact fiscal year match)
                            for year, candidates in sorted(year_data.items(), key=lambda x: x[0], reverse=True):
                                if year not in years_seen:
                                    # Sort candidates: exact pattern match first, then by date (most recent)
                                    candidates.sort(key=lambda x: (not x['matches_pattern'], x['date']), reverse=True)
                                    best = candidates[0]
                                    
                                    # Debug: print first extraction for each concept
                                    if not result:
                                        print(f"DEBUG: Extracted {concept_name} for year {year}: {best['val']} (unit: {unit_to_use}, date: {best['date']}, matches_pattern: {best['matches_pattern']})")
                                    
                                    result[year] = best['val']
                                    result[f'{year}_date'] = best['date']
                                    years_seen.add(year)
                                    
                                    # Limit to most recent N years
                                    if len(years_seen) >= years:
                                        break
                    
                    # Prioritize concepts that have data for the most recent years (2023, 2024, 2025)
                    # Don't use concepts that only have old data or are missing recent years
                    if result:
                        years_found = [y for y in result.keys() if not y.endswith('_date') and y.isdigit()]
                        if years_found:
                            sorted_years = sorted([int(y) for y in years_found], reverse=True)
                            # We need at least the 5 most recent years, and they should be recent (2020+)
                            if len(sorted_years) >= 5 and sorted_years[0] >= 2023:
                                # Check if we have the 5 most recent years (should be 2021, 2022, 2023, 2024, 2025)
                                required_years = sorted_years[:5]
                                if all(y >= 2020 for y in required_years):
                                    # This concept has good recent data covering the years we need, use it
                                    break
                            elif len(sorted_years) >= 1 and sorted_years[0] >= 2020:
                                # Has some recent data but not enough years - continue looking for better concept
                                # Only use this if we've tried all concepts and this is the best we have
                                pass
                        # This concept doesn't have enough recent data, continue looking
                        # Don't clear result yet - we'll use it as fallback if nothing better is found
                        if not years_found or (years_found and sorted([int(y) for y in years_found], reverse=True)[0] < 2020):
                            result = {}
            
            # If we found data in this namespace, break
            if result:
                break
        
        return result
    
    def parse_income_statement(self, facts: Dict) -> pd.DataFrame:
        """Parse Income Statement data from XBRL facts"""
        income_data = {}
        
        # Determine fiscal year end pattern once and reuse it for all concepts
        fiscal_year_ends = self._determine_fiscal_year_end_pattern(facts)
        if fiscal_year_ends:
            print(f"DEBUG: Determined fiscal year end pattern: {fiscal_year_ends}")
        
        # Extract last 10 years of data to ensure we have enough, then filter to 3 most recent
        for key, concept_list in self.INCOME_STATEMENT_CONCEPTS.items():
            historical = self.extract_historical_data(facts, concept_list, years=10, fiscal_year_ends=fiscal_year_ends)
            income_data[key] = historical
            # Debug: print what we found with dates
            if historical:
                years_found = [k for k in historical.keys() if not k.endswith('_date')]
                dates_found = [historical.get(f'{k}_date', 'N/A') for k in sorted(years_found, reverse=True)[:3]]
                print(f"DEBUG: Found {key} for years: {sorted(years_found, reverse=True)[:3]} with dates: {dates_found}")
            else:
                print(f"DEBUG: No data found for {key} (tried {len(concept_list)} concepts)")
        
        # SPECIAL HANDLING FOR REVENUE: Check if revenue exists for the years we need
        # Get the years we're actually going to display
        years = set()
        for key, values in income_data.items():
            years.update([k for k in values.keys() if not k.endswith('_date')])
        
        if years:
            sorted_years = sorted([int(y) for y in years if y.isdigit()], reverse=True)
            recent_years = sorted_years[:5]  # The 5 most recent years we'll display
            
            # Check if revenue exists for these recent years
            revenue_data = income_data.get('Revenue', {})
            revenue_missing_for_recent = False
            for year in recent_years:
                year_str = str(year)
                if year_str not in revenue_data or revenue_data.get(year_str, 0) == 0:
                    revenue_missing_for_recent = True
                    break
            
            # If revenue is missing for recent years, try aggregation
            if revenue_missing_for_recent:
                print(f"DEBUG: Revenue is zero or missing for recent years {recent_years}, attempting to aggregate from multiple revenue sources...")
                revenue_aggregate = self._aggregate_revenue_from_multiple_sources(facts)
                if revenue_aggregate:
                    print(f"DEBUG: Successfully aggregated revenue: {list(revenue_aggregate.keys())}")
                    # Merge aggregated revenue with existing (prioritize aggregated for recent years)
                    for year_str, value in revenue_aggregate.items():
                        if not year_str.endswith('_date'):
                            income_data['Revenue'][year_str] = value
                else:
                    print("WARNING: Could not aggregate revenue from any sources")
        
        # Convert to DataFrame
        years = set()
        for key, values in income_data.items():
            years.update([k for k in values.keys() if not k.endswith('_date')])
        
        if not years:
            print("DEBUG: No years found in income statement data")
            return pd.DataFrame()
        
        # Sort years and take only the most recent 5 years
        sorted_years = sorted([int(y) for y in years if y.isdigit()], reverse=True)
        recent_years = sorted_years[:5]  # Only 5 most recent years
        
        df_data = {}
        for year in recent_years:
            year_str = str(year)
            row = {}
            for key in self.INCOME_STATEMENT_CONCEPTS.keys():
                value = income_data.get(key, {}).get(year_str, 0)
                row[key] = value
                # Debug: warn if Revenue is zero
                if key == 'Revenue' and value == 0:
                    print(f"WARNING: Revenue is 0 for year {year_str}")
                    print(f"  Income data for Revenue: {income_data.get(key, {})}")
            df_data[year_str] = row
        
        # Debug: print sample of what we're creating
        if df_data:
            sample_year = list(df_data.keys())[0]
            print(f"DEBUG: Sample row for year {sample_year}: Revenue={df_data[sample_year].get('Revenue', 'N/A')}")
        
        # Return with years in ascending order (oldest to newest)
        return pd.DataFrame(df_data).T.sort_index()
    
    def _aggregate_revenue_from_multiple_sources(self, facts: Dict) -> Dict[str, float]:
        """
        Try to aggregate revenue from multiple XBRL concepts if direct revenue extraction failed.
        Prioritizes "Total" revenue concepts first, then falls back to individual components.
        """
        if 'facts' not in facts:
            return {}
        
        facts_data = facts['facts']
        
        # Prioritize total/aggregate revenue concepts first
        priority_concepts = [
            'Revenues',  # Most common
            'TotalRevenue',
            'RevenueFromContractWithCustomerIncludingAssessedTax',
            'RevenueFromContractWithCustomerExcludingAssessedTax',
            'RevenueFromContractWithCustomer',
            'NetSales',
            'SalesAndOtherOperatingRevenue',
            'SalesRevenueNet',
            'RevenuesNetOfInterestExpense'
        ]
        
        # Fallback to component revenue concepts
        fallback_concepts = [
            'SalesRevenueGoodsNet',
            'SalesRevenueServicesNet',
            'ProductRevenueNet',
            'ServiceRevenueNet',
            'SalesRevenueServicesAndOther'
        ]
        
        # Try all namespaces
        namespaces_to_try = ['us-gaap', 'ifrs-full', 'dei']
        
        aggregated_revenue = {}
        
        # First, try priority concepts (these are usually total revenue)
        for ns in namespaces_to_try:
            if ns not in facts_data:
                continue
            
            namespace_facts = facts_data[ns]
            
            for concept_name in priority_concepts:
                if concept_name not in namespace_facts:
                    continue
                
                revenue_data = self._extract_revenue_from_concept(namespace_facts[concept_name])
                if revenue_data:
                    # Check if we have recent data (2020 or later)
                    recent_years = [y for y in revenue_data.keys() if not y.endswith('_date') and int(y) >= 2020]
                    if recent_years:
                        aggregated_revenue = revenue_data
                        print(f"DEBUG: Found revenue using priority concept '{concept_name}' from namespace '{ns}'")
                        print(f"DEBUG: Revenue years found: {sorted([y for y in aggregated_revenue.keys() if not y.endswith('_date')], reverse=True)[:5]}")
                        return aggregated_revenue
                    else:
                        print(f"DEBUG: Concept '{concept_name}' found but only has old data: {sorted([y for y in revenue_data.keys() if not y.endswith('_date')], reverse=True)[:3]}")
        
        # If priority concepts didn't work, try fallback concepts and sum them
        print("DEBUG: Priority revenue concepts not found, trying to aggregate from component concepts...")
        component_revenue_by_year = {}
        
        for ns in namespaces_to_try:
            if ns not in facts_data:
                continue
            
            namespace_facts = facts_data[ns]
            
            for concept_name in fallback_concepts:
                if concept_name not in namespace_facts:
                    continue
                
                revenue_data = self._extract_revenue_from_concept(namespace_facts[concept_name])
                if revenue_data:
                    # Sum component revenues by year
                    for year, value in revenue_data.items():
                        if not year.endswith('_date'):
                            if year in component_revenue_by_year:
                                component_revenue_by_year[year] += value
                            else:
                                component_revenue_by_year[year] = value
        
        if component_revenue_by_year:
            print(f"DEBUG: Aggregated revenue from {len(fallback_concepts)} component concepts")
            print(f"DEBUG: Revenue years found: {sorted(component_revenue_by_year.keys(), reverse=True)[:3]}")
            return component_revenue_by_year
        
        return {}
    
    def _extract_revenue_from_concept(self, concept_data: Dict) -> Dict[str, float]:
        """Extract revenue values from a single XBRL concept"""
        if 'units' not in concept_data:
            return {}
        
        units = concept_data['units']
        unit_to_use = None
        
        # Prefer USD units
        for pref_unit in ['USD', 'usd']:
            if pref_unit in units:
                unit_to_use = pref_unit
                break
        
        if not unit_to_use and units:
            unit_to_use = list(units.keys())[0]
        
        if not unit_to_use or unit_to_use not in units:
            return {}
        
        data_list = units[unit_to_use]
        revenue_by_year = {}
        
        # Get annual data - prioritize recent years
        annual_items = []
        for item in data_list:
            end_date = item.get('end', '')
            if end_date and len(end_date) >= 4:
                start_date = item.get('start', '')
                # Check if this is annual data (ends in -12-31 or spans full year)
                is_annual = (end_date.endswith('-12-31') or 
                           (start_date and len(start_date) >= 4 and end_date[:4] != start_date[:4]))
                if is_annual:
                    annual_items.append(item)
        
        # Sort by end date (most recent first)
        annual_items.sort(key=lambda x: x.get('end', ''), reverse=True)
        
        # Extract values, prioritizing most recent
        for item in annual_items:
            end_date = item.get('end', '')
            if end_date and len(end_date) >= 4:
                year = end_date[:4]
                val = float(item.get('val', 0))
                
                # Handle unit conversion (thousands to actual)
                if 'thousand' in unit_to_use.lower():
                    val = val * 1000
                
                # Take the most recent value if multiple exist for same year
                if year not in revenue_by_year or val > revenue_by_year[year]:
                    revenue_by_year[year] = val
        
        return revenue_by_year
    
    def parse_balance_sheet(self, facts: Dict, fiscal_year_ends: Optional[Dict] = None) -> pd.DataFrame:
        """Parse Balance Sheet data from XBRL facts"""
        balance_data = {}
        
        # Extract last 10 years of data to ensure we have enough, then filter to 5 most recent
        for key, concept_list in self.BALANCE_SHEET_CONCEPTS.items():
            historical = self.extract_historical_data(facts, concept_list, years=10, fiscal_year_ends=fiscal_year_ends)
            balance_data[key] = historical
            # Debug: print what we found
            if historical:
                years_found = [k for k in historical.keys() if not k.endswith('_date')]
                print(f"DEBUG: Found {key} for years: {sorted(years_found, reverse=True)[:5]}")
            else:
                print(f"DEBUG: No data found for {key} (tried {len(concept_list)} concepts)")
        
        # Convert to DataFrame
        years = set()
        for key, values in balance_data.items():
            years.update([k for k in values.keys() if not k.endswith('_date')])
        
        if not years:
            return pd.DataFrame()
        
        # Sort years and take only the most recent 5 years
        sorted_years = sorted([int(y) for y in years if y.isdigit()], reverse=True)
        recent_years = sorted_years[:5]  # Only 5 most recent years
        
        df_data = {}
        for year in recent_years:
            year_str = str(year)
            row = {}
            for key in self.BALANCE_SHEET_CONCEPTS.keys():
                row[key] = balance_data.get(key, {}).get(year_str, 0)
            df_data[year_str] = row
        
        return pd.DataFrame(df_data).T.sort_index()
    
    def parse_cash_flow(self, facts: Dict, fiscal_year_ends: Optional[Dict] = None) -> pd.DataFrame:
        """Parse Cash Flow Statement data from XBRL facts"""
        cashflow_data = {}
        
        # Extract last 10 years of data to ensure we have enough, then filter to 3 most recent
        for key, concept_list in self.CASH_FLOW_CONCEPTS.items():
            historical = self.extract_historical_data(facts, concept_list, years=10, fiscal_year_ends=fiscal_year_ends)
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
        
        # Sort years and take only the most recent 5 years
        sorted_years = sorted([int(y) for y in years if y.isdigit()], reverse=True)
        recent_years = sorted_years[:5]  # Only 5 most recent years
        
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
        # Determine fiscal year end pattern once and reuse for all statements
        fiscal_year_ends = self._determine_fiscal_year_end_pattern(facts)
        if fiscal_year_ends:
            print(f"DEBUG: Determined fiscal year end pattern: {fiscal_year_ends}")
        
        income_statement = self.parse_income_statement(facts)
        balance_sheet = self.parse_balance_sheet(facts, fiscal_year_ends=fiscal_year_ends)
        cash_flow = self.parse_cash_flow(facts, fiscal_year_ends=fiscal_year_ends)
        
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

