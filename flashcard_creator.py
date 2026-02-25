"""
AI Flashcard Creator using Google Gemini (FREE)
Updated version with new Google AI SDK
"""

import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load the API key from .env file
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Configure Gemini with new SDK
client = genai.Client(api_key=api_key)

def generate_flashcards(study_text, num_cards=5, difficulty="medium"):
    """
    Generate flashcards from study material
    """
    
    # Create the prompt for AI
    prompt = f"""
You are an expert teacher creating study flashcards.

Read this study material and create {num_cards} flashcards.
Difficulty level: {difficulty}

STUDY MATERIAL:
{study_text}

FORMAT (follow exactly):
Q1: [question here]
A1: [answer here]

Q2: [question here]
A2: [answer here]

Continue for all {num_cards} questions.
"""
    
    print("🤖 Generating flashcards...")
    
    # Send to Gemini AI using new SDK
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    
    # Parse the response
    flashcards = parse_flashcards(response.text)
    
    return flashcards

def parse_flashcards(text):
    """
    Convert AI response into structured flashcards
    """
    flashcards = []
    lines = text.strip().split('\n')
    
    current_question = None
    current_answer = None
    
    for line in lines:
        line = line.strip()
        
        # Look for questions (Q1:, Q2:, etc.)
        if line.startswith('Q') and ':' in line:
            # Save previous card
            if current_question and current_answer:
                flashcards.append({
                    "question": current_question,
                    "answer": current_answer
                })
            
            # Start new card
            current_question = line.split(':', 1)[1].strip()
            current_answer = None
        
        # Look for answers (A1:, A2:, etc.)
        elif line.startswith('A') and ':' in line:
            current_answer = line.split(':', 1)[1].strip()
    
    # Don't forget last card
    if current_question and current_answer:
        flashcards.append({
            "question": current_question,
            "answer": current_answer
        })
    
    return flashcards

def print_flashcards(flashcards):
    """
    Display flashcards nicely
    """
    print("\n" + "="*50)
    print("YOUR FLASHCARDS")
    print("="*50 + "\n")
    
    for i, card in enumerate(flashcards, 1):
        print(f"📝 Card {i}")
        print(f"Q: {card['question']}")
        print(f"A: {card['answer']}")
        print("-"*50 + "\n")

def save_flashcards(flashcards, filename="flashcards.txt"):
    """
    Save flashcards to a file
    """
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("="*50 + "\n")
        f.write("YOUR AI-GENERATED FLASHCARDS\n")
        f.write("="*50 + "\n\n")
        
        for i, card in enumerate(flashcards, 1):
            f.write(f"CARD {i}\n")
            f.write(f"Q: {card['question']}\n")
            f.write(f"A: {card['answer']}\n")
            f.write("-"*50 + "\n\n")
    
    print(f"✅ Saved {len(flashcards)} flashcards to {filename}")

# MAIN PROGRAM
if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════╗
    ║   AI FLASHCARD CREATOR (FREE VERSION)        ║
    ║   Powered by Google Gemini 2.0               ║
    ╚══════════════════════════════════════════════╝
    """)
    
    # Example study material
    study_notes = """
    Photosynthesis is the process by which plants convert light energy into chemical energy.
    It occurs in the chloroplasts of plant cells.
    The process has two main stages: light-dependent reactions and the Calvin cycle.
    
    Light-dependent reactions occur in the thylakoid membranes and require sunlight.
    They produce ATP and NADPH.
    Oxygen is released as a byproduct.
    
    The Calvin cycle occurs in the stroma and uses ATP and NADPH to convert CO2 into glucose.
    This is also called carbon fixation.
    """
    
    # Generate flashcards
    flashcards = generate_flashcards(study_notes, num_cards=5, difficulty="medium")
    
    # Display them
    print_flashcards(flashcards)
    
    # Save to file
    save_flashcards(flashcards)
    
    print("\n✨ Done! Check flashcards.txt for your saved flashcards!")