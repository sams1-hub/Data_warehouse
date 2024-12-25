import pandas as pd
import matplotlib.pyplot as plt
from openpyxl import load_workbook

# Function to load the Excel file and display sheet names
def load_excel(file_path):
    xls = pd.ExcelFile(file_path)
    print(f"Sheets available: {xls.sheet_names}")
    return xls

# Function to display the first few rows of a selected sheet
def display_sheet_data(xls, sheet_name, rows=10):
    df = pd.read_excel(xls, sheet_name=sheet_name)
    print(f"Displaying first {rows} rows of {sheet_name} sheet:")
    print(df.head(rows))

    return df

# Function to visualize data
def visualize_data(df, column_x, column_y, title="Data Visualization", kind='line'):
    plt.figure(figsize=(10, 6))
    if kind == 'line':
        df.plot(x=column_x, y=column_y, kind='line', title=title)
    elif kind == 'bar':
        df.plot(x=column_x, y=column_y, kind='bar', title=title)
    elif kind == 'scatter':
        df.plot(x=column_x, y=column_y, kind='scatter', title=title)
    else:
        print("Unsupported plot kind. Use 'line', 'bar', or 'scatter'.")
        return

    plt.xlabel(column_x)
    plt.ylabel(column_y)
    plt.show()

# Function to visualize data for a single sheet
def visualize_single_sheet(file_path, sheet_name, rows=10, column_x=None, column_y=None, plot_kind='line'):
    # Load the Excel file
    xls = load_excel(file_path)

    # Display the data from the selected sheet
    df = display_sheet_data(xls, sheet_name, rows)

    # If no column names are provided, attempt to use the first two columns
    if column_x is None or column_y is None:
        column_x = df.columns[0]  # Use the first column as the x-axis
        column_y = df.columns[1]  # Use the second column as the y-axis

    # Visualize the data with the chosen columns
    visualize_data(df, column_x, column_y, title=f"{sheet_name} Data Visualization", kind=plot_kind)

# Main function to handle file input and visualization options
def main():
    file_path = input("Enter the path to your Excel file: ")
    
    # Check if the file exists
    try:
        xls = load_excel(file_path)
    except FileNotFoundError:
        print(f"File '{file_path}' not found. Please check the path and try again.")
        return

    # Ask the user which sheet to visualize
    sheet_name = input(f"Enter the sheet name to visualize (available sheets: {', '.join(xls.sheet_names)}): ")

    # Check if the sheet exists in the Excel file
    if sheet_name not in xls.sheet_names:
        print(f"Sheet '{sheet_name}' not found in the file. Please choose a valid sheet name.")
        return

    # Ask the user for the number of rows to display
    try:
        rows = int(input("Enter the number of rows to display (default is 10): ") or 10)
    except ValueError:
        print("Invalid input. Defaulting to 10 rows.")
        rows = 10

    # Ask the user for column names to visualize
    print("Available columns:", ", ".join(xls.parse(sheet_name).columns))
    column_x = input(f"Enter the column name for the X-axis (default is the first column): ") or None
    column_y = input(f"Enter the column name for the Y-axis (default is the second column): ") or None
    
    # Ask the user for the plot type
    plot_kind = input("Enter the plot kind (options: 'line', 'bar', 'scatter', default is 'line'): ") or 'line'

    # Visualize the selected sheet data
    visualize_single_sheet(file_path, sheet_name, rows, column_x, column_y, plot_kind)

if __name__ == "__main__":
    main()
