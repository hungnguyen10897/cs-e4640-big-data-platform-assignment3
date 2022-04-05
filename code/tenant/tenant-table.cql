USE mysimbdp;

DROP TABLE IF EXISTS aggregated_reviews;

CREATE TABLE aggregated_reviews (
  product_id TEXT,
  avg_star_rating INT,
  sum_helpful_votes INT,
  sum_total_votes INT,
  number_of_reviews INT,
  review_date TEXT,
  PRIMARY KEY (product_id)
);
