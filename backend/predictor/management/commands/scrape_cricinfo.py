"""
ESPNcricinfo Scraper for Dream11 Team Predictor

This script scrapes cricket data from ESPNcricinfo for use in the Dream11 Team Predictor application.
It collects match results, player statistics, and venue information.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
import sqlite3
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from predictor.models import Team, Player, Venue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("espncricinfo_scraper.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ESPNCricinfoScraper:
    """
    A class to scrape cricket data from ESPNcricinfo.
    """

    def __init__(self, base_dir=None, delay_range=(1, 3)):
        """
        Initialize the scraper.
        
        Args:
            base_dir: Directory to save data files
            delay_range: Range for random delay between requests (min, max) in seconds
        """
        self.base_dir = base_dir if base_dir else os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.base_dir, 'cricket_data')
        self.delay_range = delay_range
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        
        # Create data directory if it doesn't exist
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        # Connect to SQLite database
        self.db_path = os.path.join(self.data_dir, 'cricket_stats.db')
        self._setup_database()
    
    def _setup_database(self):
        """Set up the SQLite database with necessary tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            short_name TEXT,
            cricinfo_id TEXT UNIQUE
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS venues (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            city TEXT,
            country TEXT,
            cricinfo_id TEXT UNIQUE
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY,
            name TEXT,
            team_id INTEGER,
            role TEXT,
            batting_average REAL,
            bowling_average REAL,
            recent_form REAL,
            cricinfo_id TEXT UNIQUE,
            FOREIGN KEY (team_id) REFERENCES teams (id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY,
            cricinfo_id TEXT UNIQUE,
            date TEXT,
            team1_id INTEGER,
            team2_id INTEGER,
            venue_id INTEGER,
            winner_id INTEGER,
            match_type TEXT,
            series_id TEXT,
            FOREIGN KEY (team1_id) REFERENCES teams (id),
            FOREIGN KEY (team2_id) REFERENCES teams (id),
            FOREIGN KEY (venue_id) REFERENCES venues (id),
            FOREIGN KEY (winner_id) REFERENCES teams (id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS player_performances (
            id INTEGER PRIMARY KEY,
            player_id INTEGER,
            match_id INTEGER,
            runs INTEGER,
            balls_faced INTEGER,
            fours INTEGER,
            sixes INTEGER,
            wickets INTEGER,
            overs_bowled REAL,
            runs_conceded INTEGER,
            fantasy_points REAL,
            FOREIGN KEY (player_id) REFERENCES players (id),
            FOREIGN KEY (match_id) REFERENCES matches (id)
        )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("Database setup complete")

    def _random_delay(self):
        """Add random delay between requests to avoid being blocked."""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
        
    def _get_soup(self, url):
        """
        Get BeautifulSoup object from URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None if request fails
        """
        try:
            logger.info(f"Fetching URL: {url}")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return BeautifulSoup(response.content, 'lxml')
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def scrape_ipl_matches(self, season_year, series_id=None):
        """
        Scrape IPL matches for a specific season.
        
        Args:
            season_year: Year of the IPL season
            series_id: Cricinfo series ID (if known)
            
        Returns:
            DataFrame of matches
        """
        if not series_id:
            # If series_id is not provided, we could try to find it, but for now, use a default format
            series_id = f"indian-premier-league-{season_year}"
            
        url = f'https://www.espncricinfo.com/series/{series_id}/match-results'
        
        soup = self._get_soup(url)
        if not soup:
            logger.error(f"Failed to get match results for IPL {season_year}")
            return pd.DataFrame()
            
        # Find all match cards
        match_elements = soup.select('div.ds-flex.ds-flex-wrap')
        matches_data = []
        
        for match_element in match_elements:
            try:
                # Extract match details
                match_link = match_element.select_one('a.ds-no-tap-higlight')
                if not match_link or 'href' not in match_link.attrs:
                    continue
                    
                match_url = f"https://www.espncricinfo.com{match_link['href']}"
                match_id = match_url.split('/')[-1]
                
                teams_elements = match_element.select('p.ds-text-tight-m')
                if len(teams_elements) < 2:
                    continue
                    
                team1 = teams_elements[0].text.strip()
                team2 = teams_elements[1].text.strip()
                
                # Extract venue and date
                info_element = match_element.select_one('div.ds-text-compact-xs')
                if not info_element:
                    continue
                    
                info_text = info_element.text.strip()
                venue = info_text.split(',')[0] if ',' in info_text else ''
                date_str = info_text.split(',')[-1].strip() if ',' in info_text else ''
                
                # Extract result
                result_element = match_element.select_one('p.ds-text-tight-s')
                result = result_element.text.strip() if result_element else 'No result'
                
                matches_data.append({
                    'match_id': match_id,
                    'team1': team1,
                    'team2': team2,
                    'venue': venue,
                    'date': date_str,
                    'result': result,
                    'match_url': match_url
                })
                
                logger.info(f"Extracted match: {team1} vs {team2} at {venue}")
                self._random_delay()
                
            except Exception as e:
                logger.error(f"Error extracting match data: {e}")
        
        matches_df = pd.DataFrame(matches_data)
        matches_df.to_csv(os.path.join(self.data_dir, f"ipl_{season_year}_matches.csv"), index=False)
        
        return matches_df
    
    def scrape_match_scorecard(self, match_url):
        """
        Scrape player statistics from a match scorecard.
        
        Args:
            match_url: URL of the match scorecard
            
        Returns:
            Tuple of (batting_data, bowling_data)
        """
        soup = self._get_soup(match_url)
        if not soup:
            logger.error(f"Failed to get scorecard for {match_url}")
            return pd.DataFrame(), pd.DataFrame()
        
        match_id = match_url.split('/')[-1]
        
        # Extract teams
        team_names = []
        team_elements = soup.select('span.ds-text-title-xs.ds-font-bold')
        for elem in team_elements:
            if elem.text.strip():
                team_names.append(elem.text.strip())
        
        if len(team_names) < 2:
            logger.warning(f"Could not find team names for match {match_id}")
            team_names = ["Team 1", "Team 2"]
        
        # Extract batting stats
        batting_data = []
        innings_elements = soup.select('div.ds-rounded-lg.ds-mt-2')
        
        for i, innings in enumerate(innings_elements[:2]):  # Only process first 2 innings
            team_batting = team_names[i] if i < len(team_names) else f"Team {i+1}"
            team_bowling = team_names[1-i] if i < len(team_names) else f"Team {2-i}"
            
            batter_elements = innings.select('table > tbody > tr')
            
            for batter_element in batter_elements:
                try:
                    cols = batter_element.select('td')
                    if len(cols) < 8:
                        continue
                    
                    # Check if this is a batsman row (has runs)
                    runs_elem = cols[2]
                    if not runs_elem or not runs_elem.text.strip().isdigit():
                        continue
                    
                    player_link = cols[0].select_one('a')
                    player_name = cols[0].text.strip()
                    player_id = player_link['href'].split('-')[-1] if player_link and 'href' in player_link.attrs else ''
                    
                    dismissal = cols[1].text.strip()
                    runs = int(cols[2].text.strip())
                    balls = int(cols[3].text.strip()) if cols[3].text.strip().isdigit() else 0
                    minutes = cols[4].text.strip()
                    fours = int(cols[5].text.strip()) if cols[5].text.strip().isdigit() else 0
                    sixes = int(cols[6].text.strip()) if cols[6].text.strip().isdigit() else 0
                    strike_rate = float(cols[7].text.strip()) if cols[7].text.strip() and cols[7].text.strip() != '-' else 0
                    
                    # Calculate fantasy points (rough approximation)
                    fantasy_points = runs + (runs * 0.5 if runs >= 50 else 0) + (runs * 0.5 if runs >= 100 else 0) + (fours * 1) + (sixes * 2)
                    
                    batting_data.append({
                        'match_id': match_id,
                        'player_name': player_name,
                        'player_id': player_id,
                        'team': team_batting,
                        'opposing_team': team_bowling,
                        'runs': runs,
                        'balls': balls,
                        'fours': fours,
                        'sixes': sixes,
                        'strike_rate': strike_rate,
                        'dismissal': dismissal,
                        'fantasy_points': fantasy_points
                    })
                    
                except Exception as e:
                    logger.error(f"Error extracting batting data: {e}")
        
        # Extract bowling stats
        bowling_data = []
        for i, innings in enumerate(innings_elements[:2]):  # Only process first 2 innings
            team_batting = team_names[i] if i < len(team_names) else f"Team {i+1}"
            team_bowling = team_names[1-i] if i < len(team_names) else f"Team {2-i}"
            
            bowling_table = innings.select('table.ds-table')
            if len(bowling_table) < 2:
                continue
                
            bowler_elements = bowling_table[1].select('tbody > tr')
            
            for bowler_element in bowler_elements:
                try:
                    cols = bowler_element.select('td')
                    if len(cols) < 10:
                        continue
                    
                    player_link = cols[0].select_one('a')
                    player_name = cols[0].text.strip()
                    player_id = player_link['href'].split('-')[-1] if player_link and 'href' in player_link.attrs else ''
                    
                    overs = float(cols[1].text.strip().replace('-', '0'))
                    maidens = int(cols[2].text.strip()) if cols[2].text.strip().isdigit() else 0
                    runs = int(cols[3].text.strip()) if cols[3].text.strip().isdigit() else 0
                    wickets = int(cols[4].text.strip()) if cols[4].text.strip().isdigit() else 0
                    economy = float(cols[5].text.strip()) if cols[5].text.strip() and cols[5].text.strip() != '-' else 0
                    dots = int(cols[6].text.strip()) if cols[6].text.strip().isdigit() else 0
                    fours = int(cols[7].text.strip()) if cols[7].text.strip().isdigit() else 0
                    sixes = int(cols[8].text.strip()) if cols[8].text.strip().isdigit() else 0
                    
                    # Calculate fantasy points (rough approximation)
                    fantasy_points = (wickets * 25) + (maidens * 8) + (dots * 0.5) - (runs * 0.5)
                    if wickets >= 3:
                        fantasy_points += 8
                    if wickets >= 5:
                        fantasy_points += 16
                    
                    bowling_data.append({
                        'match_id': match_id,
                        'player_name': player_name,
                        'player_id': player_id,
                        'team': team_bowling,
                        'opposing_team': team_batting,
                        'overs': overs,
                        'maidens': maidens,
                        'runs': runs,
                        'wickets': wickets,
                        'economy': economy,
                        'dots': dots,
                        'fours': fours,
                        'sixes': sixes,
                        'fantasy_points': fantasy_points
                    })
                    
                except Exception as e:
                    logger.error(f"Error extracting bowling data: {e}")
        
        batting_df = pd.DataFrame(batting_data)
        bowling_df = pd.DataFrame(bowling_data)
        
        # Save to CSV
        match_date = datetime.now().strftime('%Y%m%d')
        batting_df.to_csv(os.path.join(self.data_dir, f"match_{match_id}_batting_{match_date}.csv"), index=False)
        bowling_df.to_csv(os.path.join(self.data_dir, f"match_{match_id}_bowling_{match_date}.csv"), index=False)
        
        return batting_df, bowling_df
    
    def scrape_player_profile(self, player_id):
        """
        Scrape detailed player profile.
        
        Args:
            player_id: Cricinfo player ID
            
        Returns:
            Dictionary with player details
        """
        url = f'https://www.espncricinfo.com/player/player-name-{player_id}'
        
        soup = self._get_soup(url)
        if not soup:
            logger.error(f"Failed to get player profile for ID {player_id}")
            return {}
        
        player_data = {}
        
        try:
            # Get player name
            name_element = soup.select_one('h1.ds-text-title-l')
            player_data['name'] = name_element.text.strip() if name_element else 'Unknown'
            
            # Get player role
            role_element = soup.select_one('span.ds-text-typo-mid3')
            if role_element:
                role_text = role_element.text.strip().lower()
                if 'wicketkeeper' in role_text or 'keeper' in role_text:
                    player_data['role'] = 'WK'
                elif 'allrounder' in role_text:
                    player_data['role'] = 'AR'
                elif 'bowler' in role_text:
                    player_data['role'] = 'BWL'
                else:
                    player_data['role'] = 'BAT'
            else:
                player_data['role'] = 'BAT'  # Default role
                
            # Get player team
            team_element = soup.select_one('a.ds-text-typo-primary')
            player_data['team'] = team_element.text.strip() if team_element else 'Unknown'
                
            # Get basic stats
            stats_tables = soup.select('table.ds-table')
            batting_averages = {}
            bowling_averages = {}
            
            for table in stats_tables:
                # Check if this is a batting or bowling table
                header_text = ' '.join([h.text for h in table.select('thead th')])
                
                if 'batting' in header_text.lower():
                    rows = table.select('tbody tr')
                    for row in rows:
                        cols = row.select('td')
                        if len(cols) >= 5:
                            format_type = cols[0].text.strip()
                            matches = int(cols[1].text.strip()) if cols[1].text.strip().isdigit() else 0
                            innings = int(cols[2].text.strip()) if cols[2].text.strip().isdigit() else 0
                            runs = int(cols[3].text.strip()) if cols[3].text.strip().isdigit() else 0
                            average = float(cols[4].text.strip()) if cols[4].text.strip() and cols[4].text.strip() != '-' else 0
                            batting_averages[format_type] = average
                
                if 'bowling' in header_text.lower():
                    rows = table.select('tbody tr')
                    for row in rows:
                        cols = row.select('td')
                        if len(cols) >= 5:
                            format_type = cols[0].text.strip()
                            matches = int(cols[1].text.strip()) if cols[1].text.strip().isdigit() else 0
                            wickets = int(cols[3].text.strip()) if cols[3].text.strip().isdigit() else 0
                            average = float(cols[4].text.strip()) if cols[4].text.strip() and cols[4].text.strip() != '-' else 0
                            bowling_averages[format_type] = average
            
            # Prioritize T20/IPL stats if available, otherwise use other formats
            player_data['batting_average'] = (
                batting_averages.get('T20Is', 0) or 
                batting_averages.get('IPL', 0) or 
                batting_averages.get('T20s', 0) or 
                batting_averages.get('ODIs', 0) or 
                batting_averages.get('Tests', 0) or 
                0
            )
            
            player_data['bowling_average'] = (
                bowling_averages.get('T20Is', 0) or 
                bowling_averages.get('IPL', 0) or 
                bowling_averages.get('T20s', 0) or 
                bowling_averages.get('ODIs', 0) or 
                bowling_averages.get('Tests', 0) or 
                0
            )
            
            # Placeholder for recent form (would require more data)
            player_data['recent_form'] = player_data['batting_average']
            
            # Extract recent matches if available
            recent_matches_element = soup.select('div.ds-flex.ds-flex-col h3.ds-mt-3 ~ div')
            player_data['recent_matches'] = []
            
            if recent_matches_element:
                pass  # Would need to process recent matches
        
        except Exception as e:
            logger.error(f"Error extracting player data: {e}")
        
        # Save to CSV
        pd.DataFrame([player_data]).to_csv(
            os.path.join(self.data_dir, f"player_{player_id}.csv"), 
            index=False
        )
        
        return player_data
    
    def save_to_database(self, data_type, data):
        """
        Save scraped data to SQLite database.
        
        Args:
            data_type: Type of data ('teams', 'players', 'matches', etc.)
            data: DataFrame or dict of data
            
        Returns:
            Boolean success status
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            if data_type == 'teams' and isinstance(data, pd.DataFrame):
                data.to_sql('teams', conn, if_exists='append', index=False)
                
            elif data_type == 'players' and isinstance(data, pd.DataFrame):
                data.to_sql('players', conn, if_exists='append', index=False)
                
            elif data_type == 'venues' and isinstance(data, pd.DataFrame):
                data.to_sql('venues', conn, if_exists='append', index=False)
                
            elif data_type == 'matches' and isinstance(data, pd.DataFrame):
                data.to_sql('matches', conn, if_exists='append', index=False)
                
            elif data_type == 'performances' and isinstance(data, pd.DataFrame):
                data.to_sql('player_performances', conn, if_exists='append', index=False)
                
            # For individual records
            elif data_type == 'team' and isinstance(data, dict):
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO teams (name, short_name, cricinfo_id) VALUES (?, ?, ?)",
                    (data.get('name'), data.get('short_name'), data.get('cricinfo_id'))
                )
                
            elif data_type == 'player' and isinstance(data, dict):
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO players 
                    (name, team_id, role, batting_average, bowling_average, recent_form, cricinfo_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data.get('name'), 
                        data.get('team_id'), 
                        data.get('role'),
                        data.get('batting_average'), 
                        data.get('bowling_average'),
                        data.get('recent_form'),
                        data.get('cricinfo_id')
                    )
                )
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error saving {data_type} to database: {e}")
            return False

    def import_data_to_django(self):
        """
        Import scraped data into Django models.
        
        This should be run from a Django management command.
        """
        try:
            from django.db import transaction
            
            conn = sqlite3.connect(self.db_path)
            
            # Import teams
            cursor = conn.cursor()
            cursor.execute("SELECT name, short_name FROM teams")
            teams = cursor.fetchall()
            
            with transaction.atomic():
                for name, short_name in teams:
                    Team.objects.get_or_create(
                        name=name,
                        defaults={'short_name': short_name or name[:4].upper()}
                    )
                    logger.info(f"Imported team: {name}")
            
            # Import venues
            cursor.execute("SELECT name, city, country FROM venues")
            venues = cursor.fetchall()
            
            with transaction.atomic():
                for name, city, country in venues:
                    Venue.objects.get_or_create(
                        name=name,
                        defaults={'city': city or 'Unknown', 'country': country or 'India'}
                    )
                    logger.info(f"Imported venue: {name}")
            
            # Import players
            cursor.execute("""
                SELECT p.name, p.role, p.batting_average, p.bowling_average, p.recent_form, t.name 
                FROM players p
                JOIN teams t ON p.team_id = t.id
            """)
            players = cursor.fetchall()
            
            with transaction.atomic():
                for name, role, batting_avg, bowling_avg, recent_form, team_name in players:
                    try:
                        team = Team.objects.get(name=team_name)
                        Player.objects.get_or_create(
                            name=name,
                            team=team,
                            defaults={
                                'role': role,
                                'batting_average': batting_avg or 0.0,
                                'bowling_average': bowling_avg or 0.0,
                                'recent_form': recent_form or batting_avg or 0.0
                            }
                        )
                        logger.info(f"Imported player: {name} ({team_name})")
                    except Team.DoesNotExist:
                        logger.error(f"Team {team_name} not found for player {name}")
            
            conn.close()
            logger.info("Data import complete!")
            return True
            
        except Exception as e:
            logger.error(f"Error importing data to Django: {e}")
            return False


class Command(BaseCommand):
    help = 'Scrape cricket data from ESPNCricinfo and import it into the database'
    
    def add_arguments(self, parser):
        parser.add_argument('--season', type=int, help='IPL season year to scrape (e.g., 2023)')
        parser.add_argument('--series-id', type=str, help='ESPNcricinfo series ID')
        parser.add_argument('--match-url', type=str, help='ESPNcricinfo match URL to scrape')
        parser.add_argument('--player-id', type=str, help='ESPNcricinfo player ID to scrape')
        parser.add_argument('--import-only', action='store_true', help='Import existing data without scraping')
    
    def handle(self, *args, **options):
        # Initialize scraper
        base_dir = os.path.dirname(os.path.abspath(__file__))
        scraper = ESPNCricinfoScraper(base_dir=base_dir)
        
        # Import existing data if requested
        if options['import_only']:
            self.stdout.write('Importing existing data to Django models...')
            success = scraper.import_data_to_django()
            if success:
                self.stdout.write(self.style.SUCCESS('Successfully imported data!'))
            else:
                self.stdout.write(self.style.ERROR('Failed to import data'))
            return
        
        # Scrape season matches
        if options['season']:
            season_year = options['season']
            series_id = options['series_id']
            self.stdout.write(f'Scraping IPL {season_year} matches...')
            
            matches_df = scraper.scrape_ipl_matches(season_year, series_id)
            self.stdout.write(f'Found {len(matches_df)} matches')
            
            # Optionally scrape match details
            if not matches_df.empty and self.confirm('Do you want to scrape details for these matches?'):
                for _, match in matches_df.iterrows():
                    self.stdout.write(f"Scraping {match['team1']} vs {match['team2']}...")
                    batting_df, bowling_df = scraper.scrape_match_scorecard(match['match_url'])
                    self.stdout.write(f"  Scraped {len(batting_df)} batting and {len(bowling_df)} bowling performances")
        
        # Scrape specific match
        elif options['match_url']:
            match_url = options['match_url']
            self.stdout.write(f'Scraping match details from {match_url}...')
            batting_df, bowling_df = scraper.scrape_match_scorecard(match_url)
            self.stdout.write(f"Scraped {len(batting_df)} batting and {len(bowling_df)} bowling performances")
        
        # Scrape player profile
        elif options['player_id']:
            player_id = options['player_id']
            self.stdout.write(f'Scraping player profile for ID {player_id}...')
            player_data = scraper.scrape_player_profile(player_id)
            if player_data:
                self.stdout.write(f"Scraped player: {player_data['name']}, Role: {player_data['role']}")
        
        # No specific action
        else:
            self.stdout.write(self.style.WARNING('No action specified. Use --help to see available options.'))
            return
        
        # Import to Django
        if self.confirm('Do you want to import scraped data into Django models?'):
            success = scraper.import_data_to_django()
            if success:
                self.stdout.write(self.style.SUCCESS('Successfully imported data!'))
            else:
                self.stdout.write(self.style.ERROR('Failed to import data'))
    
    def confirm(self, question):
        """Ask a yes/no question and return the answer."""
        response = input(f"\n{question} (y/n): ").lower().strip()
        return response and response[0] == 'y'
