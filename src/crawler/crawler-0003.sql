CREATE TABLE IF NOT EXISTS CrawlerToRelevancy ( id_number INT AUTO_INCREMENT PRIMARY KEY, publisher TEXT NOT NULL, title TEXT NOT NULL, article_text LONGTEXT NOT NULL, link TEXT NOT NULL UNIQUE, constraint u_global unique (publisher, title) );
