-- schema.sql
-- SQL结构化查询语言(Structured Query Language)
drop database if exists kafclub;

create database kafclub;

use kafclub;

drop user if exists 'www-data'@'localhost';

-- CREATE USER  'user_name'@'host'  IDENTIFIED BY  'password';
create user 'www-data'@'localhost' identified by 'www-data';

-- alter user 'www-data'@'localhost' identified with mysql_native_password by 'www-data';本语句可以修改root密码
grant SELECT,INSERT,UPDATE,DELETE on kafclub.* to 'www-data'@'localhost';
-- 用root密码执行grant授权命令
-- mysql中 数据库、表、索引、列和别名用的是引用符是反引号backquote `
create table users (
    `id` varchar(50) not null,
    `email` varchar(50) not null,
    `passwd` varchar(50) not null,
    `admin` bool not null,
    `name` varchar(50) not null,
    `image` varchar(500) not null,
    `created_at` real not null,
    unique key `idx_email` (`email`),
    key `idx_created_at` (`created_at`),
    primary key (`id`)
) engine=innodb default charset=utf8;

create table blogs (
    `id` varchar(50) not null,
    `user_id` varchar(50) not null,
    `user_name` varchar(50) not null,
    `user_image` varchar(500) not null,
    `name` varchar(50) not null,
    `summary` varchar(200) not null,
    `content` mediumtext not null,
    `created_at` real not null,
    key `idx_created_at` (`created_at`),
    primary key (`id`)
) engine=innodb default charset=utf8;

create table comments (
    `id` varchar(50) not null,
    `blog_id` varchar(50) not null,
    `user_id` varchar(50) not null,
    `user_name` varchar(50) not null,
    `user_image` varchar(500) not null,
    `content` mediumtext not null,
    `created_at` real not null,
    key `idx_created_at` (`created_at`),
    primary key (`id`)
) engine=innodb default charset=utf8;