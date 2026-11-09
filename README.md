# OlistEntrepot

Un entrepôt de données en étoile construit avec SQL à partir des ventes d'une boutique en ligne brésilienne (jeu de données public Olist), et un tableau de bord Power BI pour analyser les ventes et les livraisons.

Un script Python charge les fichiers CSV dans PostgreSQL, construit le modèle, vérifie les données et exporte les tables pour Power BI.

J'ai fait ce projet pour m'entraîner à la modélisation dimensionnelle, au SQL d'analyse et à la construction d'indicateurs.

## Les données

Le jeu de données s'appelle Brazilian E-Commerce Public Dataset by Olist et il est sur Kaggle. Il contient environ 100 000 commandes passées entre 2016 et 2018, réparties en plusieurs fichiers : clients, commandes, articles, paiements, avis, produits et vendeurs. Les données sont anonymisées.

Sur la page Kaggle, la licence indiquée est CC BY-NC-SA 4.0. Les fichiers ne sont pas dans ce dépôt, il faut les télécharger.

## Le modèle

Quatre dimensions :

- dim_date : un jour par ligne
- dim_customer : un client par ligne
- dim_product : un produit par ligne, avec sa catégorie en portugais et en anglais
- dim_seller : un vendeur par ligne

Trois tables de faits :

- fact_order_items : un article commandé par ligne, avec le prix, les frais de port, le délai de livraison et le retard par rapport à la date prévue
- fact_payments : un paiement par ligne, car une commande peut être payée en plusieurs fois
- fact_reviews : un avis par ligne, avec sa note de 1 à 5

## Comment mon projet marche

Le script src/pipeline.py fait cinq étapes :

1. Il recrée l'entrepôt de zéro.
2. Il charge les fichiers CSV tels quels dans un schéma staging, avec la commande COPY de PostgreSQL. Tout est en texte à cette étape.
3. Il construit les dimensions en SQL (sql/10_dimensions.sql).
4. Il construit les tables de faits en SQL (sql/20_facts.sql).
5. Il lance les contrôles de qualité (sql/quality_checks.sql).

Avec l'option --export, il écrit ensuite les tables en CSV dans le dossier exports, pour les importer dans Power BI.

Quelques choix que j'ai faits :

- Un client, c'est un customer_unique_id. Dans ce jeu de données, customer_id change à chaque commande.
- Le grain de la table de ventes est l'article commandé, pour pouvoir analyser par produit, par vendeur ou par catégorie.
- Un même avis peut apparaître sur plusieurs commandes. J'ai supprimé les doublons exacts et ajouté une clé propre à la table.
- Quand la traduction d'une catégorie manque, je garde le nom portugais. Quand la catégorie manque, je mets inconnu.
- Je n'ai pas chargé le fichier de géolocalisation (environ un million de lignes), le modèle n'en a pas besoin.

## Contrôles de qualité

Il y a huit contrôles. Cinq sont bloquants et arrêtent le pipeline : lignes perdues entre le staging et les faits, article en double, prix négatif, note hors de 1 à 5, paiement négatif.

Trois sont de simples avertissements : commande livrée sans date de livraison, livraison avant la date d'achat, écart entre le total payé et le total des articles. Ces anomalies existent dans les données d'origine, je les signale sans les corriger.

## Requêtes d'analyse

Le fichier sql/analytics.sql contient neuf requêtes : chiffre d'affaires et panier moyen par mois, catégories les plus vendues, commandes en retard par état, délai de livraison par mois, moyens de paiement, vendeurs les mieux notés, clients qui commandent plusieurs fois, effet d'un retard sur la note, et chiffre d'affaires par état. Pour les afficher :

```
python -m src.report
```

## Limites

- Les données datent de 2016 à 2018 et concernent un seul pays. Elles servent à montrer une méthode, pas à décrire le commerce en ligne d'aujourd'hui.
- Les avis et les paiements sont rattachés à la commande, pas à l'article. Quand une commande a plusieurs vendeurs, sa note compte pour chacun d'eux dans l'analyse par vendeur.
- Le taux de retard ne porte que sur les commandes livrées qui ont une date de livraison et une date prévue.
- Dans Power BI, la note moyenne porte sur tous les avis, pas seulement sur les commandes livrées.
- Le tableau de bord est construit sur des exports CSV, il ne se met pas à jour tout seul.

## Technologies

SQL, PostgreSQL, Python, Docker, Power BI, pytest.

## Auteur

Cherif Khalla Abdel Djelil, étudiant en informatique de gestion, option science des données.
