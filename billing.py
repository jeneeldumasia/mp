# billing.py
from settings import GST_RATE_PERCENT

class BillLogic:
    """
    Manages the state and logic of the current bill.
    This class does not interact with the UI or database directly.
    """
    def __init__(self):
        self.items = [] # List of {'name': str, 'price': float, 'quantity': int}

    def add_item(self, name, price):
        """Adds an item to the bill or increments its quantity if it already exists."""
        for item in self.items:
            if item['name'] == name:
                item['quantity'] += 1
                return
        self.items.append({'name': name, 'price': price, 'quantity': 1})

    def update_quantity(self, item_name, change):
        """Updates the quantity of an item. Removes it if quantity becomes zero or less."""
        for item in self.items:
            if item['name'] == item_name:
                item['quantity'] += change
                if item['quantity'] <= 0:
                    self.items.remove(item)
                return

    def get_bill_items(self):
        """Returns the current list of items in the bill."""
        return self.items

    def calculate_totals(self, discount_percent=0, apply_gst=False):
        """
        Calculates subtotal, discount amount, GST amount, and the final total.
        Returns a dictionary with all calculated values.
        """
        subtotal = sum(item['price'] * item['quantity'] for item in self.items)
        
        discount_amount = (subtotal * discount_percent) / 100
        
        amount_after_discount = subtotal - discount_amount
        
        gst_amount = 0
        if apply_gst:
            gst_amount = (amount_after_discount * GST_RATE_PERCENT) / 100
            
        final_total = amount_after_discount + gst_amount
        
        return {
            "subtotal": subtotal,
            "discount_amount": discount_amount,
            "gst_amount": gst_amount,
            "final_total": final_total
        }

    def clear_bill(self):
        """Resets the bill to an empty state."""
        self.items = []