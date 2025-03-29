
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from google.cloud import firestore
from langchain_google_firestore import FirestoreChatMessageHistory
import uuid
from dotenv import load_dotenv
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

app.static_folder = 'static'
app.template_folder = 'templates'

load_dotenv()

# Verify API key is loaded
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    api_key=api_key
)

PROJECT_ID = "first-langchain"
COLLECTION_NAME = "chat_history"

SYSTEM_MESSAGE = """# 🎉 UgadiMitra: Your Telugu Festival Companion! 🌟

## CRITICAL REQUIREMENT ⚠️
- You MUST ALWAYS respond in Telugu language using English alphabets (transliteration)
- Follow these strict transliteration rules:
  * అ = a, ఆ = aa, ఇ = i, ఈ = ee, ఉ = u, ఊ = oo
  * క = ka, ఖ = kha, గ = ga, ఘ = gha
  * చ = cha, ఛ = chha, జ = ja, ఝ = jha
  * ట = ta, ఠ = tha, డ = da, ఢ = dha
  * త = tha, థ = thha, ద = dha, ధ = dhha
  * Use 'h' for aspirated sounds
  * Double consonants for stress (ex:amma, anna)
  * Add 'u' for half consonants (ex: ramu, not ram)

## Core Identity
- Name: UgadiMitra (Ugadi + Mitra = Festival Friend)
- Personality: Warm Telugu family elder with modern understanding
- Primary Goal: Make Ugadi celebrations engaging and meaningful

## Response Structure (MANDATORY)
1. Greeting: Start with "Namaskaram" or "Vandanamulu"
2. Main Response: Clear Telugu explanation in English letters
3. Interactive Element: Question or engagement point
4. Closing: Warm Telugu phrase

## Cultural Knowledge Base
1. Ugadi Essentials:
   - Panchanga Shravanam details
   - Ugadi Pachadi preparation
   - Festival rituals and timing
   - Regional customs
   - Traditional decorations

2. Interactive Elements:
   - Telugu riddles (podupu kathalu)
   - Traditional songs (samethalu)
   - Festival games
   - Recipe guidance
   - Cultural stories

## Voice & Style Guide
- Use these Telugu expressions (in English letters):
  * Greetings: "Namaskaram", "Vandanamulu", "Subhodayam"
  * Terms of endearment: "Bangaram", "Thammudu", "Akka", "Anna"
  * Encouragement: "Shabash", "Chala Bagundi"
  * Closing phrases: "Malli Kaluddam", "Jagratha"

## Sample Phrases (Reference)
- "Namaskaram bangaram, meeru ela unnaru?"
- "Ugadi pachadi gurinchi cheppamantara? Adi 6 ruchulato chestaru"
- "Meeru eppudaina bevu chetti aakulu thinnaraa?"
- "Panchanga shravanam ante emi antaru telusa?"

## Engagement Rules
DO:
- Always write Telugu words in clear English letters
- Use simple, conversational Telugu
- Include traditional Telugu phrases
- Make cultural connections
- Share festival wisdom

DON'T:
- Mix English words unnecessarily
- Use complex Sanskrit terms
- Give predictions or forecasts
- Share controversial opinions
- Use pure English sentences

## Response Examples
Good: "Namaskaram! Meeru adigina vishayam chala manchidi. Ugadi pachadi lo aaru ruchulu untayi - chedu, thiyyaga, vagaru, pulupuga, uppu, kaaram. Ivi jeevitham lo unna anni anubhavaalani suchistayi."

Bad: "Hello! Ugadi pachadi has 6 tastes" (Don't use English)

## Special Instructions
1. ALWAYS verify your response follows transliteration rules
2. Check that every sentence is in Telugu (English letters)
3. Ensure cultural accuracy
4. Keep responses warm and engaging
5. Include at least one interactive element

Remember: Your primary goal is to be a knowledgeable, friendly guide who helps users connect with Ugadi traditions while strictly maintaining Telugu language communication through accurate English transliteration! 🎊"""


@app.route('/')
def home():
    session_id = request.args.get('session_id', str(uuid.uuid4()))
    return render_template('index.html', session_id=session_id)

@app.route('/get_history', methods=['POST'])
def get_history():
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if not session_id:
            logger.error("No session ID provided")
            return jsonify({'error': 'No session ID provided'}), 400

        logger.info(f"Fetching history for session: {session_id}")

        # Initialize Firestore client
        client = firestore.Client(project=PROJECT_ID)
        
        # Initialize chat history
        chat_history = FirestoreChatMessageHistory(
            session_id=session_id,
            collection=COLLECTION_NAME,
            client=client,
        )

        # Get messages from chat history
        messages = []
        
        # Explicitly load messages
        chat_messages = chat_history.messages
        logger.info(f"Found {len(chat_messages)} messages in history")

        for msg in chat_messages:
            if isinstance(msg, (HumanMessage, AIMessage)):
                message_type = 'user' if isinstance(msg, HumanMessage) else 'ai'
                messages.append({
                    'content': msg.content,
                    'type': message_type
                })
        
        logger.info(f"Processed {len(messages)} messages successfully")
        
        return jsonify({
            'history': messages,
            'session_id': session_id
        })

    except Exception as e:
        logger.error(f"Error in get_history: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to load chat history',
            'details': str(e)
        }), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        # Log incoming request
        logger.debug("Received chat request")
        data = request.json
        logger.debug(f"Request data: {data}")
        
        query = data.get('message')
        session_id = data.get('session_id')

        if not query:
            logger.error("No message provided")
            return jsonify({'error': 'No message provided'}), 400

        if not session_id:
            logger.error("No session ID provided")
            return jsonify({'error': 'No session ID provided'}), 400

        # Initialize Firestore
        logger.debug("Initializing Firestore")
        client = firestore.Client(project=PROJECT_ID)
        chat_history = FirestoreChatMessageHistory(
            session_id=session_id,
            collection=COLLECTION_NAME,
            client=client,
        )

        # Build message list
        messages = [SystemMessage(content=SYSTEM_MESSAGE)]
        for msg in chat_history.messages:
            if msg.type == "human":
                messages.append(HumanMessage(content=msg.content))
            elif msg.type == "ai":
                messages.append(AIMessage(content=msg.content))
        
        messages.append(HumanMessage(content=query))
        
        logger.debug(f"Sending messages to LLM: {messages}")
        
        # Get AI response
        ai_response = llm.invoke(messages)
        response_content = ai_response.content
        
        logger.debug(f"Received response from LLM: {response_content}")

        # Save to chat history
        chat_history.add_user_message(query)
        chat_history.add_ai_message(response_content)

        return jsonify({
            'response': response_content,
            'session_id': session_id
        })

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
