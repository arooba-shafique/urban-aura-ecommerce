import json
import stripe
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from .cart import Cart
from .models import Category, Order, OrderItem, Product

stripe.api_key = settings.STRIPE_SECRET_KEY

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
        cart_items = [{"product": product, "quantity": 1, "total": product.price}]
        subtotal = product.price
        shipping = 5
        total_order_price = Decimal(str(subtotal)) + Decimal(str(shipping))
        request.session["buy_now"] = {"product_id": product.id, "quantity": 1}
        return render(request, "boutique/checkout.html", {
            "cart": cart_items,
            "total_price": subtotal,
            "shipping": shipping,
            "total_order_price": total_order_price,
            "buy_now": True,
            "stripe_public_key": settings.STRIPE_PUBLIC_KEY,
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
    
    total_order_price = Decimal(str(total_price)) + Decimal(str(shipping))

    if request.method == "POST":
        payment_method = request.POST.get("payment_method", "COD")

        if payment_method == "CARD":
            order = Order.objects.create(
                user=request.user,
                payment_method="CARD",
                is_paid=False,
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

            line_items = []
            for item in order.orderitem_set.select_related("product"):
                line_items.append({
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": item.product.name},
                        "unit_amount": int(float(item.product.price) * 100),
                    },
                    "quantity": item.quantity,
                })
            line_items.append({
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": "Shipping"},
                    "unit_amount": int(shipping * 100),
                },
                "quantity": 1,
            })

            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=line_items,
                mode="payment",
                success_url=request.build_absolute_uri(f"/payment/success/{order.id}/"),
                cancel_url=request.build_absolute_uri(f"/payment/cancel/{order.id}/"),
                metadata={"order_id": order.id},
            )

            order.stripe_session_id = session.id
            order.save()

            return redirect(session.url, code=303)

        else:
            order = Order.objects.create(
                user=request.user,
                payment_method="COD",
                is_paid=False,
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
        "stripe_public_key": settings.STRIPE_PUBLIC_KEY,
    })

@login_required
def payment_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if not order.is_paid:
        order.is_paid = True
        order.save()
    order_items = order.orderitem_set.all()
    for item in order_items:
        item.total_price = item.product.price * item.quantity
    subtotal = sum(item.total_price for item in order_items)
    shipping = order.shipping_cost
    total = subtotal + Decimal(str(shipping))
    return render(request, "boutique/payment_success.html", {
        "order": order,
        "order_items": order_items,
        "subtotal": subtotal,
        "shipping": shipping,
        "total": total,
    })


@login_required
def payment_cancel(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "boutique/payment_cancel.html", {"order": order})


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        order_id = session["metadata"].get("order_id")
        if order_id:
            Order.objects.filter(id=order_id).update(is_paid=True)

    return HttpResponse(status=200)


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.orderitem_set.all()
    for item in order_items:
        item.total_price = item.product.price * item.quantity
    subtotal = sum(item.total_price for item in order_items)
    shipping = 5
    total = subtotal + Decimal(str(shipping))
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


from .forms import RegisterForm  # ← add this import at the top

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)  # ← changed from UserCreationForm
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("boutique:landing")
    else:
        form = RegisterForm()  # ← changed from UserCreationForm
    return render(request, "boutique/register.html", {"form": form})