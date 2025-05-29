#!/usr/bin/env python
"""
ESPNCricinfo Scraper Test Script

This script demonstrates how to use the scraper from outside the Django management command.
It's useful for testing or ad-hoc scraping needs.

Example usage:
    python test_scraper.py
"""

import os
import sys

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Set up Django environment
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dream11_backend.settings')
django.setup()

# Import the scraper
from predictor.management.commands.scrape_cricinfo import ESPNCricinfoScraper

def main():
    """Main function to demonstrate usage of the ESPNCricinfo scraper."""
    print("ESPNCricinfo Scraper Test Script")
    print("--------------------------------")
    
    # Initialize the scraper
    scraper = ESPNCricinfoScraper()
    print(f"Scraper initialized. Data will be stored in: {scraper.data_dir}")
    print(f"SQLite database path: {scraper.db_path}")
    
    # Ask user what they want to scrape
    print("\nWhat would you like to scrape?")
    print("1. IPL matches for a specific season")
    print("2. A specific match scorecard")
    print("3. A player profile")
    print("4. Import existing data to Django models")
    print("5. Exit")
    
    choice = input("\nEnter your choice (1-5): ")
    
    if choice == '1':
        season_year = input("Enter IPL season year (e.g., 2023): ")
        series_id = input("Enter series ID (leave blank for default format): ")
        
        if not series_id:
            series_id = None
            
        print(f"\nScraping IPL {season_year} matches...")
        matches_df = scraper.scrape_ipl_matches(int(season_year), series_id)
        print(f"Found {len(matches_df)} matches")
        
        if not matches_df.empty:
            print("\nFirst few matches:")
            print(matches_df[['team1', 'team2', 'venue', 'date']].head())
            
            proceed = input("\nDo you want to scrape details for these matches? (y/n): ")
            if proceed.lower().startswith('y'):
                for _, match in matches_df.iterrows():
                    print(f"\nScraping {match['team1']} vs {match['team2']}...")
                    batting_df, bowling_df = scraper.scrape_match_scorecard(match['match_url'])
                    print(f"  Scraped {len(batting_df)} batting and {len(bowling_df)} bowling performances")
    
    elif choice == '2':
        match_url = input("Enter match URL from ESPNCricinfo: ")
        
        print(f"\nScraping match details from {match_url}...")
        batting_df, bowling_df = scraper.scrape_match_scorecard(match_url)
        
        if not batting_df.empty:
            print(f"\nScraping successful! Found {len(batting_df)} batting performances")
            print("\nTop batting performances (by fantasy points):")
            print(batting_df.sort_values('fantasy_points', ascending=False)[
                ['player_name', 'team', 'runs', 'balls', 'fours', 'sixes', 'fantasy_points']
            ].head())
        
        if not bowling_df.empty:
            print("\nTop bowling performances (by fantasy points):")
            print(bowling_df.sort_values('fantasy_points', ascending=False)[
                ['player_name', 'team', 'overs', 'wickets', 'runs', 'fantasy_points']
            ].head())
    
    elif choice == '3':
        player_id = input("Enter player ID from ESPNCricinfo: ")
        
        print(f"\nScraping player profile for ID {player_id}...")
        player_data = scraper.scrape_player_profile(player_id)
        
        if player_data:
            print("\nPlayer details:")
            print(f"Name: {player_data['name']}")
            print(f"Role: {player_data['role']}")
            print(f"Team: {player_data['team']}")
            print(f"Batting Average: {player_data['batting_average']}")
            print(f"Bowling Average: {player_data['bowling_average']}")
    
    elif choice == '4':
        print("\nImporting scraped data into Django models...")
        success = scraper.import_data_to_django()
        
        if success:
            print("Successfully imported data!")
        else:
            print("Failed to import data. Check the log for details.")
    
    elif choice == '5':
        print("\nExiting...")
        return
    
    else:
        print("\nInvalid choice. Please run the script again.")

if __name__ == "__main__":
    main()
