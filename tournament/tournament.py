#!/usr/bin/env python
#
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2


def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def deleteMatches():
    """Remove all the match records from the database."""
    con = connect()
    if con:
        cursor = con.cursor()
        cursor.execute("DELETE FROM match")
        con.commit()
        con.close()


def deletePlayers():
    """Remove all the player records from the database."""
    con = connect()
    if con:
        cursor = con.cursor()
        cursor.execute("DELETE FROM player")
        con.commit()
        con.close()

def deleteTournaments():
    """Remove all tournament records from the database."""
    con = connect()
    if con:
        cursor = con.cursor()
        cursor.execute("DELETE FROM tournament")
        con.commit()
        con.close()


def countPlayers():
    """Returns the number of players currently registered."""
    con = connect()
    if con:
        cursor = con.cursor()
        cursor.execute("SELECT count(*) FROM player")
        result = cursor.fetchone()
        con.close()
        return int(result[0])
    return


def registerPlayer(name):
    """Adds a player to the tournament database.

    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)

    Args:
      name: the player's full name (need not be unique).
    """
    con = connect()
    if con:
        cursor = con.cursor()
        cursor.execute("INSERT INTO player (name) VALUES (%s)",
                       (name,))
        con.commit()
        con.close()


def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    con = connect()
    if con:
        cursor = con.cursor()
        cursor.execute("SELECT * FROM playerranking ORDER BY TOTAL_WINS DESC")

        results = list()
        for row in cursor.fetchall():
            results.append((str(row[0]), str(row[1]), row[2], row[3]))
        con.close()
        return results


def reportMatch(winner, loser):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
    con = connect()
    if con:
        cursor = con.cursor()
        cursor.execute("INSERT INTO match (winner, loser) VALUES (%s, %s)",
                       (winner, loser,))
        con.commit()
        con.close()


def swissPairings():
    """Returns a list of pairs of players for the next round of a match.

    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.

    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
    con = connect()
    if con:
        cur = con.cursor()
        pairings = list()
        players = playerStandings()

        while len(players) > 1:
            player = players[0]
            opponent = ()

            for i in range(1, len(players)):
                opponent = players[i]

                foundMatch = cur.execute("SELECT count(*) FROM match WHERE winner = %s and loser = %s OR winner = %s and loser = %s",
                 (player[0], opponent[0], opponent[0], player[0],))

                if not foundMatch:
                    pairings.append((player[0], player[1], opponent[0], opponent[1]))
                    break

            players.remove(player)
            players.remove(opponent)

        con.close()
        return pairings






