"""Génère un petit jeu de données SYNTHÉTIQUE au format Olist, pour tester le pipeline sans télécharger Kaggle.

Les données sont inventées : elles servent uniquement à vérifier que le code fonctionne.
Elles contiennent volontairement des cas difficiles (BOM, commentaires sur plusieurs lignes,
review_id en double, commandes non livrées, catégories sans traduction...).

Utilisation : python tests/make_fixtures.py
"""
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

OUT = Path(__file__).parent / "fixtures"
random.seed(42)

STATES = ["SP", "RJ", "MG", "BA", "RS"]
CITIES = {"SP": "sao paulo", "RJ": "rio de janeiro", "MG": "belo horizonte", "BA": "salvador", "RS": "porto alegre"}
CATEGORIES = [("beleza_saude", "health_beauty"), ("informatica_acessorios", "computers_accessories"),
              ("esporte_lazer", "sports_leisure"), ("moveis_decoracao", "furniture_decor")]


def write(name, header, rows, bom=False):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / name, "w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def fmt(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""


# --- clients : 40 personnes, certaines avec deux customer_id (donc deux commandes)
persons = [f"person{i:03d}" for i in range(40)]
customers, customer_of_person = [], {}
for i, p in enumerate(persons):
    state = STATES[i % len(STATES)]
    cid = f"cust{i:03d}a"
    customers.append([cid, p, 1000 + i, CITIES[state], state])
    customer_of_person[p] = [cid]
    if i % 5 == 0:
        cid2 = f"cust{i:03d}b"
        customers.append([cid2, p, 1000 + i, CITIES[state], state])
        customer_of_person[p].append(cid2)
write("olist_customers_dataset.csv",
      ["customer_id", "customer_unique_id", "customer_zip_code_prefix", "customer_city", "customer_state"], customers)

# --- vendeurs
sellers = [[f"seller{i:02d}", 2000 + i, CITIES[STATES[i % 5]], STATES[i % 5]] for i in range(8)]
write("olist_sellers_dataset.csv", ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"], sellers)

# --- produits : un sans catégorie, un dont la catégorie n'a pas de traduction
products = []
for i in range(25):
    cat = CATEGORIES[i % len(CATEGORIES)][0]
    products.append([f"prod{i:03d}", cat, 40, 300, random.randint(1, 5), f"{random.randint(100, 3000)}.0", 20, 10, 15])
products.append(["prod_nocat", "", "", "", "", "", "", "", ""])
products.append(["prod_notrad", "pc_gamer", 30, 200, 2, "800.0", 30, 20, 25])
write("olist_products_dataset.csv",
      ["product_id", "product_category_name", "product_name_lenght", "product_description_lenght",
       "product_photos_qty", "product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"], products)
write("product_category_name_translation.csv", ["product_category_name", "product_category_name_english"],
      [list(c) for c in CATEGORIES], bom=True)   # le vrai fichier Olist commence par un BOM

# --- commandes
orders, items, payments, reviews = [], [], [], []
base = datetime(2017, 1, 5)
order_no = 0
for p in persons:
    for cid in customer_of_person[p]:
        order_no += 1
        oid = f"order{order_no:04d}"
        purchase = base + timedelta(days=random.randint(0, 400), hours=random.randint(0, 23))
        estimated = purchase + timedelta(days=random.randint(10, 20))
        status, delivered = "delivered", purchase + timedelta(days=random.randint(5, 25))
        if order_no % 11 == 0:
            status, delivered = "shipped", None                       # pas encore livrée
        if order_no % 17 == 0:
            status, delivered = "delivered", None                     # livrée mais sans date (anomalie réelle)
        orders.append([oid, cid, status, fmt(purchase), fmt(purchase + timedelta(hours=2)),
                       fmt(purchase + timedelta(days=2)), fmt(delivered), fmt(estimated)])

        total = 0.0
        for k in range(1, random.randint(1, 3) + 1):
            price = round(random.uniform(15, 300), 2)
            freight = round(random.uniform(5, 40), 2)
            total += price + freight
            prod = random.choice(products)[0]
            seller = random.choice(sellers)[0]
            items.append([oid, k, prod, seller, fmt(purchase + timedelta(days=3)), price, freight])
        n_pay = 2 if order_no % 6 == 0 else 1
        for s in range(1, n_pay + 1):
            payments.append([oid, s, random.choice(["credit_card", "boleto", "voucher"]),
                             random.randint(1, 6), round(total / n_pay, 2)])
        score = random.choice([1, 2, 3, 4, 4, 5, 5, 5])
        comment = "Produto ótimo, chegou rápido" if order_no % 3 == 0 else ""
        if order_no % 7 == 0:
            comment = 'Linha 1\nLinha 2 avec "guillemets", virgule'      # commentaire sur plusieurs lignes
        reviews.append([f"rev{order_no:04d}", oid, score, "", comment,
                        fmt(purchase + timedelta(days=12)), fmt(purchase + timedelta(days=13))])

# review_id en double : le même avis apparaît sur deux commandes (cas réel du jeu de données)
reviews.append(["rev0001", orders[1][0], 4, "", "", fmt(base + timedelta(days=30)), fmt(base + timedelta(days=31))])

write("olist_orders_dataset.csv",
      ["order_id", "customer_id", "order_status", "order_purchase_timestamp", "order_approved_at",
       "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date"], orders)
write("olist_order_items_dataset.csv",
      ["order_id", "order_item_id", "product_id", "seller_id", "shipping_limit_date", "price", "freight_value"], items)
write("olist_order_payments_dataset.csv",
      ["order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value"], payments)
write("olist_order_reviews_dataset.csv",
      ["review_id", "order_id", "review_score", "review_comment_title", "review_comment_message",
       "review_creation_date", "review_answer_timestamp"], reviews)
print(f"{len(orders)} commandes, {len(items)} articles, {len(payments)} paiements, {len(reviews)} avis -> {OUT}")
