CREATE TABLE dwh.dim_date AS
WITH bornes AS (
    SELECT
        LEAST(
            MIN(NULLIF(order_purchase_timestamp, '')::timestamp),
            MIN(NULLIF(order_estimated_delivery_date, '')::timestamp)
        )::date AS debut,
        GREATEST(
            MAX(NULLIF(order_purchase_timestamp, '')::timestamp),
            MAX(NULLIF(order_delivered_customer_date, '')::timestamp),
            MAX(NULLIF(order_estimated_delivery_date, '')::timestamp)
        )::date AS fin
    FROM staging.orders
)
SELECT
    to_char(d, 'YYYYMMDD')::int          AS date_id,
    d::date                              AS full_date,
    EXTRACT(year    FROM d)::smallint    AS year,
    EXTRACT(quarter FROM d)::smallint    AS quarter,
    EXTRACT(month   FROM d)::smallint    AS month,
    to_char(d, 'YYYY-MM')                AS year_month,
    EXTRACT(day     FROM d)::smallint    AS day,
    EXTRACT(isodow  FROM d)::smallint    AS day_of_week,   -- 1 = lundi ... 7 = dimanche
    (EXTRACT(isodow FROM d) >= 6)        AS is_weekend
FROM bornes, generate_series(bornes.debut, bornes.fin, interval '1 day') AS g(d);

ALTER TABLE dwh.dim_date ADD PRIMARY KEY (date_id);

-- Dimension client : un client = un customer_unique_id.
-- Dans le jeu de données, customer_id change à chaque commande, customer_unique_id identifie la personne.
CREATE TABLE dwh.dim_customer AS
SELECT
    ROW_NUMBER() OVER (ORDER BY customer_unique_id)::int AS customer_key,
    customer_unique_id,
    customer_city            AS city,
    customer_state           AS state,
    customer_zip_code_prefix AS zip_prefix
FROM (
    SELECT DISTINCT ON (customer_unique_id)
           customer_unique_id, customer_city, customer_state, customer_zip_code_prefix
    FROM staging.customers
    ORDER BY customer_unique_id, customer_id
) c;

ALTER TABLE dwh.dim_customer ADD PRIMARY KEY (customer_key);
ALTER TABLE dwh.dim_customer ADD UNIQUE (customer_unique_id);

-- Dimension produit, avec la catégorie en portugais et en anglais.
-- Quand la traduction manque, on garde le nom portugais ; quand la catégorie manque, 'inconnu'.
CREATE TABLE dwh.dim_product AS
SELECT
    ROW_NUMBER() OVER (ORDER BY p.product_id)::int AS product_key,
    p.product_id,
    COALESCE(NULLIF(p.product_category_name, ''), 'inconnu')       AS category_pt,
    COALESCE(NULLIF(t.product_category_name_english, ''),
             NULLIF(p.product_category_name, ''), 'unknown')       AS category_en,
    NULLIF(p.product_weight_g, '')::numeric                        AS weight_g,
    NULLIF(p.product_photos_qty, '')::numeric::int                 AS photos_qty
FROM staging.products p
LEFT JOIN staging.category_translation t
       ON t.product_category_name = p.product_category_name;

ALTER TABLE dwh.dim_product ADD PRIMARY KEY (product_key);
ALTER TABLE dwh.dim_product ADD UNIQUE (product_id);

-- Dimension vendeur.
CREATE TABLE dwh.dim_seller AS
SELECT
    ROW_NUMBER() OVER (ORDER BY seller_id)::int AS seller_key,
    seller_id,
    seller_city            AS city,
    seller_state           AS state,
    seller_zip_code_prefix AS zip_prefix
FROM staging.sellers;

ALTER TABLE dwh.dim_seller ADD PRIMARY KEY (seller_key);
ALTER TABLE dwh.dim_seller ADD UNIQUE (seller_id);
