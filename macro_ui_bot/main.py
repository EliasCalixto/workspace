"""User interface for creating export/import templates.

This module presents a small Tkinter based GUI that allows the user to
generate different sets of spreadsheets based on predefined templates.
The GUI now exposes three dedicated buttons – *API Onboarding*,
*Simple Disconnection* and *BMC Exports* – each producing the required
files in a folder structure that contains two directories:
``Exports Results`` and ``Imports Results``.  All generated files are
prefixed with the provided Case ID.

The templates used to create the files live under ``renato_macro`` and
serve as blueprints for the final documents.  When multiple hotel IDs
are provided (one per line), the rows in every generated spreadsheet are
duplicated accordingly so that each hotel ID appears in the appropriate
column.
"""

from __future__ import annotations

import glob
import os
from typing import Dict, Iterable, List

import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMPLATES: Dict[str, str] = {
    "API Onboarding": os.path.join(ROOT_DIR, "renato_macro", "api ob"),
    "Simple Disconnection": os.path.join(
        ROOT_DIR, "renato_macro", "simple disconnection"
    ),
    "BMC Exports": os.path.join(ROOT_DIR, "renato_macro", "bmc exports"),
}


def _prepare_case_dir(base_path: str, case_id: str) -> Dict[str, str]:
    """Create case directory and the required sub-folders."""

    case_dir = os.path.join(base_path, case_id)
    exports_dir = os.path.join(case_dir, "Exports Results")
    imports_dir = os.path.join(case_dir, "Imports Results")
    os.makedirs(exports_dir, exist_ok=True)
    os.makedirs(imports_dir, exist_ok=True)
    return {"case": case_dir, "exports": exports_dir, "imports": imports_dir}


def _prefix_name(case_id: str, file_name: str) -> str:
    """Return ``file_name`` prefixed with the ``case_id``."""

    base = os.path.basename(file_name)
    parts = base.split("_", 1)
    core = parts[1] if len(parts) > 1 else base
    return f"{case_id} {core}"


def _duplicate_rows(
    df: pd.DataFrame, hotel_ids: Iterable[str], case_id: str, account_id: str
) -> pd.DataFrame:
    """Return a dataframe with one row per hotel id."""

    template_row = df.iloc[0].copy()
    rows: List[pd.Series] = []
    ids = list(hotel_ids) or [""]
    for hid in ids:
        row = template_row.copy()
        for col in ("Hotel ID", "Expedia ID"):
            if col in row.index:
                row[col] = hid
        if "SF ID" in row.index:
            row["SF ID"] = case_id
        rows.append(row)
    return pd.DataFrame(rows, columns=df.columns)


def create_api_onboarding(
    case_id: str, account_id: str, hotel_ids: Iterable[str], base_path: str
) -> None:
    dirs = _prepare_case_dir(base_path, case_id)
    template_dir = TEMPLATES["API Onboarding"]

    df = pd.read_excel(os.path.join(template_dir, "testapiob_Stop Sell Removal.xlsx"))
    df_out = _duplicate_rows(df, hotel_ids, case_id, account_id)
    out_xlsx = os.path.join(
        dirs["case"], _prefix_name(case_id, "Stop Sell Removal.xlsx")
    )
    df_out.to_excel(out_xlsx, index=False)

    csv_out = os.path.join(
        dirs["case"], _prefix_name(case_id, "UpdateManagedBy.csv")
    )
    pd.DataFrame(
        [
            {"Account ID": hid, "Managed by": account_id}
            for hid in (list(hotel_ids) or [""])
        ],
        columns=["Account ID", "Managed by"],
    ).to_csv(csv_out, index=False)


def create_simple_disconnection(
    case_id: str, account_id: str, hotel_ids: Iterable[str], base_path: str
) -> None:
    dirs = _prepare_case_dir(base_path, case_id)
    template_dir = TEMPLATES["Simple Disconnection"]

    df = pd.read_excel(
        os.path.join(template_dir, "testsimpledisc_disconnection import.xlsx")
    )
    df_out = _duplicate_rows(df, hotel_ids, case_id, account_id)
    out_xlsx = os.path.join(
        dirs["case"], _prefix_name(case_id, "disconnection import.xlsx")
    )
    df_out.to_excel(out_xlsx, index=False)

    csv_out = os.path.join(
        dirs["case"], _prefix_name(case_id, "delete managedBy.csv")
    )
    pd.DataFrame(
        [
            {"Account ID": hid, "Managed by": account_id}
            for hid in (list(hotel_ids) or [""])
        ],
        columns=["Account ID", "Managed by"],
    ).to_csv(csv_out, index=False)


def create_bmc_exports(
    case_id: str, account_id: str, hotel_ids: Iterable[str], base_path: str
) -> None:
    dirs = _prepare_case_dir(base_path, case_id)
    template_dir = TEMPLATES["BMC Exports"]

    for template in glob.glob(os.path.join(template_dir, "*.xlsx")):
        df = pd.read_excel(template)
        df_out = _duplicate_rows(df, hotel_ids, case_id, account_id)
        out_xlsx = os.path.join(
            dirs["case"], _prefix_name(case_id, os.path.basename(template))
        )
        df_out.to_excel(out_xlsx, index=False)


def main() -> None:  # pragma: no cover - GUI code
    root = tk.Tk()
    root.title("Macro UI Bot")

    tk.Label(root, text="SF Case ID:").grid(row=0, column=0, sticky="e")
    case_entry = tk.Entry(root)
    case_entry.grid(row=0, column=1, sticky="we")

    tk.Label(root, text="SF Account ID:").grid(row=1, column=0, sticky="e")
    account_entry = tk.Entry(root)
    account_entry.grid(row=1, column=1, sticky="we")

    tk.Label(root, text="Hotel IDs (one per line):").grid(row=2, column=0, sticky="ne")
    hotels_text = tk.Text(root, height=5, width=30)
    hotels_text.grid(row=2, column=1, sticky="we")

    tk.Label(root, text="Destination Path:").grid(row=3, column=0, sticky="e")
    path_var = tk.StringVar()
    path_entry = tk.Entry(root, textvariable=path_var, width=40)
    path_entry.grid(row=3, column=1, sticky="we")

    def browse() -> None:
        path = filedialog.askdirectory()
        if path:
            path_var.set(path)

    tk.Button(root, text="Browse", command=browse).grid(row=3, column=2)

    def run(option: str) -> None:
        case_id = case_entry.get().strip()
        account_id = account_entry.get().strip()
        hotels = [h.strip() for h in hotels_text.get("1.0", tk.END).splitlines() if h.strip()]
        base = path_var.get().strip()

        if not case_id or not account_id or not base:
            messagebox.showerror(
                "Error", "SF Case ID, SF Account ID and destination path are required."
            )
            return

        try:
            if option == "API Onboarding":
                create_api_onboarding(case_id, account_id, hotels, base)
            elif option == "Simple Disconnection":
                create_simple_disconnection(case_id, account_id, hotels, base)
            else:
                create_bmc_exports(case_id, account_id, hotels, base)
            messagebox.showinfo("Success", "Files created successfully.")
        except Exception as exc:  # pragma: no cover - safety net for GUI
            messagebox.showerror("Error", str(exc))

    button_frame = tk.Frame(root)
    button_frame.grid(row=4, column=0, columnspan=3, pady=10)
    tk.Button(
        button_frame, text="API Onboarding", command=lambda: run("API Onboarding")
    ).grid(row=0, column=0, padx=5)
    tk.Button(
        button_frame,
        text="Simple Disconnection",
        command=lambda: run("Simple Disconnection"),
    ).grid(row=0, column=1, padx=5)
    tk.Button(
        button_frame, text="BMC Exports", command=lambda: run("BMC Exports")
    ).grid(row=0, column=2, padx=5)
    tk.Button(button_frame, text="Quit", command=root.destroy).grid(row=0, column=3, padx=5)

    root.columnconfigure(1, weight=1)
    root.mainloop()


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()

