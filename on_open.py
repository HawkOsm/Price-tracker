from Product import Product
from Tracker import update_all_products, load_products

import webbrowser
import tkinter as tk
from tkinter import ttk
from typing import Optional

update_all_products("data.json")

load_products("data.json")

def _effective_threshold_for(p: Product, default_threshold: float = 10.0) -> float:
    """
    Decide the notify threshold for this product (in %).
    Priority:
      1) If the object has attributes on_change/on_max_change, use the max of those (if present & >=0)
      2) Else fall back to a default (e.g., 10%)
    """
    candidates = []
    for attr in ("on_change", "on_max_change"):
        if hasattr(p, attr):
            v = getattr(p, attr)
            if isinstance(v, (int, float)) and v >= 0:
                candidates.append(float(v))
    return max(candidates) if candidates else float(default_threshold)

def find_changed_products(products: list[Product], default_threshold: float = 10.0):
  
    changed = []
    for p in products:
        try:
            name = p.get_name()
            url = p.get_url()

            pct_change = p.get_change()

            if pct_change is None or pct_change == "":
                continue

            pct = abs(float(pct_change))
            threshold = _effective_threshold_for(p, default_threshold)

            if pct >= threshold:
                changed.append((name, url, pct, threshold))
        except Exception:

            continue
    return changed

def show_changes_popup(changed_items: list[tuple[str, str, float, float]]) -> None:
    """
    Tkinter popup showing items that crossed the threshold.
    - Double-click an item or press 'Open Selected' to open its URL
    - 'Open All' opens all URLs
    """
    if not changed_items:
        return
    root = tk.Tk()
    root.title("Product Change Alert")

    frm = ttk.Frame(root, padding=12)
    frm.grid(row=0, column=0, sticky="nsew")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)


    ttk.Label(frm, text="The following products changed beyond your threshold:").grid(
        row=0, column=0, columnspan=3, sticky="w", pady=(0, 8)
    )

    list_frame = ttk.Frame(frm)
    list_frame.grid(row=1, column=0, columnspan=3, sticky="nsew")
    frm.rowconfigure(1, weight=1)
    frm.columnconfigure(0, weight=1)

    lb = tk.Listbox(list_frame, height=10, activestyle="dotbox")
    sb = ttk.Scrollbar(list_frame, orient="vertical", command=lb.yview)
    lb.configure(yscrollcommand=sb.set)
    lb.grid(row=0, column=0, sticky="nsew")
    sb.grid(row=0, column=1, sticky="ns")
    list_frame.columnconfigure(0, weight=1)
    list_frame.rowconfigure(0, weight=1)

    urls = []

    for name, url, pct, threshold in changed_items:
        lb.insert(tk.END, f"{name} — {pct:.1f}% (threshold {threshold:.1f}%)")
        urls.append(url)

    def open_selected(event: Optional[tk.Event] = None):
        sel = lb.curselection()
        if not sel:
            return
        idx = sel[0]
        u = urls[idx]
        if u:
            webbrowser.open(u)

    def open_all():
        for u in urls:
            if u:
                webbrowser.open(u)

    # Buttons
    btn_open = ttk.Button(frm, text="Open Selected", command=open_selected)
    btn_open.grid(row=2, column=0, sticky="w", pady=(8, 0))

    btn_open_all = ttk.Button(frm, text="Open All", command=open_all)
    btn_open_all.grid(row=2, column=1, sticky="w", pady=(8, 0))

    btn_close = ttk.Button(frm, text="Close", command=root.destroy)
    btn_close.grid(row=2, column=2, sticky="e", pady=(8, 0))

    lb.bind("<Double-Button-1>", open_selected)

    root.minsize(520, 260)
    root.mainloop()


changed = find_changed_products(products, default_threshold=10.0)
show_changes_popup(changed)
