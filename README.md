# Reddit User Persona Generator

This script is a submission for the AI/LLM Engineer Intern assignment. It analyzes a Reddit user's recent activity to generate a detailed user persona, including key interests, overall tone, and an AI-generated summary.

## Features

* **Data Collection:** Fetches the 100 most recent comments and posts for any given Reddit user using the PRAW library.
* **Interest Analysis:** Identifies the user's primary interests by analyzing their most active subreddits.
* **Sentiment Analysis:** Determines the user's overall tone (Positive, Negative, or Neutral) by performing sentiment analysis on their comments using NLTK.
* **AI-Powered Summary:** Leverages the Google Gemini API to generate a concise, human-like bio that summarizes the user's personality and interests.
* **Cited Reporting:** Generates a `.txt` report that includes all findings and provides a direct link and quote as a citation for the user's primary interest.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/adityav-123/reddit-persona-generator.git](https://github.com/adityav-123/reddit-persona-generator.git)
    cd reddit-persona-generator
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

3.  **Install the required libraries:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create your environment file:**
    Create a file named `.env` in the main project directory and add your API credentials. You will need keys from both Reddit and Google AI Studio.

    ```
    REDDIT_CLIENT_ID="your_reddit_client_id"
    REDDIT_CLIENT_SECRET="your_reddit_client_secret"
    REDDIT_USER_AGENT="PersonaGenerator/0.1 by YourRedditUsername"
    GOOGLE_API_KEY="your_google_ai_api_key"
    ```

## How to Run

To generate a persona, run the script from your terminal with the target Reddit username as an argument:

```bash
python persona_generator.py <username>