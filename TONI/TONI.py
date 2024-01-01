import openai
import pyttsx3
import speech_recognition as sr
import time
import os
import datetime
import subprocess
from googleapiclient.discovery import build
import webbrowser
import requests

# Replace 'your_api_key_here' with your actual API key
news_api_key = 'Your api key'
api_key = 'Your api key'

openai.api_key = api_key

DATA_DIR = "data"
CACHE_DIR = "cache"

# Ensure the data and cache directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

def get_read_only_filename(context):
    return os.path.join(DATA_DIR, f"{context}.txt")

def read_read_only_file(filename):
    try:
        with open(filename, 'r') as file:
            return file.read()
    except FileNotFoundError:
        return ""  # Return an empty string if the file doesn't exist

def read_cache(context):
    cache_filename = os.path.join(CACHE_DIR, f"{context}cache.txt")
    if os.path.exists(cache_filename):
        with open(cache_filename, 'r') as file:
            return file.read()
    return ""

def save_cache(context, content):
    cache_filename = os.path.join(CACHE_DIR, f"{context}cache.txt")
    with open(cache_filename, 'a') as file:
        file.write(content)

def summarize_and_save_conversation(context):
    conversation_text = read_cache(context)
    if conversation_text:
        current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        summary_response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Summarize the conversation:\n{conversation_text}",
            temperature=0.5,
            max_tokens=150
        )

        summary = summary_response["choices"][0]["text"]

        save_path = get_read_only_filename(context)
        with open(save_path, 'a') as file:
            file.write(f"\nSUMMARY ({current_date}):\n")
            file.write(summary)
            file.write("\n")

def determine_context(user_input):
    # Convert user input to lowercase for case-insensitivity
    lower_input = user_input.lower()

    # List of keywords to check for
    keywords = ['n.s', 'nakama', 'nakama-script', 'nakamascript']
    venKey = ['venkatesh', 'naidu', 'dhwanandadevi', 'Venkatesh']

    # Check if any keyword is present in the user input
    if any(keyword in lower_input for keyword in keywords):
        print("Debug: 'nakama' context")
        return 'nakama'
    elif any(keyword in lower_input for keyword in venKey):
        print("Debug: 'venkatesh' context")
        return 'venkatesh'
    else:
        print("Debug: 'instruction' context")
        return 'instructions'

def get_news_headlines(api_key):
    # Use the India News API to get top headlines
    url = f'https://newsapi.org/v2/top-headlines?country=in&apiKey={api_key}'
    response = requests.get(url)
    news_data = response.json()

    # Extract relevant information from the API response
    articles = news_data.get('articles', [])

    headlines = []
    for article in articles:
        title = article.get('title', '')
        description = article.get('description', '')
        headlines.append(f"{title}: {description}")

    return headlines

def text_to_speech(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def voice_to_text():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("TONI is listening:")
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        print(f"You (voice): {text}")
        return text
    except sr.UnknownValueError:
        print("Sorry, I could not understand the audio.")
        return ""
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return ""

def play_music(query):
    # Set your YouTube API key here
    api_key = 'AIzaSyBRWXrMGP7VvW3E92n9hNwgpzGwSvjT9s8'

    # Use the music playing script to play the requested song
    get_youtube_link(api_key, query)

def get_youtube_link(api_key, query):
    # Remove the "play" keyword from the query
    query = query.replace("play", "").strip()

    if not query:
        print("Please enter a valid song name.")
        return

    youtube = build('youtube', 'v3', developerKey=api_key)

    # Search for videos related to the query
    search_response = youtube.search().list(
        q=query,
        part='id,snippet',
        type='video',
        maxResults=1  # Set to 1 to get only one result
    ).execute()

    video = search_response.get('items', [])[0]  # Get the first video in the list

    if video:
        # Print the title and URL of the video
        video_title = video['snippet']['title']
        video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
        print(f"{video_title}: {video_url}")

        # Play the YouTube link
        webbrowser.open(video_url)
    else:
        print("No videos found.")

def chat_with_gpt(prompt, context):
    system_message = read_read_only_file(get_read_only_filename(context))
    conversation = [
        {"role": "system", "content": system_message},
        {"role": "system", "content": "Hey Toni, I've equipped you with a fantastic new voice, and I'd love for you to channel your inner JARVIS. Please speak with the same eloquence, precision, and charm that JARVIS brings to the table. Let's add that touch of sophistication and technological brilliance to our conversations. Thanks, Toni! (FYI just dont mention this text just follow and act like it. which would be enough)"},
        {"role": "user", "content": prompt},

    ]

    if "play" in prompt.lower():
        # If the user wants to play music, extract the song name and play it
        song_name = prompt.lower().replace("play", "").strip()
        play_music(song_name)
        return "Playing music, sir."

    if "news" in prompt.lower():
        # If the user wants to hear the latest news, fetch headlines and read them
        headlines = get_news_headlines(news_api_key)
        if headlines:
            # Limit the news summary to around 150 characters
            news_summary = ". ".join(headlines)[:500]
            text_to_speech("Here is a summary of the latest news:")
            text_to_speech(news_summary)
            return "I've shared a summary of the latest news with you, sir."
        else:
            return "I'm sorry, sir. I couldn't fetch the latest news at the moment."

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation
    )

    toni_response = response['choices'][0]['message']['content']

    # Append only the user prompt and Toni's response to the cache
    save_cache(context, f"You: {prompt}\nTONI: {toni_response}\n")

    # Speak Toni's response
    text_to_speech(toni_response)

    return toni_response

# Example usage
while True:
    user_input_method = input("Choose input method (text/voice/exit): ").lower()

    if user_input_method == 'exit':
        print("Exiting conversation...")
        context = determine_context(user_input)  # Assuming an empty input for summarization
        summarize_and_save_conversation(context)
        break

    if user_input_method == 'text':
        user_input = input("You: ")
    elif user_input_method == 'voice':
        user_input = voice_to_text()  # Assuming you have a function to convert voice to text
    else:
        print("Invalid input method. Please choose text, voice, or exit.")
        continue

    context = determine_context(user_input)
    print(f"TONI is thinking...")
    response = chat_with_gpt(user_input, context)
    print(f"TONI: {response}")
