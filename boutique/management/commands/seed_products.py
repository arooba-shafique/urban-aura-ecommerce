import urllib.request
import os
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from boutique.models import Category, Product

PRODUCTS = [
    # Dresses
    {
        "category": "dresses",
        "name": "Floral Maxi Dress",
        "slug": "floral-maxi-dress",
        "description": "A beautiful floral maxi dress perfect for summer outings.",
        "price": "19.99",
        "stock": 20,
        "image_url": "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=400",
    },
    {
        "category": "dresses",
        "name": "Velvet Twilight Dress",
        "slug": "Velvet-Twilight-Dress",
        "description": "Elegant black evening gown for formal occasions.",
        "price": "34.99",
        "stock": 15,
        "image_url": "https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=400",
    },
    {
        "category": "dresses",
        "name": "Casual Summer Dress",
        "slug": "casual-summer-dress",
        "description": "Light and breezy casual dress for everyday wear.",
        "price": "12.99",
        "stock": 25,
        "image_url": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400",
    },
    # Shoes
    {
        "category": "shoes",
        "name": "Nude Heels",
        "slug": "nude-heels",
        "description": "Classic nude heels that go with every outfit.",
        "price": "17.99",
        "stock": 18,
        "image_url": "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=400",
    },
    {
        "category": "shoes",
        "name": "White Sneakers",
        "slug": "white-sneakers",
        "description": "Trendy white sneakers for a casual chic look.",
        "price": "14.99",
        "stock": 30,
        "image_url": "https://images.unsplash.com/photo-1600269452121-4f2416e55c28?w=400",
    },
    {
        "category": "shoes",
        "name": "Strappy Sandals",
        "slug": "strappy-sandals",
        "description": "Stylish strappy sandals perfect for summer.",
        "price": "9.99",
        "stock": 22,
        "image_url": "https://images.unsplash.com/photo-1603487742131-4160ec999306?w=400",
    },
    # Bags
    {
        "category": "bags",
        "name": "Leather Tote Bag",
        "slug": "leather-tote-bag",
        "description": "Spacious leather tote bag for work and everyday use.",
        "price": "24.99",
        "stock": 12,
        "image_url": "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=400",
    },
    {
        "category": "bags",
        "name": "Mini Crossbody Bag",
        "slug": "mini-crossbody-bag",
        "description": "Cute mini crossbody bag for evenings out.",
        "price": "12.99",
        "stock": 20,
        "image_url": "https://images.unsplash.com/photo-1590874103328-eac38a683ce7?w=400",
    },
    {
        "category": "bags",
        "name": "Sequin Clutch",
        "slug": "sequin-clutch",
        "description": "Glamorous sequin clutch for parties and special events.",
        "price": "8.99",
        "stock": 25,
        "image_url": "https://images.unsplash.com/photo-1566150905458-1bf1fc113f0d?w=400",
    },
    # Jewelry
    {
        "category": "jewelry",
        "name": "Gold Hoop Earrings",
        "slug": "gold-hoop-earrings",
        "description": "Classic gold hoop earrings that elevate any look.",
        "price": "5.99",
        "stock": 40,
        "image_url": "https://images.unsplash.com/photo-1630019852942-f89202989a59?w=400",
    },
    {
        "category": "jewelry",
        "name": "Pearl Necklace",
        "slug": "pearl-necklace",
        "description": "Timeless pearl necklace for elegant occasions.",
        "price": "9.99",
        "stock": 30,
        "image_url": "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=400",
    },
    {
        "category": "jewelry",
        "name": "Stackable Rings Set",
        "slug": "stackable-rings-set",
        "description": "Trendy set of stackable rings in gold and silver tones.",
        "price": "7.99",
        "stock": 35,
        "image_url": "https://images.unsplash.com/photo-1605100804763-247f67b3557e?w=400",
    },
]


class Command(BaseCommand):
    help = "Seed the database with sample products"

    def handle(self, *args, **kwargs):
        for data in PRODUCTS:
            category, _ = Category.objects.get_or_create(
                slug=data["category"],
                defaults={"name": data["category"].capitalize()}
            )

            if Product.objects.filter(slug=data["slug"]).exists():
                self.stdout.write(f"Skipping {data['name']} — already exists")
                continue

            product = Product(
                category=category,
                name=data["name"],
                slug=data["slug"],
                description=data["description"],
                price=data["price"],
                stock=data["stock"],
            )

            try:
                self.stdout.write(f"Downloading image for {data['name']}...")
                req = urllib.request.Request(
                    data["image_url"],
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    image_data = response.read()
                filename = f"{data['slug']}.jpg"
                product.image.save(filename, ContentFile(image_data), save=False)
            except Exception as e:
                self.stdout.write(f"  Image failed: {e} — skipping image")

            product.save()
            self.stdout.write(self.style.SUCCESS(f"✓ Created {data['name']}"))

        self.stdout.write(self.style.SUCCESS("\nAll products seeded!"))