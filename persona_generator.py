import praw
import os
import argparse
import requests
from collections import Counter
from dotenv import load_dotenv
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    print("Just a moment, downloading a necessary file for analysis...")
    nltk.download('vader_lexicon', quiet=True)

load_dotenv()

CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
USER_AGENT = os.getenv("REDDIT_USER_AGENT")
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
DATA_LIMIT = 100

def connect_to_reddit():
    if not all([CLIENT_ID, CLIENT_SECRET, USER_AGENT]):
        print("oops, I can't find the Reddit API details in the .env file.")
        return None
        
    print("Alright, let's connect to Reddit...")
    try:
        reddit = praw.Reddit(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, user_agent=USER_AGENT)
        print("Success! We're connected to Reddit.")
        return reddit
    except Exception as e:
        print(f"Hmm, couldn't connect to Reddit. Here's the error: {e}")
        return None

def fetch_user_data(reddit: praw.Reddit, username: str, limit: int):
    print(f"\nNow, let's see what we can find about u/{username}...")
    try:
        redditor = reddit.redditor(username)
        comments = list(redditor.comments.new(limit=limit))
        submissions = list(redditor.submissions.new(limit=limit))
        user_data = {"username": redditor.name, "comments": comments, "submissions": submissions}
        print(f"Got it. Found {len(comments)} recent comments and {len(submissions)} posts.")
        return user_data
    except NotFound:
        print(f"Couldn't find anyone on Reddit with the username u/{username}.")
        return None
    except Exception as e:
        print(f"Something went wrong while getting the data: {e}")
        return None

def analyze_data(user_data: dict):
    print("\nOkay, time to analyze this data...")
    subreddit_counter = Counter()
    all_text_content = []
    
    for comment in user_data["comments"]:
        subreddit_counter[comment.subreddit.display_name] += 1
        all_text_content.append(comment.body)
        
    for submission in user_data["submissions"]:
        subreddit_counter[submission.subreddit.display_name] += 1
        if submission.selftext:
            all_text_content.append(submission.title + " " + submission.selftext)
        else:
            all_text_content.append(submission.title)

    sia = SentimentIntensityAnalyzer()
    sentiment_scores = [sia.polarity_scores(comment.body)['compound'] for comment in user_data["comments"]]
    average_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
    
    analysis_results = {
        "most_active_subreddits": subreddit_counter.most_common(5),
        "average_sentiment": average_sentiment,
        "raw_text": "\n".join(all_text_content)
    }
    print("Analysis done.")
    return analysis_results

def get_ai_summary(text_corpus: str) -> str:
    print("Asking the AI to write up a summary...")
    if not GEMINI_API_KEY:
        return "Can't generate an AI summary because the GOOGLE_API_KEY is missing from the .env file."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    prompt = f"Based on the following collection of a person's Reddit comments and posts, please write a brief, insightful 2-3 sentence user persona summary. Your goal is to capture their personality, tone, and primary interests based *only* on the text provided.\n\n---\n\n{text_corpus[:4000]}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if 'candidates' in result and result['candidates'][0]['content']['parts'][0]['text']:
            summary = result['candidates'][0]['content']['parts'][0]['text']
            return summary.strip()
        else:
            return "The AI responded, but I couldn't find a summary in its answer."
            
    except requests.exceptions.RequestException as e:
        return f"Couldn't reach the AI. There might be a network issue. Error: {e}"
    except (KeyError, IndexError):
        return "The AI's response was not in the format I expected."
    except Exception as e:
        return f"An unexpected error occurred while talking to the AI: {e}"

def generate_report(user_data: dict, analysis: dict):
    username = user_data['username']
    filename = f"{username}_persona.txt"
    print(f"\nPutting it all together in a report: {filename}...")

    ai_summary = get_ai_summary(analysis['raw_text'])
    top_subreddit = analysis['most_active_subreddits'][0][0] if analysis['most_active_subreddits'] else None
    citation_comment = next((c for c in user_data['comments'] if c.subreddit.display_name == top_subreddit), None)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"USER PERSONA: u/{username}\n{'='*30}\n\n")
        f.write("## AI-Generated Bio ##\n")
        f.write(f"{ai_summary}\n\n")
        f.write("## Personality & Tone ##\n")
        sentiment_score = analysis['average_sentiment']
        tone = "Neutral"
        if sentiment_score > 0.05: tone = "Positive"
        elif sentiment_score < -0.05: tone = "Negative"
        f.write(f"- Overall Tone: Generally {tone} (Sentiment Score: {sentiment_score:.2f})\n\n")
        f.write("## Key Interests (from Subreddit Activity) ##\n")
        if not analysis['most_active_subreddits']:
            f.write("- Not enough activity to determine key interests.\n")
        else:
            for sub, count in analysis['most_active_subreddits']:
                f.write(f"- {sub} (based on {count} recent activities)\n")
        
        if citation_comment:
            f.write("\n\n## Example of Activity ##\n")
            f.write(f"Here's an example of their activity in r/{top_subreddit}:\n")
            f.write("------------------------\n")
            f.write(f"URL: https://www.reddit.com{citation_comment.permalink}\n\n")
            f.write(f'"{citation_comment.body[:300]}..."\n')
            f.write("------------------------\n")

    print(f"All done! The persona has been saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description="A script to generate a user persona from a Reddit profile.")
    parser.add_argument("username", help="The Reddit username you want to look up.")
    args = parser.parse_args()
    
    reddit_instance = connect_to_reddit()

    if reddit_instance:
        data = fetch_user_data(reddit_instance, args.username, DATA_LIMIT)

        if data:
            analysis = analyze_data(data)
            generate_report(data, analysis)

if __name__ == "__main__":
    main()
