

CREATE TABLE dwh.fact_order_items AS
WITH commandes AS (
    SELECT
        o.order_id,
        o.order_status,
        sc.customer_unique_id,
        NULLIF(o.order_purchase_timestamp, '')::timestamp        AS achat,
        NULLIF(o.order_delivered_customer_date, '')::timestamp   AS livraison,
        NULLIF(o.order_estimated_delivery_date, '')::timestamp   AS livraison_prevue
    FROM staging.orders o
    JOIN staging.customers sc ON sc.customer_id = o.customer_id
)
SELECT
    oi.order_id,
    oi.order_item_id::int                                           AS order_item_id,
    c.customer_key,
    p.product_key,
    s.seller_key,
    to_char(cmd.achat, 'YYYYMMDD')::int                             AS purchase_date_id,
    to_char(cmd.livraison, 'YYYYMMDD')::int                         AS delivered_date_id,
    to_char(cmd.livraison_prevue, 'YYYYMMDD')::int                  AS estimated_date_id,
    cmd.order_status,
    oi.price::numeric(12, 2)                                        AS price,
    oi.freight_value::numeric(12, 2)                                AS freight_value,
    (oi.price::numeric + oi.freight_value::numeric)::numeric(12, 2) AS item_total,
    CASE WHEN cmd.livraison IS NOT NULL
         THEN cmd.livraison::date - cmd.achat::date END             AS delivery_days,
    CASE WHEN cmd.livraison IS NOT NULL AND cmd.livraison_prevue IS NOT NULL
         THEN cmd.livraison::date - cmd.livraison_prevue::date END  AS delay_days,
    CASE WHEN cmd.livraison IS NOT NULL AND cmd.livraison_prevue IS NOT NULL
         THEN cmd.livraison::date > cmd.livraison_prevue::date END  AS is_late
FROM staging.order_items oi
JOIN commandes cmd      ON cmd.order_id = oi.order_id
JOIN dwh.dim_customer c ON c.customer_unique_id = cmd.customer_unique_id
JOIN dwh.dim_product p  ON p.product_id = oi.product_id
JOIN dwh.dim_seller s   ON s.seller_id = oi.seller_id;

ALTER TABLE dwh.fact_order_items ADD PRIMARY KEY (order_id, order_item_id);
ALTER TABLE dwh.fact_order_items ADD FOREIGN KEY (customer_key)      REFERENCES dwh.dim_customer (customer_key);
ALTER TABLE dwh.fact_order_items ADD FOREIGN KEY (product_key)       REFERENCES dwh.dim_product (product_key);
ALTER TABLE dwh.fact_order_items ADD FOREIGN KEY (seller_key)        REFERENCES dwh.dim_seller (seller_key);
ALTER TABLE dwh.fact_order_items ADD FOREIGN KEY (purchase_date_id)  REFERENCES dwh.dim_date (date_id);
ALTER TABLE dwh.fact_order_items ADD FOREIGN KEY (delivered_date_id) REFERENCES dwh.dim_date (date_id);
ALTER TABLE dwh.fact_order_items ADD FOREIGN KEY (estimated_date_id) REFERENCES dwh.dim_date (date_id);
CREATE INDEX ON dwh.fact_order_items (customer_key);
CREATE INDEX ON dwh.fact_order_items (product_key);
CREATE INDEX ON dwh.fact_order_items (seller_key);
CREATE INDEX ON dwh.fact_order_items (purchase_date_id);

CREATE TABLE dwh.fact_payments AS
SELECT
    pay.order_id,
    pay.payment_sequential::int                     AS payment_sequential,
    pay.payment_type,
    pay.payment_installments::int                   AS installments,
    pay.payment_value::numeric(12, 2)               AS payment_value,
    to_char(NULLIF(o.order_purchase_timestamp, '')::timestamp, 'YYYYMMDD')::int AS purchase_date_id
FROM staging.order_payments pay
JOIN staging.orders o ON o.order_id = pay.order_id;

ALTER TABLE dwh.fact_payments ADD PRIMARY KEY (order_id, payment_sequential);
ALTER TABLE dwh.fact_payments ADD FOREIGN KEY (purchase_date_id) REFERENCES dwh.dim_date (date_id);

-- Un même review_id peut apparaître pour plusieurs commandes dans le jeu de données :
-- on dédoublonne les lignes strictement identiques et on ajoute une clé de substitution.
CREATE TABLE dwh.fact_reviews AS
SELECT
    ROW_NUMBER() OVER (ORDER BY review_id, order_id)::int AS review_key,
    review_id,
    order_id,
    review_score::smallint                                AS review_score,
    to_char(NULLIF(review_creation_date, '')::timestamp, 'YYYYMMDD')::int AS review_date_id
FROM (
    SELECT DISTINCT review_id, order_id, review_score, review_creation_date
    FROM staging.order_reviews
) r;

ALTER TABLE dwh.fact_reviews ADD PRIMARY KEY (review_key);
CREATE INDEX ON dwh.fact_reviews (order_id);
