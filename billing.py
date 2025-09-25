# billing.py

class BillLogic:
    def __init__(self):
        self.items = []

    def add_item(self, name, price):
        for item in self.items:
            if item['name'] == name:
                item['quantity'] += 1
                return
        self.items.append({'name': name, 'price': price, 'quantity': 1})

    def update_quantity(self, item_name, change):
        for item in self.items:
            if item['name'] == item_name:
                item['quantity'] += change
                if item['quantity'] <= 0:
                    self.items.remove(item)
                return

    def get_bill_items(self):
        return self.items

    # --- MODIFIED: Function now accepts the gst_rate from the database ---
    def calculate_totals(self, discount_percent=0, apply_gst=False, gst_rate=5.0):
        subtotal = sum(item['price'] * item['quantity'] for item in self.items)
        discount_amount = (subtotal * discount_percent) / 100
        amount_after_discount = subtotal - discount_amount
        
        gst_amount = 0
        if apply_gst:
            gst_amount = (amount_after_discount * gst_rate) / 100
            
        final_total = amount_after_discount + gst_amount
        
        return {
            "subtotal": subtotal,
            "discount_amount": discount_amount,
            "gst_amount": gst_amount,
            "final_total": final_total
        }

    def clear_bill(self):
        self.items = []