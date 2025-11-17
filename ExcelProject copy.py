import xlsxwriter

currentYear = 2025
companyName = "Apple"

#current
revenue = [2644, 3892, 4049]
ebit    = [209, 484, 505]
DACurrent = [132, 195, 202]
SBCCurrent = [13,19,20]
changeNWC = [80, 120, 120]
capEx = [63, 115, 120]

#assumptions
RevenueGrowthRateAssumptions = [0.05, 0.05, 0.05, 0.05, 0.05]
EBITMarginAssumptions = [0.125, 0.125, 0.125, 0.125, 0.125]
taxRate = 0.4
DARate = [0.05, 0.05, 0.05, 0.05, 0.05]
SBCRate = [0.005, 0.005, 0.005, 0.005, 0.005]
changeNWCAssumption = [0.03, 0.03, 0.03, 0.03, 0.03]
capExAssumption = [0.025, 0.025, 0.025, 0.025, 0.025]

#helper functions
#percentofRevenue
def percentRevenue(ws, rowRev, colStart, rates, outRow, fmt):
    for i, rate in enumerate(rates):
        c = colStart + i                
        rev_cell = xlsxwriter.utility.xl_rowcol_to_cell(rowRev, c)
        ws.write_formula(outRow, c, f"={rev_cell}*{rate}", fmt)

#printHistorical
def printHistorical(ws, outRow, values, colStart, fmt):
    for i, val in enumerate(values):
        ws.write_number(outRow, colStart + i, val, fmt)

#Write a blank row
def blankRow(ws, row, cols, fmt):
    for c in range(cols):
        ws.write(row, c, "", fmt)


years = [
    ("Historical", "Year 1A"),
    ("Historical", "Year 2A"),
    ("Historical", "Year 3A"),
    ("Projected",  "Year 1E"),
    ("Projected",  "Year 2E"),
    ("Projected",  "Year 3E"),
    ("Projected",  "Year 4E"),
    ("Projected",  "Year 5E")
]


revenue = [2644, 3892, 4049]
ebit    = [209, 484, 505]

#Create Workbook
wb = xlsxwriter.Workbook(f"{companyName}Projections.xlsx")
ws = wb.add_worksheet("Assumptions")

#Set Column width
ws.set_column("A:A", 30)
ws.set_column("B:I", 15)

#formats
blue = wb.add_format({"bold": True, "font_color": "white", "align":"center", "valign":"vcenter","bg_color":"#274A78","border":0})
lightBlueHdr = wb.add_format({"bold": True, "font_color": "white", "align":"left", "valign":"vcenter","bg_color":"#5476A7","border":0})
blueLeft = wb.add_format({"bold": True, "font_color": "white", "align":"left", "valign":"vcenter","bg_color":"#274A78","border":0})
lightBlueMoney = wb.add_format({"bold": True, "font_color": "white", "align":"right", "valign":"vcenter","bg_color":"#5476A7", 'num_format':'#,##0;(#,##0)', "border":0})
italic = wb.add_format({"italic":True, "align":"left","border":0,"indent":2, "bg_color": "white"})
money = wb.add_format({'num_format': '#,##0.0;(#,##0.0)', "align": "right", "border": 1, "bg_color": "white"})
pct1 = wb.add_format({'num_format':'0.0%', "border":0, "bg_color": "white"})
subHdr  = wb.add_format({"bold":True,"align":"center","valign":"vcenter","bg_color":"#E6EEF7","border":0, "bg_color": "white"})
rowHdr  = wb.add_format({"bold":True,"align":"left","valign":"vcenter","border":0,"indent":1, "bg_color": "white"})
blank    = wb.add_format({"border":0, "bg_color": "white"})
topline = wb.add_format({"top": 1, "bg_color": "white"})

#Header
ws.merge_range(0,0,0,8, "Free Cash Flow", blueLeft)
ws.write(1,0, "", blue)
ws.merge_range(1, 1, 1, 3, "Historical", blue)  # B2:D2
ws.merge_range(1, 4, 1, 8, "Projected",  blue)  # E2:I2

#Years
ws.write(2,0,"",subHdr)
for c, (_, label) in enumerate(years, start=1):
    ws.write(2, c, label, subHdr)

#Historical Revenue
ws.write(3, 0, "Revenue:", rowHdr)
printHistorical(ws, 3, revenue, 1, money)

ws.write(4, 0, "Revenue Growth Rate:", italic)
ws.write(4,1, "", blank)

#Calculated Revenue with Growth Rate Assumptions
baseRev = 3
for i, rate in enumerate(RevenueGrowthRateAssumptions):
    c = baseRev + (i + 1)
    prevRev = xlsxwriter.utility.xl_rowcol_to_cell(3, c-1)
    newRev = f"={prevRev}*(1+{rate})"
    ws.write_formula(3, c, newRev, money)


#Revenue Growth
for c in range(2, 9):
    rev = xlsxwriter.utility.xl_rowcol_to_cell(3,c)
    prevRev = xlsxwriter.utility.xl_rowcol_to_cell(3, c-1)
    ws.write_formula(4, c, f"={rev}/{prevRev}-1", pct1)


#Historical EBIT
ws.write(5,0, "EBIT:", rowHdr)
printHistorical(ws, 5, ebit, 1, money)

#New EBIT calculated with EBIT margin assumptions
baseEBIT = 3
for i, margin in enumerate(EBITMarginAssumptions):
    c = baseEBIT + (i + 1)
    Rev = xlsxwriter.utility.xl_rowcol_to_cell(3, c)
    calcEBIT = f"={Rev}*{margin}"
    ws.write_formula(5, c, calcEBIT, money)

#Write out EBIT Margin
ws.write(6,0, "EBIT Margin:", italic)
for c in range(1,9):
    EBIT = xlsxwriter.utility.xl_rowcol_to_cell(5,c)
    Rev = xlsxwriter.utility.xl_rowcol_to_cell(3,c)
    ws.write_formula(6, c, f"={EBIT}/{Rev}", pct1)

#Write out Taxes
ws.write(7,0, "Tax Expense:", rowHdr)
for c in range(1,9):
    EBIT = xlsxwriter.utility.xl_rowcol_to_cell(5,c)
    taxes = f"={taxRate}*{EBIT}"
    ws.write_formula(7,c, taxes, money)

#NOPAT
ws.write(8,0, "NOPAT:", rowHdr)
for c in range(1,9):
    EBIT = xlsxwriter.utility.xl_rowcol_to_cell(5,c)
    taxes = xlsxwriter.utility.xl_rowcol_to_cell(7,c)
    ws.write_formula(8,c, f"={EBIT}-{taxes}", money)

#D&A
blankRow(ws, 9, 9, blank)
ws.write(10, 0, "D&A:", rowHdr)
printHistorical(ws, 10, DACurrent, 1, money)                 
percentRevenue(ws, 3, 4, DARate, 10, money)

#SBC
ws.write(11, 0, "SBC:", rowHdr)
printHistorical(ws, 11, SBCCurrent, 1, money)                
percentRevenue(ws, 3, 4, SBCRate, 11, money)

#Change in NWC 
blankRow(ws, 12, 9, blank)
ws.write(13, 0, "Change in NWC:", rowHdr)
printHistorical(ws, 13, changeNWC, 1, money)                  
percentRevenue(ws, 3, 4, changeNWCAssumption, 13, money)

#CapEx
ws.write(14, 0, "CapEx:", rowHdr)
printHistorical(ws, 14, [-x for x in capEx], 1, money)
percentRevenue(ws, 3, 4, [-r for r in capExAssumption], 14, money)

#FCF
ws.write(16,0, "Unlevered Free Cash Flow:", lightBlueHdr)
for c in range (1,9):
    NOPAT = xlsxwriter.utility.xl_rowcol_to_cell(8,c)
    DA = xlsxwriter.utility.xl_rowcol_to_cell(10,c)
    SBC = xlsxwriter.utility.xl_rowcol_to_cell(11,c)
    changeNWC = xlsxwriter.utility.xl_rowcol_to_cell(13,c)
    capEx = xlsxwriter.utility.xl_rowcol_to_cell(14,c)
    formula = f"={NOPAT} + {DA} + {SBC} - {changeNWC} - {capEx}"
    ws.write_formula(16, c, formula, lightBlueMoney)

wb.close()












