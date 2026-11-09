
SELECT ABS((SELECT COUNT(*) FROM dwh.fact_order_items) - (SELECT COUNT(*) FROM staging.order_items));

-- check: grain unique (commande, article) | error
SELECT COUNT(*) - COUNT(DISTINCT (order_id, order_item_id)) FROM dwh.fact_order_items;

-- check: aucun prix ou frais de port négatif | error
SELECT COUNT(*) FROM dwh.fact_order_items WHERE price < 0 OR freight_value < 0;

-- check: note d'avis comprise entre 1 et 5 | error
SELECT COUNT(*) FROM dwh.fact_reviews WHERE review_score IS NULL OR review_score NOT BETWEEN 1 AND 5;

-- check: aucun paiement négatif | error
SELECT COUNT(*) FROM dwh.fact_payments WHERE payment_value < 0;

-- check: commandes livrées sans date de livraison | warning
SELECT COUNT(*) FROM dwh.fact_order_items WHERE order_status = 'delivered' AND delivered_date_id IS NULL;

-- check: livraison avant la date d'achat | warning
SELECT COUNT(*) FROM dwh.fact_order_items WHERE delivery_days < 0;

-- check: commandes dont le total payé diffère du total des articles de plus de 1 | warning
SELECT COUNT(*) FROM (
    SELECT i.order_id
    FROM (SELECT order_id, SUM(item_total) AS total FROM dwh.fact_order_items GROUP BY order_id) i
    JOIN (SELECT order_id, SUM(payment_value) AS paye FROM dwh.fact_payments GROUP BY order_id) p USING (order_id)
    WHERE ABS(i.total - p.paye) > 1
) ecarts;
