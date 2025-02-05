import pandas as pd
import matplotlib.pyplot as plt
from tkinter import Tk, filedialog, messagebox, Button, Label, StringVar, OptionMenu, Entry, Frame

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
        elif file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file format. Please provide a CSV or Excel file.")
        print(f"Loaded file: {file_path}")
        print(f"Available columns: {', '.join(df.columns)}")
        return df
    except Exception as e:
        messagebox.showerror("File Load Error", str(e))
        return None


def analyze_missing_data(df):
    missing_counts = df.isnull().sum()
    zero_counts = (df == 0).sum()
    
    print("Missing Value Analysis:")
    print(missing_counts[missing_counts > 0])
    print("\nZero Value Analysis:")
    print(zero_counts[zero_counts > 0])
    
    plt.figure(figsize=(12, 6))
    plt.bar(missing_counts.index, missing_counts.values, color='orange', label='Missing (NULL)')
    plt.bar(zero_counts.index, zero_counts.values, color='blue', alpha=0.6, label='Zeros')
    plt.title("Missing and Zero Values Count")
    plt.xlabel("Columns")
    plt.ylabel("Count")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.show()

def analyze_duplicates(df, columns):
    duplicate_counts = df.duplicated(subset=columns, keep=False).sum()
    print(f"\nNumber of duplicate rows based on {columns}: {duplicate_counts}")
    
    plt.figure(figsize=(10, 6))
    if duplicate_counts > 0:
        plt.bar(["Duplicates", "Unique"], [duplicate_counts, len(df) - duplicate_counts], color=['red', 'green'])
    else:
        plt.bar(["Unique"], [len(df)], color='green')
    plt.title(f"Duplicate Analysis Based on {', '.join(columns)}")
    plt.ylabel("Count")
    plt.show()

def create_visualization_window(df):
    from tkinter import messagebox

    root = Tk()
    root.title("Data Visualization")
    root.geometry("500x400")

    Label(root, text="Select visualization options:", font=('Arial', 12, 'bold')).pack(pady=10)

    # Row selection
    row_frame = Frame(root)
    Label(row_frame, text="Rows to visualize (number or 'all'):").pack(side='left')
    row_var = StringVar(root)
    row_var.set('all')
    Entry(row_frame, textvariable=row_var, width=10).pack(side='right')
    row_frame.pack(pady=5)

    # Column selection
    column_frame = Frame(root)
    Label(column_frame, text="Select columns (comma-separated or 'all'):").pack(side='left')
    column_var = StringVar(root)
    column_var.set('all')
    Entry(column_frame, textvariable=column_var, width=20).pack(side='right')
    column_frame.pack(pady=5)

    # Plot type selection
    Label(root, text="Plot type:").pack()
    plot_var = StringVar(root)
    plot_var.set('histogram')
    plot_types = ['bar', 'line', 'scatter', 'histogram', 'boxplot']
    OptionMenu(root, plot_var, *plot_types).pack(pady=5)

    def on_visualize():
        rows = row_var.get()
        selected_columns = column_var.get().split(',') if column_var.get() != 'all' else list(df.columns)
        plot_kind = plot_var.get()

        try:
            sub_df = df.copy()
            if rows != 'all':
                rows = int(rows)
                sub_df = sub_df.head(rows)
            
            print("\nFirst 10 rows of the dataset:")
            print(df.head(10))  # Print first 10 rows in the terminal

            for column in selected_columns:
                if column.strip() in sub_df.columns:
                    plt.figure(figsize=(10, 6))
                    if plot_kind == 'bar':
                        sub_df[column.strip()].value_counts().plot(kind='bar', title=f"Bar Plot: {column.strip()}")
                    elif plot_kind == 'histogram':
                        sub_df[column.strip()].hist(bins=10, edgecolor='black')
                        plt.title(f"Histogram: {column.strip()}")
                    elif plot_kind == 'boxplot':
                        plt.boxplot(sub_df[column.strip()].dropna(), vert=False)
                        plt.title(f"Boxplot: {column.strip()}")
                    else:
                        plt.title(f"{plot_kind.capitalize()} Plot: {column.strip()}")
                    plt.xlabel(column.strip())
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    plt.show()
                else:
                    messagebox.showerror("Error", f"Column {column.strip()} not found in data.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_analyze():
        # Retrieve selected columns
        selected_columns = column_var.get().split(',') if column_var.get() != 'all' else list(df.columns)
        
        print("\nFirst 10 rows of the dataset:")
        print(df.head(10))  # Print first 10 rows in the terminal

        # Analyze missing data
        print("\nMissing values per column:")
        print(df.isnull().sum())

        # Analyze duplicate values
        print("\nDuplicate entries:")
        print(df.duplicated().sum())

        # Analyze duplicates in selected columns
        if selected_columns:
            print("\nDuplicates in selected columns:")
            duplicate_counts = df[selected_columns].duplicated().sum()
            print(f"Duplicates in {', '.join(selected_columns)}: {duplicate_counts}")

    Button(root, text="Generate Visualization", 
           command=on_visualize,
           bg='#4CAF50', fg='white').pack(pady=10)

    Button(root, text="Analyze Data", 
           command=on_analyze,
           bg='#2196F3', fg='white').pack(pady=10)

    root.mainloop()


def main():
    file_path = select_file()
    if not file_path:
        print("No file selected. Exiting.")
        return
    
    df = load_file(file_path)
    if df is not None:
        create_visualization_window(df)

if __name__ == "__main__":
    main()