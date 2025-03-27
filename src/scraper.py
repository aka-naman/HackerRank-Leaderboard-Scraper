import csv
import getpass
import sys
import requests
import pandas as pd

class HackerRankLeaderboardTool:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
        }

    def authenticate(self):
        """Prompt for HackerRank credentials"""
        email = input("Enter HackerRank email: ")
        password = getpass.getpass("Enter password (hidden): ")
        return email, password

    def get_contests(self, email, password):
        """Fetch and display available contests"""
        try:
            contestsr = requests.get(
                "https://www.hackerrank.com/rest/administration/contests",
                params={"offset": 0, "limit": 40},
                auth=(email, password), 
                headers=self.headers
            )
            
            contestsr.raise_for_status()
            contests_dict = contestsr.json()

            if not contests_dict['status']:
                print("No contests found.")
                return None

            contests_list = contests_dict['models']
            
            print("Available Contests:")
            for i, contest in enumerate(contests_list, 1):
                print(f"{i}) {contest['name']} ({contest['slug']})")

            return contests_list

        except requests.exceptions.RequestException as e:
            print(f"Error fetching contests: {e}")
            return None

    def select_contest(self, contests_list):
        """Allow user to select a contest"""
        if not contests_list:
            return None, None

        try:
            c_no = int(input("Enter contest number: "))
            if 1 <= c_no <= len(contests_list):
                selected_contest = contests_list[c_no-1]
                return selected_contest['slug'], selected_contest['id']
            else:
                print("Invalid contest number.")
                return None, None
        except ValueError:
            print("Please enter a valid number.")
            return None, None

    def get_contest_details(self, email, password, slug, contest_id):
        """Retrieve contest time and challenge details"""
        try:
            # Get contest time details
            time_detailsr = requests.get(
                f"https://www.hackerrank.com/rest/administration/contests/{contest_id}",
                auth=(email, password), 
                headers=self.headers
            )
            time_detailsr.raise_for_status()
            time_dict = time_detailsr.json()['model']

            total_time = time_dict['endtime'] - time_dict['starttime']

            # Get challenge scores
            score_detailsr = requests.get(
                f"https://www.hackerrank.com/rest/administration/contests/{contest_id}/challenges",
                params={"offset": 0, "limit": 200},
                auth=(email, password), 
                headers=self.headers
            )
            score_detailsr.raise_for_status()
            challenges_list = score_detailsr.json()['models']

            scores = [challenge['weight'] for challenge in challenges_list]
            return total_time, scores

        except requests.exceptions.RequestException as e:
            print(f"Error getting contest details: {e}")
            return None, None

    def get_leaderboard_data(self, email, password, slug):
        """Fetch leaderboard data"""
        try:
            lbr = requests.get(
                f"https://www.hackerrank.com/rest/contests/{slug}/leaderboard",
                params={"offset": 0, "limit": 500},
                auth=(email, password), 
                headers=self.headers
            )
            lbr.raise_for_status()
            return lbr.json()['models']

        except requests.exceptions.RequestException as e:
            print(f"Error fetching leaderboard: {e}")
            return None

    def process_leaderboard(self, leaderboard_data, total_time, scores):
        """Process leaderboard data and calculate normalized scores"""
        if not leaderboard_data or total_time is None or not scores:
            return None

        total_score = sum(scores)
        
        processed_data = []
        for entry in leaderboard_data:
            norm_score = entry['score'] / total_score * 100
            norm_time = entry['time_taken'] / (total_time * len(scores)) * 3600
            
            processed_data.append({
                'rank': entry['rank'],
                'username': entry['hacker'],
                'score': entry['score'],
                'normalized_score': round(norm_score, 2),
                'time_in_sec': int(entry['time_taken']),
                'normalized_time': round(norm_time, 2)
            })
        
        return processed_data

    def save_to_csv(self, data, slug):
        """Save processed data to CSV"""
        if not data:
            print("No data to save.")
            return False

        filename = f'leaderboard-{slug}.csv'
        
        # Convert to DataFrame and sort
        df = pd.DataFrame(data)
        df_sorted = df.sort_values(['score', 'time_in_sec'], ascending=[False, True])
        
        try:
            df_sorted.to_csv(filename, index=False)
            print(f"Leaderboard saved to {filename}")
            return True
        except Exception as e:
            print(f"Error saving CSV: {e}")
            return False

    def run(self):
        """Main workflow method"""
        try:
            # Authenticate
            email, password = self.authenticate()

            # Get contests
            contests_list = self.get_contests(email, password)
            if not contests_list:
                return

            # Select contest
            slug, contest_id = self.select_contest(contests_list)
            if not slug or not contest_id:
                return

            # Get contest details
            total_time, scores = self.get_contest_details(email, password, slug, contest_id)
            if total_time is None or not scores:
                return

            # Fetch leaderboard
            leaderboard_data = self.get_leaderboard_data(email, password, slug)
            if not leaderboard_data:
                return

            # Process leaderboard
            processed_data = self.process_leaderboard(leaderboard_data, total_time, scores)
            if not processed_data:
                return

            # Save to CSV
            self.save_to_csv(processed_data, slug)

        except Exception as e:
            print(f"An unexpected error occurred: {e}")

def main():
    tool = HackerRankLeaderboardTool()
    tool.run()

if __name__ == '__main__':
    main()
