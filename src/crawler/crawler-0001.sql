create table if not exists SeenCoverage(article_url_sha256 varchar(64) primary key, publisher text not null, title text not null);
