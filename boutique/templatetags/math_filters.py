from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply two numbers."""
    return float(value) * float(arg)

@register.filter
def sum_total(order_items):
    """Calculate total price of an order."""
    total = 0
    for item in order_items:
        total += item.quantity * float(item.product.price)
    return total
