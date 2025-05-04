import requests
from requests_oauthlib import OAuth1
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from urllib.parse import urljoin

class WooPriceUpdater:
    def __init__(self, root):
        self.root = root
        self.root.title("بروزرسانی قیمت سایت ............")
        self.root.geometry("750x500")
        self.root.configure(bg="#f9f9f9")

        self.base_url = "https://........../wp-json/wc/v3/"
        self.consumer_key = ""
        self.consumer_secret = ""
        self.auth = OAuth1(self.consumer_key, self.consumer_secret)

        self.new_prices = {}
        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill="both", expand=True)

        title = ttk.Label(frame, text="بروزرسانی قیمت محصولات", font=("Arial", 16, "bold"))
        title.pack(pady=10)

        search_frame = ttk.Frame(frame)
        search_frame.pack(fill="x", pady=5)

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, font=("Arial", 10), width=40)
        search_entry.pack(side="left", padx=5)

        search_button = ttk.Button(search_frame, text="جستجو", command=self.search_products)
        search_button.pack(side="left", padx=5)

        self.tree = ttk.Treeview(frame, columns=("ID", "نام", "رنگ", "قیمت قدیم", "قیمت جدید"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")

        self.tree.pack(fill="both", expand=True, pady=10)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack()

        ttk.Button(btn_frame, text="بروزرسانی قیمت‌ها", command=self.update_prices).pack(side="left", padx=5)

        credit = ttk.Label(self.root, text="Developed by Milad Ahmadi", font=("Arial", 8), foreground="gray")
        credit.pack(side="bottom", pady=5)

        self.tree.bind("<Button-1>", self.on_click)

    def search_products(self):
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning("هشدار", "لطفاً یک عبارت برای جستجو وارد کنید.")
            return

        for item in self.tree.get_children():
            self.tree.delete(item)
        self.new_prices.clear()

        try:
            url = urljoin(self.base_url, "products")
            params = {"search": query, "per_page": 100}
            response = requests.get(url, auth=self.auth, params=params, timeout=10)
            response.raise_for_status()
            products = response.json()

            for product in products:
                if query.lower() not in product["name"].lower():
                    continue  # جستجوی دقیق

                product_id = product["id"]
                name = product["name"]
                p_type = product.get("type", "")

                if p_type == "variable":
                    var_url = urljoin(self.base_url, f"products/{product_id}/variations")
                    var_resp = requests.get(var_url, auth=self.auth, timeout=10)
                    var_resp.raise_for_status()
                    variations = var_resp.json()

                    for var in variations:
                        variation_id = var["id"]
                        price = var.get("price") or "0"
                        color = self.extract_color(var)
                        key = f"{product_id}_{variation_id}"
                        new_price = self.new_prices.get(key, "")
                        self.tree.insert("", "end", values=(
                            product_id, name, color, int(float(price)), new_price), tags=(variation_id,))
                else:
                    price = product.get("price") or "0"
                    new_price = self.new_prices.get(str(product_id), "")
                    self.tree.insert("", "end", values=(
                        product_id, name, "ندارد", int(float(price)), new_price))

        except Exception as e:
            messagebox.showerror("خطا", f"خطا در دریافت محصولات:\n{e}")

    def extract_color(self, variation):
        for attr in variation.get("attributes", []):
            if attr["name"].lower() in ["رنگ", "color"]:
                return attr["option"]
        return "ندارد"

    def on_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            values = self.tree.item(item, "values")
            product_id, name, color, old_price, _ = values
            variation_id = self.tree.item(item, "tags")[0] if self.tree.item(item, "tags") else None

            prompt = f"قیمت جدید برای '{name}' رنگ {color}:"
            new_price = simpledialog.askfloat("قیمت جدید", prompt, parent=self.root, minvalue=0)

            if new_price is not None:
                new_price = int(float(new_price))
                key = f"{product_id}_{variation_id}" if variation_id else str(product_id)
                self.new_prices[key] = new_price
                self.tree.item(item, values=(product_id, name, color, old_price, new_price))

    def update_prices(self):
        try:
            for item in self.tree.get_children():
                values = self.tree.item(item)["values"]
                product_id, _, _, old_price, new_price = values
                variation_id = self.tree.item(item, "tags")[0] if self.tree.item(item, "tags") else None

                if new_price:
                    data = {
                        "regular_price": str(int(float(new_price))),
                        "meta_data": [{"key": "old_price", "value": str(old_price)}]
                    }
                    if variation_id:
                        url = urljoin(self.base_url, f"products/{product_id}/variations/{variation_id}")
                    else:
                        url = urljoin(self.base_url, f"products/{product_id}")
                    res = requests.put(url, auth=self.auth, json=data, timeout=10)
                    res.raise_for_status()

            messagebox.showinfo("موفق", "قیمت‌ها با موفقیت بروزرسانی شدند.")
            self.search_products()

        except Exception as e:
            messagebox.showerror("خطا", f"خطا در بروزرسانی:\n{e}")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    app = WooPriceUpdater(root)
    app.run()
