
SELECT d.year_month,
       COUNT(DISTINCT f.order_id)                                     AS commandes,
       ROUND(SUM(f.item_total), 2)                                    AS chiffre_affaires,
       ROUND(SUM(f.item_total) / COUNT(DISTINCT f.order_id), 2)       AS panier_moyen
FROM dwh.fact_order_items f
JOIN dwh.dim_date d ON d.date_id = f.purchase_date_id
WHERE f.order_status = 'delivered'
GROUP BY d.year_month
ORDER BY d.year_month;

-- query: Top 10 des catégories par chiffre d'affaires
SELECT p.category_en AS categorie,
       COUNT(*)                        AS articles_vendus,
       ROUND(SUM(f.price), 2)          AS chiffre_affaires
FROM dwh.fact_order_items f
JOIN dwh.dim_product p ON p.product_key = f.product_key
WHERE f.order_status = 'delivered'
GROUP BY p.category_en
ORDER BY chiffre_affaires DESC
LIMIT 10;

-- query: Taux de commandes livrées en retard par état du client
WITH commandes AS (
    SELECT order_id, customer_key, BOOL_OR(is_late) AS en_retard
    FROM dwh.fact_order_items
    WHERE delivered_date_id IS NOT NULL AND is_late IS NOT NULL
    GROUP BY order_id, customer_key
)
SELECT c.state AS etat_client,
       COUNT(*)                                                        AS commandes_livrees,
       ROUND(100.0 * AVG(CASE WHEN cmd.en_retard THEN 1 ELSE 0 END), 1) AS taux_retard_pct
FROM commandes cmd
JOIN dwh.dim_customer c ON c.customer_key = cmd.customer_key
GROUP BY c.state
ORDER BY taux_retard_pct DESC, commandes_livrees DESC
LIMIT 10;

-- query: Délai de livraison moyen par mois d'achat (en jours)
SELECT d.year_month,
       ROUND(AVG(f.delivery_days), 1) AS delai_moyen_jours
FROM dwh.fact_order_items f
JOIN dwh.dim_date d ON d.date_id = f.purchase_date_id
WHERE f.delivery_days IS NOT NULL
GROUP BY d.year_month
ORDER BY d.year_month;

-- query: Répartition des paiements par moyen de paiement
SELECT payment_type AS moyen_paiement,
       COUNT(*)                                                  AS paiements,
       ROUND(SUM(payment_value), 2)                              AS montant_total,
       ROUND(100.0 * SUM(payment_value) / SUM(SUM(payment_value)) OVER (), 1) AS part_pct
FROM dwh.fact_payments
GROUP BY payment_type
ORDER BY montant_total DESC;

-- query: Note moyenne des vendeurs les mieux notés (au moins 3 avis)
WITH commande_vendeur AS (
    SELECT DISTINCT order_id, seller_key FROM dwh.fact_order_items
)
SELECT s.seller_id,
       COUNT(*)                          AS avis,
       ROUND(AVG(r.review_score), 2)     AS note_moyenne
FROM dwh.fact_reviews r
JOIN commande_vendeur cv ON cv.order_id = r.order_id
JOIN dwh.dim_seller s    ON s.seller_key = cv.seller_key
GROUP BY s.seller_id
HAVING COUNT(*) >= 3
ORDER BY note_moyenne DESC, avis DESC
LIMIT 10;

-- query: Part des clients qui ont passé plus d'une commande
WITH par_client AS (
    SELECT customer_key, COUNT(DISTINCT order_id) AS commandes
    FROM dwh.fact_order_items
    GROUP BY customer_key
)
SELECT COUNT(*)                                                     AS clients,
       COUNT(*) FILTER (WHERE commandes > 1)                        AS clients_fideles,
       ROUND(100.0 * COUNT(*) FILTER (WHERE commandes > 1) / COUNT(*), 1) AS part_clients_fideles_pct
FROM par_client;

-- query: Effet d'un retard de livraison sur la note moyenne
WITH retard_commande AS (
    SELECT order_id, BOOL_OR(is_late) AS en_retard
    FROM dwh.fact_order_items
    WHERE delivered_date_id IS NOT NULL
    GROUP BY order_id
)
SELECT CASE WHEN rc.en_retard THEN 'en retard' ELSE 'à l''heure' END AS livraison,
       COUNT(*)                          AS avis,
       ROUND(AVG(r.review_score), 2)     AS note_moyenne
FROM dwh.fact_reviews r
JOIN retard_commande rc ON rc.order_id = r.order_id
GROUP BY rc.en_retard
ORDER BY livraison;

-- query: Chiffre d'affaires par état du client (top 10)
SELECT c.state AS etat_client,
       ROUND(SUM(f.item_total), 2) AS chiffre_affaires,
       COUNT(DISTINCT f.order_id)  AS commandes
FROM dwh.fact_order_items f
JOIN dwh.dim_customer c ON c.customer_key = f.customer_key
WHERE f.order_status = 'delivered'
GROUP BY c.state
ORDER BY chiffre_affaires DESC
LIMIT 10;
