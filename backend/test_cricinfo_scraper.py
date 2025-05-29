"""
Test script for the ESPNCricinfo scraper implementation.
This script allows quick testing of the scraper functionality without running the Django server.
"""

import os
import sys
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Define a standalone version of the scraper without Django dependencies
class ESPNCricinfoScraper:
    """
    A class to scrape cricket data from ESPNCricinfo.
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
            logging.info(f"Fetching URL: {url}")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return BeautifulSoup(response.content, 'lxml')
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching {url}: {e}")
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
            logging.error(f"Failed to get match results for IPL {season_year}")
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
                
                logging.info(f"Extracted match: {team1} vs {team2} at {venue}")
                self._random_delay()
                
            except Exception as e:
                logging.error(f"Error extracting match data: {e}")
        
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
            logging.error(f"Failed to get scorecard for {match_url}")
            return pd.DataFrame(), pd.DataFrame()
        
        match_id = match_url.split('/')[-1]
        
        # Extract teams
        team_names = []
        team_elements = soup.select('span.ds-text-title-xs.ds-font-bold')
        for elem in team_elements:
            if elem.text.strip():
                team_names.append(elem.text.strip())
        
        if len(team_names) < 2:
            logging.warning(f"Could not find team names for match {match_id}")
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
                    logging.error(f"Error extracting batting data: {e}")
        
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
                    logging.error(f"Error extracting bowling data: {e}")
        
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
            logging.error(f"Failed to get player profile for ID {player_id}")
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
            
        except Exception as e:
            logging.error(f"Error extracting player data: {e}")
        
        # Save to CSV
        pd.DataFrame([player_data]).to_csv(
            os.path.join(self.data_dir, f"player_{player_id}.csv"), 
            index=False
        )
        
        return player_data

def test_ipl_matches_scrape():
    """Test scraping IPL matches for a specific season."""
    scraper = ESPNCricinfoScraper()
    
    print("Testing IPL matches scraper...")
    season_year = 2023
    series_id = "indian-premier-league-2023-1345038"
    
    matches_df = scraper.scrape_ipl_matches(season_year, series_id)
    
    if not matches_df.empty:
        print(f"✓ Successfully scraped {len(matches_df)} IPL {season_year} matches")
        print("\nSample data:")
        print(matches_df[['team1', 'team2', 'venue', 'date', 'result']].head())
    else:
        print("✗ Failed to scrape IPL matches")

def test_match_scrape():
    """Test scraping a specific match scorecard."""
    scraper = ESPNCricinfoScraper()
    
    print("\nTesting match scorecard scraper...")
    # CSK vs GT IPL 2023 final
    match_url = "https://www.espncricinfo.com/series/indian-premier-league-2023-1345038/chennai-super-kings-vs-gujarat-titans-final-1370353/full-scorecard"
    
    batting_df, bowling_df = scraper.scrape_match_scorecard(match_url)
    
    if not batting_df.empty:
        print(f"✓ Successfully scraped batting data: {len(batting_df)} entries")
        print("\nTop batting performances:")
        print(batting_df.sort_values('runs', ascending=False)[['player_name', 'team', 'runs', 'balls', 'fours', 'sixes']].head())
    else:
        print("✗ Failed to scrape batting data")
        
    if not bowling_df.empty:
        print(f"✓ Successfully scraped bowling data: {len(bowling_df)} entries")
        print("\nTop bowling performances:")
        print(bowling_df.sort_values('wickets', ascending=False)[['player_name', 'team', 'overs', 'wickets', 'runs']].head())
    else:
        print("✗ Failed to scrape bowling data")

def test_player_scrape():
    """Test scraping a player profile."""
    scraper = ESPNCricinfoScraper()
    
    print("\nTesting player profile scraper...")
    # Virat Kohli's profile
    player_id = "253802"
    
    player_data = scraper.scrape_player_profile(player_id)
    
    if player_data:
        print(f"✓ Successfully scraped player data for: {player_data['name']}")
        print("\nPlayer details:")
        for key, value in player_data.items():
            if key != 'recent_matches':
                print(f"{key}: {value}")
    else:
        print("✗ Failed to scrape player data")

def main():
    """Main function to run all tests."""
    print("=" * 50)
    print("ESPNCRICINFO SCRAPER TEST")
    print("=" * 50)
    
    # Uncomment the tests you want to run
    test_ipl_matches_scrape()
    test_match_scrape()
    test_player_scrape()
    
    print("\n" + "=" * 50)
    print("TEST COMPLETED")
    print("=" * 50)

if __name__ == "__main__":
    main()
