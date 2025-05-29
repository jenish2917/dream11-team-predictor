from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from predictor.models import Team, Venue, Player

class Command(BaseCommand):
    help = 'Populates the database with initial data'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating initial data...')
        
        # Create IPL Teams
        teams_data = [
            {'name': 'Chennai Super Kings', 'short_name': 'CSK'},
            {'name': 'Delhi Capitals', 'short_name': 'DC'},
            {'name': 'Gujarat Titans', 'short_name': 'GT'},
            {'name': 'Kolkata Knight Riders', 'short_name': 'KKR'},
            {'name': 'Lucknow Super Giants', 'short_name': 'LSG'},
            {'name': 'Mumbai Indians', 'short_name': 'MI'},
            {'name': 'Punjab Kings', 'short_name': 'PBKS'},
            {'name': 'Rajasthan Royals', 'short_name': 'RR'},
            {'name': 'Royal Challengers Bangalore', 'short_name': 'RCB'},
            {'name': 'Sunrisers Hyderabad', 'short_name': 'SRH'},
        ]
        
        teams = {}
        for team_data in teams_data:
            team, created = Team.objects.get_or_create(
                name=team_data['name'],
                defaults={'short_name': team_data['short_name']}
            )
            teams[team.short_name] = team
            if created:
                self.stdout.write(f'Created team: {team.name}')
        
        # Create IPL Venues
        venues_data = [
            {'name': 'M. A. Chidambaram Stadium', 'city': 'Chennai', 'country': 'India'},
            {'name': 'Arun Jaitley Stadium', 'city': 'Delhi', 'country': 'India'},
            {'name': 'Narendra Modi Stadium', 'city': 'Ahmedabad', 'country': 'India'},
            {'name': 'Eden Gardens', 'city': 'Kolkata', 'country': 'India'},
            {'name': 'Wankhede Stadium', 'city': 'Mumbai', 'country': 'India'},
            {'name': 'M. Chinnaswamy Stadium', 'city': 'Bengaluru', 'country': 'India'},
            {'name': 'Rajiv Gandhi International Cricket Stadium', 'city': 'Hyderabad', 'country': 'India'},
            {'name': 'Punjab Cricket Association IS Bindra Stadium', 'city': 'Mohali', 'country': 'India'},
            {'name': 'Sawai Mansingh Stadium', 'city': 'Jaipur', 'country': 'India'},
            {'name': 'Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium', 'city': 'Lucknow', 'country': 'India'},
        ]
        
        for venue_data in venues_data:
            venue, created = Venue.objects.get_or_create(
                name=venue_data['name'],
                defaults={'city': venue_data['city'], 'country': venue_data['country']}
            )
            if created:
                self.stdout.write(f'Created venue: {venue.name}')
        
        # Create some sample players
        players_data = [
            # CSK Players
            {'name': 'MS Dhoni', 'team': teams['CSK'], 'role': 'WK', 'batting_avg': 38.5, 'bowling_avg': 0},
            {'name': 'Ravindra Jadeja', 'team': teams['CSK'], 'role': 'AR', 'batting_avg': 26.4, 'bowling_avg': 29.7},
            {'name': 'Ruturaj Gaikwad', 'team': teams['CSK'], 'role': 'BAT', 'batting_avg': 42.8, 'bowling_avg': 0},
            
            # MI Players
            {'name': 'Rohit Sharma', 'team': teams['MI'], 'role': 'BAT', 'batting_avg': 31.2, 'bowling_avg': 0},
            {'name': 'Jasprit Bumrah', 'team': teams['MI'], 'role': 'BWL', 'batting_avg': 5.2, 'bowling_avg': 23.8},
            {'name': 'Hardik Pandya', 'team': teams['MI'], 'role': 'AR', 'batting_avg': 29.5, 'bowling_avg': 31.2},
            
            # RCB Players
            {'name': 'Virat Kohli', 'team': teams['RCB'], 'role': 'BAT', 'batting_avg': 37.9, 'bowling_avg': 0},
            {'name': 'Glenn Maxwell', 'team': teams['RCB'], 'role': 'AR', 'batting_avg': 26.7, 'bowling_avg': 33.1},
            {'name': 'Mohammed Siraj', 'team': teams['RCB'], 'role': 'BWL', 'batting_avg': 6.5, 'bowling_avg': 26.8},
        ]
        
        for player_data in players_data:
            player, created = Player.objects.get_or_create(
                name=player_data['name'],
                team=player_data['team'],
                defaults={
                    'role': player_data['role'],
                    'batting_average': player_data['batting_avg'],
                    'bowling_average': player_data['bowling_avg'],
                    'recent_form': player_data['batting_avg'] if player_data['role'] in ['BAT', 'AR', 'WK'] else player_data['bowling_avg']
                }
            )
            if created:
                self.stdout.write(f'Created player: {player.name} ({player.team.short_name})')
        
        self.stdout.write(self.style.SUCCESS('Initial data created successfully!'))
