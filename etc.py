import pandas as pd

df = pd.read_excel("flipkart_products_all_pages.xlsx")
df.to_csv("flipkart_products_all_pages.csv", index=False)

print("Converted XLSX to CSV successfully")
