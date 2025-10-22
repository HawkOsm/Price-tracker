import xlsxwriter

products = xlsxwriter.Workbook("products.xlsx")
product_sheet = products.add_worksheet()


def excel(name,url,row,col):

    product_sheet.write('A1', 'Item')
    product_sheet.write('B1', 'URL')
    product_sheet.write('C1', 'Price')

    product_sheet.write(row,col,name)
    product_sheet.write(row,col+1,url)
    row+=1


