from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q

from .models import Product, Category, Order, OrderItem
from .cart import Cart


def landing(request):
    categories = Category.objects.all()
    products = Product.objects.all()[:8]
    selected_category = request.GET.get("category", "")
    return render(request, "boutique/landing.html", {
        "categories": categories,
        "products": products,
        "selected_category": selected_category,
    })


def product_list(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    return render(request, "boutique/product_list.html", {
        "products": products,
        "categories": categories,
    })


def category_products(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    products = Product.objects.filter(category=category)
    return render(request, "boutique/category_products.html", {
        "category": category,
        "products": products,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, "boutique/product_detail.html", {"product": product})


def search_products(request):
    query = request.GET.get("q")
    products = Product.objects.none()
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(category__name__icontains=query)
        )
    return render(request, "boutique/search_results.html", {
        "products": products,
        "query": query,
    })


def cart_view(request):
    cart = Cart(request)
    return render(request, "boutique/cart.html", {"cart": cart})


def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.add(product=product, quantity=1)
    messages.success(request, f"'{product.name}' added to cart!")
    return redirect(request.META.get("HTTP_REFERER", "boutique:product_list"))


def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.success(request, f"'{product.name}' removed from cart!")
    return redirect("boutique:cart_view")


@login_required
def cart_update(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "increase":
            cart.add(product=product, quantity=1)
        elif action == "decrease":
            cart.remove_one(product=product)
    return redirect("boutique:cart_view")


@login_required
def buy_now(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        product = get_object_or_404(Product, id=product_id)
        cart_items = [{
            "product": product,
            "quantity": 1,
            "total": product.price,
        }]
        subtotal = product.price
        shipping = 5
        total_order_price = subtotal + shipping
        request.session["buy_now"] = {
            "product_id": product.id,
            "quantity": 1,
        }
        return render(request, "boutique/checkout.html", {
            "cart": cart_items,
            "total_price": subtotal,
            "shipping": shipping,
            "total_order_price": total_order_price,
            "buy_now": True,
        })
    return redirect("boutique:product_list")


@login_required
def checkout(request):
    cart = Cart(request)
    buy_now_item = request.session.get("buy_now")

    if buy_now_item:
        product = get_object_or_404(Product, id=buy_now_item["product_id"])
        cart_items = [{
            "product": product,
            "quantity": buy_now_item["quantity"],
            "total": product.price * buy_now_item["quantity"],
        }]
        total_price = product.price * buy_now_item["quantity"]
    else:
        cart_items = list(cart)
        total_price = cart.get_total_price()

    shipping = 5
    total_order_price = total_price + shipping

    if request.method == "POST":
        payment_method = request.POST.get("payment_method", "COD")
        is_paid = True if payment_method == "CARD" else False
        order = Order.objects.create(
            user=request.user,
            payment_method=payment_method,
            is_paid=is_paid,
            shipping_cost=shipping,
        )
        if buy_now_item:
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=buy_now_item["quantity"],
            )
            del request.session["buy_now"]
        else:
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item["product"],
                    quantity=item["quantity"],
                )
            cart.clear()
        return redirect("boutique:order_success", order_id=order.id)

    return render(request, "boutique/checkout.html", {
        "cart": cart_items,
        "total_price": total_price,
        "shipping": shipping,
        "total_order_price": total_order_price,
    })


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.orderitem_set.all()
    for item in order_items:
        item.total_price = item.product.price * item.quantity
    subtotal = sum(item.total_price for item in order_items)
    shipping = 5
    total = subtotal + shipping
    return render(request, "boutique/order_success.html", {
        "order": order,
        "order_items": order_items,
        "subtotal": subtotal,
        "shipping": shipping,
        "total": total,
    })


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "boutique/order_list.html", {"orders": orders})


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("boutique:landing")
    else:
        form = UserCreationForm()
    return render(request, "boutique/register.html", {"form": form})
