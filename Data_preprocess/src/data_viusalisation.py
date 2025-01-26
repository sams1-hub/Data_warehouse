import pandas as pd
import matplotlib.pyplot as plt
from tkinter import Tk, filedialog, messagebox, Button, Label, StringVar, OptionMenu, Frame
import os

def select_file():
    root = Tk()
    root.withdraw()
    return filedialog.askopenfilename(
        title="Select a file",
        filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xls *.xlsx"), ("All files", "*.*")]
    )

def load_file(file_path):
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
            print(f"Loaded CSV file: {file_path}")
        elif file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
            print(f"Loaded Excel file: {file_path}")
        else:
            raise ValueError("Unsupported file format. Use CSV or Excel files.")
        
        print(f"Available columns: {', '.join(df.columns)}")
        display_data(df)
        return df
    except Exception as e:
        messagebox.showerror("Error", str(e))
        return None

def display_data(df, rows=10):
    print(f"\nDisplaying first {rows} rows of data:")
    print(df.head(rows))

def visualize_data(df, column_x=None, column_y=None, plot_kind='histogram'):
    plt.figure(figsize=(10, 6))
    
    try:
        if plot_kind == 'line':
            if column_x and column_y:
                plt.plot(df[column_x], df[column_y], marker='o')
                plt.title(f"Line Plot: {column_x} vs {column_y}")
            else:
                messagebox.showerror("Error", "Both X and Y columns are required for a line plot.")
                return
        elif plot_kind == 'bar':
            if column_x and column_y:
                plt.bar(df[column_x], df[column_y])
                plt.title(f"Bar Plot: {column_x} vs {column_y}")
            else:
                messagebox.showerror("Error", "Both X and Y columns are required for a bar plot.")
                return
        elif plot_kind == 'scatter':
            if column_x and column_y:
                plt.scatter(df[column_x], df[column_y])
                plt.title(f"Scatter Plot: {column_x} vs {column_y}")
            else:
                messagebox.showerror("Error", "Both X and Y columns are required for a scatter plot.")
                return
        elif plot_kind == 'histogram':
            if column_x:
                plt.hist(df[column_x], bins=10, edgecolor='black')
                plt.title(f"Histogram: {column_x}")
            else:
                messagebox.showerror("Error", "X column is required for a histogram.")
                return
        elif plot_kind == 'boxplot':
            if column_x:
                plt.boxplot(df[column_x])
                plt.title(f"Boxplot: {column_x}")
            else:
                messagebox.showerror("Error", "X column is required for a boxplot.")
                return
        
        plt.xlabel(column_x if column_x else '')
        if column_y:
            plt.ylabel(column_y)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    except Exception as e:
        messagebox.showerror("Error", str(e))

def create_visualization_window(df):
    root = Tk()
    root.title("Data Visualization")
    root.geometry("400x350")

    Label(root, text="Select columns and plot type:", font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)

    # Column selection
    Label(root, text="X-axis column:").grid(row=1, column=0)
    x_var = StringVar(root)
    x_var.set(df.columns[0])
    OptionMenu(root, x_var, *df.columns).grid(row=1, column=1)

    Label(root, text="Y-axis column (optional):").grid(row=2, column=0)
    y_var = StringVar(root)
    y_var.set('')
    OptionMenu(root, y_var, '', *df.columns).grid(row=2, column=1)

    # Plot type selection
    Label(root, text="Plot type:").grid(row=3, column=0)
    plot_var = StringVar(root)
    plot_var.set('histogram')
    plot_types = ['line', 'bar', 'scatter', 'histogram', 'boxplot']
    OptionMenu(root, plot_var, *plot_types).grid(row=3, column=1)

    def on_visualize():
        column_x = x_var.get()
        column_y = y_var.get() if y_var.get() else None
        plot_kind = plot_var.get()
        visualize_data(df, column_x, column_y, plot_kind)

    Button(root, text="Generate Plot", 
           command=on_visualize,
           bg='#4CAF50', 
           fg='white',
           pady=10).grid(row=4, column=0, columnspan=2, pady=20)

    root.mainloop()

def main():
    while True:
        print("\nPlease select a file to visualize.")
        file_path = select_file()
        
        if not file_path:
            print("No file selected. Exiting the program. Goodbye!")
            break
            
        df = load_file(file_path)
        if df is not None:
            create_visualization_window(df)
        
        if not messagebox.askyesno("Continue", "Do you want to visualize another file?"):
            print("Exiting the program. Goodbye!")
            break

if __name__ == "__main__":
    main()