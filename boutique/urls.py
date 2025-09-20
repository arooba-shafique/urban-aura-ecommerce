from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = "boutique"

urlpatterns = [
    # Landing & Products
    path("", views.landing, name="landing"),
    path("products/", views.product_list, name="product_list"),
    path("products/category/<slug:category_slug>/", views.category_products, name="category_products"),
    path("search/", views.search_products, name="search_products"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),

    # Cart
    path("cart/", views.cart_view, name="cart_view"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/remove/<int:product_id>/", views.cart_remove, name="cart_remove"),
    path("cart/update/<int:product_id>/", views.cart_update, name="cart_update"),

    # Orders
    path("orders/", views.order_list, name="order_list"),
    path("buy-now/", views.buy_now, name="buy_now"),
    path("checkout/", views.checkout, name="checkout"),
    path("order/success/<int:order_id>/", views.order_success, name="order_success"),

    # Auth
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="boutique/login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page=reverse_lazy("boutique:landing")),
        name="logout",
    ),
]
