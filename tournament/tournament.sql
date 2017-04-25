-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

CREATE TABLE tournament (
id SERIAL PRIMARY KEY,
name varchar(64) NOT NULL
);

CREATE TABLE player (
id SERIAL PRIMARY KEY,
name varchar(64) NOT NULL
);

CREATE TABLE match (
match_id SERIAL PRIMARY KEY,
winner INTEGER NOT NULL REFERENCES player (id),
loser INTEGER NOT NULL REFERENCES player (id)
);

CREATE VIEW playerranking AS
    SELECT player.id, player.name,
    (SELECT Count(winner) FROM match WHERE WINNER=PLAYER.ID) AS TOTAL_WINS,
    (SELECT Count(*) FROM match WHERE LOSER=PLAYER.ID OR WINNER=PLAYER.ID) AS TOTAL_MATCHES
    FROM player
    ORDER BY TOTAL_WINS DESC;
