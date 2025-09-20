from .models import Product

class Cart:
    def __init__(self, request):
        """
        Initialize the cart using the session.
        """
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, product, quantity=1):
        """
        Add a product to the cart or increase its quantity.
        """
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0, 'price': str(product.price)}
        self.cart[product_id]['quantity'] += quantity
        self.save()

    def remove(self, product):
        """
        Remove a product from the cart completely.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def remove_one(self, product):
        """
        Decrease quantity of a product by one. Remove if quantity <= 0.
        """
        product_id = str(product.id)
        if product_id in self.cart:
            self.cart[product_id]['quantity'] -= 1
            if self.cart[product_id]['quantity'] <= 0:
                del self.cart[product_id]
            self.save()

    def clear(self):
        """
        Clear the entire cart.
        """
        self.session['cart'] = {}
        self.session.modified = True

    def save(self):
        """
        Mark the session as modified to save changes.
        """
        self.session['cart'] = self.cart
        self.session.modified = True

    def __iter__(self):
        """
        Iterate over the items and attach the actual product object.
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        for product in products:
            item = self.cart[str(product.id)]
            item['product'] = product
            item['total'] = float(item['price']) * item['quantity']
            yield item

    def get_total_price(self):
        """
        Calculate total price of all items in the cart.
        """
        return sum(float(item['price']) * item['quantity'] for item in self.cart.values())
