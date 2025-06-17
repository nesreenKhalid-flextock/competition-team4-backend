import random
from django.core.management.base import BaseCommand
from base.models import Shop, Product
from base.enums import ShopCategoryEnum


class Command(BaseCommand):
    help = "Seed database with shops and products"

    def add_arguments(self, parser):
        parser.add_argument(
            "--shops",
            type=int,
            default=20,
            help="Number of shops to create (default: 20)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing shops and products before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing data...")
            Product.objects.all().delete()
            Shop.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Existing data cleared."))

        num_shops = options["shops"]
        self.stdout.write(f"Creating {num_shops} shops with products...")

        # Shop data organized by category with unique naming patterns
        shop_data = {
            ShopCategoryEnum.RESTAURANT.value: {
                "base_names": [
                    "Al Taza",
                    "Zooba",
                    "Kazouza",
                    "Maison Thomas",
                    "Abu Shakra",
                    "Felfela",
                    "Sequoia",
                    "Abou El Sid",
                    "Taboula",
                    "Cilantro Kitchen",
                ],
                "suffixes": [
                    "Restaurant",
                    "Kitchen",
                    "Grill",
                    "House",
                    "Place",
                    "Bistro",
                    "Eatery",
                    "Dining",
                    "Express",
                    "Corner",
                ],
                "locations": [
                    "Zamalek",
                    "New Cairo",
                    "Heliopolis",
                    "Maadi",
                    "Nasr City",
                    "Downtown",
                    "Mohandessin",
                    "Dokki",
                    "Garden City",
                    "Tagamoa",
                ],
                "descriptions": [
                    "Authentic Egyptian cuisine with traditional flavors",
                    "Modern Egyptian street food experience",
                    "Family restaurant serving home-style Egyptian dishes",
                    "European-Egyptian fusion cuisine",
                    "Premium Egyptian grills and kebabs",
                    "Contemporary dining with local ingredients",
                    "Traditional recipes passed down through generations",
                    "Casual dining with Egyptian comfort food",
                ],
                "products": {
                    "Main Dishes": [
                        (
                            "Koshari",
                            45,
                            "Traditional Egyptian rice, lentils, and pasta dish",
                        ),
                        (
                            "Molokhia with Chicken",
                            85,
                            "Egyptian green soup with tender chicken",
                        ),
                        (
                            "Stuffed Vine Leaves",
                            65,
                            "Rice-stuffed grape leaves with herbs",
                        ),
                        (
                            "Grilled Chicken",
                            120,
                            "Marinated grilled chicken with Egyptian spices",
                        ),
                        (
                            "Beef Shawarma",
                            75,
                            "Sliced beef with tahini and vegetables",
                        ),
                        (
                            "Falafel Plate",
                            55,
                            "Crispy falafel with tahini and salad",
                        ),
                        (
                            "Mixed Grill",
                            150,
                            "Assorted grilled meats with rice",
                        ),
                        (
                            "Fish Tagine",
                            95,
                            "Baked fish with vegetables and rice",
                        ),
                        (
                            "Lamb Kofta",
                            110,
                            "Spiced ground lamb with rice",
                        ),
                        (
                            "Chicken Shawarma",
                            70,
                            "Marinated chicken with garlic sauce",
                        ),
                        (
                            "Beef Kebab",
                            130,
                            "Grilled beef skewers with vegetables",
                        ),
                        (
                            "Stuffed Cabbage",
                            60,
                            "Cabbage rolls with rice and meat",
                        ),
                        (
                            "Grilled Fish",
                            140,
                            "Fresh fish with Egyptian spices",
                        ),
                        (
                            "Chicken Curry",
                            90,
                            "Spiced chicken in curry sauce",
                        ),
                        (
                            "Beef Stew",
                            105,
                            "Tender beef with vegetables",
                        ),
                    ],
                    "Appetizers": [
                        ("Hummus", 25, "Creamy chickpea dip with olive oil"),
                        ("Baba Ganoush", 30, "Smoky eggplant dip with tahini"),
                        (
                            "Egyptian Salad",
                            35,
                            "Fresh tomatoes, cucumbers, and herbs",
                        ),
                        ("Cheese Sambousek", 40, "Fried pastry filled with cheese"),
                        (
                            "Fried Eggplant",
                            32,
                            "Crispy eggplant with garlic sauce",
                        ),
                        ("Tahini Salad", 28, "Mixed vegetables with tahini dressing"),
                        ("Meat Sambousek", 45, "Fried pastry with spiced meat"),
                        ("Pickled Vegetables", 20, "Traditional Egyptian pickles"),
                        ("Cheese Rolls", 38, "Phyllo pastry with cheese"),
                        ("Spinach Fatayer", 35, "Pastry triangles with spinach"),
                    ],
                    "Beverages": [
                        (
                            "Fresh Orange Juice",
                            20,
                            "Freshly squeezed Egyptian oranges",
                        ),
                        ("Hibiscus Tea", 15, "Traditional Egyptian hibiscus drink"),
                        ("Turkish Coffee", 18, "Strong aromatic coffee"),
                        ("Mint Lemonade", 22, "Refreshing mint and lemon drink"),
                        ("Mango Juice", 25, "Fresh tropical mango juice"),
                        ("Cinnamon Tea", 16, "Warm spiced cinnamon tea"),
                        ("Fresh Lime Juice", 20, "Tangy fresh lime drink"),
                        ("Strawberry Juice", 24, "Sweet fresh strawberry drink"),
                    ],
                },
            },
            ShopCategoryEnum.CAFE.value: {
                "base_names": [
                    "Beano's",
                    "Cilantro",
                    "Coffee Bean",
                    "Greco",
                    "Costa",
                    "Cafe Supreme",
                    "Roastery",
                    "Brew House",
                    "Espresso Bar",
                    "Coffee Culture",
                ],
                "suffixes": [
                    "Cafe",
                    "Coffee",
                    "Lounge",
                    "Bar",
                    "House",
                    "Corner",
                    "Hub",
                    "Station",
                    "Spot",
                    "Place",
                ],
                "locations": [
                    "City Center",
                    "Mall of Egypt",
                    "Tahrir Square",
                    "Gezira",
                    "Festival City",
                    "Katameya",
                    "Sheikh Zayed",
                    "October",
                    "Rehab City",
                    "Korba",
                ],
                "descriptions": [
                    "Premium coffee and light bites",
                    "Modern cafe with international menu",
                    "Specialty coffee roasters and cafe",
                    "European-style cafe and patisserie",
                    "Cozy coffee house with free WiFi",
                    "Artisan coffee with homemade pastries",
                    "Contemporary cafe with outdoor seating",
                ],
                "products": {
                    "Coffee": [
                        ("Cappuccino", 35, "Espresso with steamed milk foam"),
                        ("Latte", 40, "Smooth espresso with steamed milk"),
                        ("Americano", 30, "Espresso with hot water"),
                        ("Espresso", 25, "Strong shot of coffee"),
                        ("Mocha", 45, "Coffee with chocolate and whipped cream"),
                        ("Macchiato", 38, "Espresso with a dollop of milk foam"),
                        ("Flat White", 42, "Double espresso with microfoam milk"),
                        ("Cortado", 36, "Equal parts espresso and warm milk"),
                        ("Iced Coffee", 32, "Cold brew coffee with ice"),
                        ("French Press", 28, "Full-bodied coffee brewing method"),
                        ("Cold Brew", 35, "Smooth cold-extracted coffee"),
                        ("Affogato", 48, "Espresso shot over vanilla ice cream"),
                    ],
                    "Pastries": [
                        ("Croissant", 25, "Buttery French pastry"),
                        ("Danish Pastry", 30, "Sweet pastry with fruit filling"),
                        ("Muffin", 28, "Soft cake with various flavors"),
                        ("Cheesecake Slice", 50, "Rich and creamy cheesecake"),
                        ("Chocolate Brownie", 35, "Fudgy chocolate brownie"),
                        ("Cinnamon Roll", 32, "Sweet spiral pastry with cinnamon"),
                        ("Scone", 26, "British-style tea pastry"),
                        ("Eclair", 40, "Cream-filled choux pastry"),
                        ("Macarons", 45, "French almond cookies"),
                        ("Tiramisu", 55, "Italian coffee-flavored dessert"),
                    ],
                    "Sandwiches": [
                        (
                            "Club Sandwich",
                            65,
                            "Triple-layer sandwich with chicken and bacon",
                        ),
                        ("Grilled Cheese", 45, "Melted cheese between toasted bread"),
                        ("Turkey Sandwich", 55, "Sliced turkey with fresh vegetables"),
                        ("Tuna Melt", 52, "Tuna salad with melted cheese"),
                        ("BLT", 48, "Bacon, lettuce, and tomato sandwich"),
                        (
                            "Chicken Caesar Wrap",
                            58,
                            "Grilled chicken with Caesar dressing",
                        ),
                        ("Veggie Panini", 42, "Grilled vegetables on pressed bread"),
                    ],
                },
            },
            ShopCategoryEnum.BAKERY.value: {
                "base_names": [
                    "Mo'men",
                    "Mandarine",
                    "La Poire",
                    "Tseppas",
                    "BreadFast",
                    "Golden Bakery",
                    "Fresh Bread",
                    "Artisan",
                    "Royal Bakery",
                    "Sweet Corner",
                ],
                "suffixes": [
                    "Bakery",
                    "Patisserie",
                    "Bread House",
                    "Sweet Shop",
                    "Pastry",
                    "Boulangerie",
                    "Sweets",
                    "Confectionery",
                    "Desserts",
                    "Treats",
                ],
                "locations": [
                    "Downtown Cairo",
                    "Zamalek",
                    "Maadi",
                    "Heliopolis",
                    "New Cairo",
                    "Nasr City",
                    "Mohandessin",
                    "Dokki",
                    "Agouza",
                    "Garden City",
                ],
                "descriptions": [
                    "Traditional Egyptian bakery",
                    "French-Egyptian patisserie",
                    "Artisan bakery and cafe",
                    "European-style bakery",
                    "Modern bakery with delivery",
                    "Fresh daily baked goods",
                    "Specialty cakes and pastries",
                ],
                "products": {
                    "Bread": [
                        (
                            "Egyptian Baladi Bread",
                            2,
                            "Traditional Egyptian flatbread",
                        ),
                        ("French Baguette", 12, "Crispy French bread"),
                        ("Whole Wheat Bread", 15, "Healthy whole grain bread"),
                        ("Pita Bread", 5, "Soft pocket bread"),
                        ("Sourdough Bread", 18, "Artisan sourdough loaf"),
                    ],
                    "Pastries": [
                        ("Basbousa", 20, "Sweet semolina cake with syrup"),
                        ("Konafa", 35, "Shredded pastry with nuts"),
                        ("Baklava", 25, "Layered pastry with honey"),
                        ("Ma'amoul", 30, "Date-filled cookies"),
                        ("Qatayef", 28, "Stuffed pancakes with cream"),
                    ],
                    "Cakes": [
                        ("Chocolate Cake", 180, "Rich chocolate layer cake"),
                        ("Vanilla Sponge", 150, "Light vanilla cake"),
                        ("Red Velvet", 220, "Classic red velvet cake"),
                        ("Carrot Cake", 200, "Moist carrot cake with cream cheese"),
                    ],
                },
            },
        }

        # Track used names to avoid duplicates
        used_names = set()
        shops_created = 0
        products_created = 0

        categories = list(shop_data.keys())

        for i in range(num_shops):
            # Select category (ensure good distribution)
            category = categories[i % len(categories)]
            category_info = shop_data[category]

            # Generate unique shop name
            attempts = 0
            shop_name = None
            while attempts < 50:  # Prevent infinite loop
                base_name = random.choice(category_info["base_names"])
                suffix = random.choice(category_info["suffixes"])
                location = random.choice(category_info["locations"])

                # Try different naming patterns
                patterns = [
                    f"{base_name} {suffix}",
                    f"{base_name} {location}",
                    f"{location} {base_name}",
                    f"{base_name} {suffix} - {location}",
                    f"{base_name}",
                ]

                potential_name = random.choice(patterns)

                if potential_name not in used_names:
                    shop_name = potential_name
                    used_names.add(shop_name)
                    break

                attempts += 1

            # Fallback if we couldn't generate unique name
            if shop_name is None:
                shop_name = f"Shop {i+1} - {random.choice(category_info['base_names'])}"
                used_names.add(shop_name)

            # Create shop
            shop = Shop.objects.create(
                name=shop_name,
                address=f"{random.choice(category_info['locations'])}, Cairo",
                description=random.choice(category_info["descriptions"]),
                category=category,
            )
            shops_created += 1

            # Create products for this shop with unique names within the shop
            products_for_shop = random.randint(10, 20)
            product_categories = list(category_info["products"].keys())

            # Track used product names for this specific shop
            used_product_names_in_shop = set()

            # Create a pool of all available products for this category
            all_products = []
            for prod_cat, prod_list in category_info["products"].items():
                for product in prod_list:
                    all_products.append((prod_cat, product))

            # Shuffle to get random selection
            random.shuffle(all_products)

            products_added = 0
            for prod_cat, base_product in all_products:
                if products_added >= products_for_shop:
                    break

                product_name = base_product[0]
                base_price = base_product[1]
                description = base_product[2]

                # Ensure unique product name within this shop
                final_product_name = product_name
                name_variant = 1

                while final_product_name in used_product_names_in_shop:
                    # Add variations to make unique
                    variations = [
                        f"Special {product_name}",
                        f"Premium {product_name}",
                        f"Deluxe {product_name}",
                        f"Classic {product_name}",
                        f"House {product_name}",
                        f"Chef's {product_name}",
                        f"Traditional {product_name}",
                        f"Signature {product_name}",
                        f"Large {product_name}",
                        f"Family {product_name}",
                    ]

                    if name_variant <= len(variations):
                        final_product_name = variations[name_variant - 1]
                    else:
                        final_product_name = (
                            f"{product_name} #{name_variant - len(variations)}"
                        )

                    name_variant += 1

                used_product_names_in_shop.add(final_product_name)

                # Adjust price for variations
                if final_product_name != product_name:
                    price_multiplier = random.uniform(1.1, 1.5)
                    final_price = int(base_price * price_multiplier)
                else:
                    final_price = base_price

                # Create product
                Product.objects.create(
                    shop=shop,
                    name=final_product_name,
                    price=final_price,
                    description=description,
                    category=prod_cat,
                )
                products_created += 1
                products_added += 1

            self.stdout.write(
                f"Created shop: {shop.name} with {products_added} unique products"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {shops_created} shops and {products_created} products!"
            )
        )

        # Display summary by category
        self.stdout.write("\nSummary by category:")
        for category in categories:
            count = Shop.objects.filter(category=category).count()
            self.stdout.write(f"  {category}: {count} shops")
