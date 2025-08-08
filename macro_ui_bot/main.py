import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List


def create_files(case_id: str, account_id: str, hotels: str, base_path: str) -> None:
    """Create folder structure and Excel/CSV files for a case.

    Args:
        case_id: Salesforce case identifier.
        account_id: Salesforce account identifier.
        hotels: Comma separated hotel identifiers.
        base_path: Destination directory where the case folder will be created.
    """
    hotel_ids: List[str] = [h.strip() for h in hotels.split(',') if h.strip()]
    case_dir = os.path.join(base_path, case_id)
    os.makedirs(case_dir, exist_ok=True)

    # Excel file
    rows = max(len(hotel_ids), 1)
    df_xlsx = pd.DataFrame({
        'Hotel ID': hotel_ids if hotel_ids else [''],
        'SF ID': [account_id] + [''] * (rows - 1),
        'Stop Sell Property': ['No'] * rows,
        'Action Type': ['Update'] * rows,
    })
    excel_path = os.path.join(case_dir, f"{case_id} IMPORT Stop Sell Removal.xlsx")
    df_xlsx.to_excel(excel_path, index=False)

    # CSV file
    df_csv = pd.DataFrame({
        'Account ID': [account_id],
        'Managed by': ['']
    })
    csv_path = os.path.join(case_dir, f"{case_id} UpdateManagedBy.csv")
    df_csv.to_csv(csv_path, index=False)


def main() -> None:
    root = tk.Tk()
    root.title("Macro UI Bot")

    tk.Label(root, text="SF Case ID:").grid(row=0, column=0, sticky="e")
    case_entry = tk.Entry(root)
    case_entry.grid(row=0, column=1)

    tk.Label(root, text="SF Account ID:").grid(row=1, column=0, sticky="e")
    account_entry = tk.Entry(root)
    account_entry.grid(row=1, column=1)

    tk.Label(root, text="Hotels IDs (comma separated):").grid(row=2, column=0, sticky="e")
    hotels_entry = tk.Entry(root)
    hotels_entry.grid(row=2, column=1)

    tk.Label(root, text="Destination Path:").grid(row=3, column=0, sticky="e")
    path_var = tk.StringVar()
    path_entry = tk.Entry(root, textvariable=path_var, width=40)
    path_entry.grid(row=3, column=1)

    def browse() -> None:
        path = filedialog.askdirectory()
        if path:
            path_var.set(path)

    tk.Button(root, text="Browse", command=browse).grid(row=3, column=2)

    def run() -> None:
        case_id = case_entry.get().strip()
        account_id = account_entry.get().strip()
        hotels = hotels_entry.get().strip()
        path = path_var.get().strip()

        if not case_id or not account_id or not path:
            messagebox.showerror("Error", "SF Case ID, SF Account ID and path are required.")
            return
        try:
            create_files(case_id, account_id, hotels, path)
            messagebox.showinfo("Success", "Files created successfully.")
        except Exception as exc:  # pragma: no cover - GUI errors
            messagebox.showerror("Error", str(exc))

    tk.Button(root, text="Create Files", command=run).grid(row=4, column=1, pady=10)
    tk.Button(root, text="Quit", command=root.destroy).grid(row=4, column=2, pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()
