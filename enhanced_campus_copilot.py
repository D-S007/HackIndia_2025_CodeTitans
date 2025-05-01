import streamlit as st
import langchain
from langchain.llms import HuggingFaceHub
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
import requests
import os
import re
import json
import datetime
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# Initialize session state for conversation memory
if 'memory' not in st.session_state:
    st.session_state.memory = ConversationBufferMemory()
    
if 'reminders' not in st.session_state:
    st.session_state.reminders = []
    
if 'chai_break_count' not in st.session_state:
    st.session_state.chai_break_count = 0
    
if 'last_chai_time' not in st.session_state:
    st.session_state.last_chai_time = None

# Simulated FAQ data
faq_data = {
    "when is the next exam?": "Exams start on May 10, 2025.",
    "what is the library schedule?": "Library is open from 8 AM to 10 PM daily.",
    "where is the hostel?": "Hostel is located at the north end of campus.",
    "library hours": "Library is open from 8 AM to 10 PM on weekdays, 10 AM to 8 PM on weekends.",
    "fee payment": "Fee payment deadline is May 15, 2025. You can pay online through the student portal.",
    "wifi password": "The campus WiFi password is updated monthly. Check the IT department's notice board.",
    "hostel curfew": "Hostel curfew is at 10 PM on weekdays and 11 PM on weekends."
}
# Simulated timetable
timetable = {
    "Assignment - Data Structures": "May 2, 2025, 10 PM",
    "Mid-term Exam - Operating Systems": "May 10, 2025, 9 AM",
    "Project Submission - Machine Learning": "May 12, 2025, 11:59 PM",
    "Final Exam - Database Management": "May 20, 2025, 2 PM"
}

# Simulated form assistance data
form_assistance = {
    "kyc": "For KYC verification, you need:\n1. ID proof (Aadhar/PAN/Passport)\n2. Address proof\n3. Recent photograph\nSubmit these at the admin office with form KYC-101.",
    "tax": "For tax form assistance, visit the finance office with your PAN card and Form 16. The office is open Monday to Friday, 10 AM to 4 PM.",
    "visa": "For visa form assistance, you need:\n1. Passport\n2. College ID\n3. Admission letter\n4. Bank statements\nVisit the International Student Office in Building B."
}

# Initialize LLM (Mistral via Hugging Face)
os.environ["HUGGINGFACEHUB_API_TOKEN"] = HUGGINGFACE_API_KEY
llm = HuggingFaceHub(repo_id="mistralai/Mixtral-8x7B-Instruct-v0.1", model_kwargs={"temperature": 0.7})

# Create conversation chain with memory
conversation = ConversationChain(
    llm=llm,
    memory=st.session_state.memory,
    verbose=True
)

# Function to handle FAQ queries
def answer_faq(query):
    query = query.lower().strip()
    
    # Check for exact or partial matches in FAQ data
    for q, a in faq_data.items():
        if q in query:
            return a
    
    # Check for timetable queries
    if any(word in query.lower() for word in ["assignment", "exam", "deadline", "due", "schedule"]):
        return get_timetable_info(query)
    
    # Check for form assistance queries
    if any(word in query.lower() for word in ["kyc", "tax", "visa", "form"]):
        return get_form_assistance(query)
    
    # Fallback to LLM
    prompt = f"""You are a college assistant named CampusCopilot. 
    Answer based on this FAQ data: {json.dumps(faq_data)}
    And this timetable: {json.dumps(timetable)}
    If you don't know the answer, say 'I don't have that information yet, but I can help you with other college-related questions!'
    Query: {query}"""
    
    try:
        response = llm(prompt)
        return response
    except Exception as e:
        return f"I'm having trouble connecting to my brain. Please try again later. Error: {str(e)}"

# Function to get timetable information
def get_timetable_info(query):
    response = "Here's what I found in your schedule:\n\n"
    
    # Convert timetable to a list of items with dates for sorting
    events = []
    for event, date_str in timetable.items():
        try:
            date_obj = datetime.strptime(date_str, "%B %d, %Y, %I %p")
            events.append((event, date_str, date_obj))
        except ValueError:
            events.append((event, date_str, None))  # Add events with invalid dates without parsing
    
    # Sort events by date
    events_with_dates = [(e, d, do) for e, d, do in events if do is not None]
    events_with_dates.sort(key=lambda x: x[2])
    
    # Check for specific queries
    if "next" in query:
        now = datetime.now()
        future_events = [(e, d) for e, d, do in events_with_dates if do > now]
        if future_events:
            next_event, next_date = future_events[0]
            return f"Your next event is: {next_event} on {next_date}"
        else:
            return "No upcoming events found in your schedule."
    
    # Default: return all events
    for event, date_str, _ in events_with_dates:
        response += f"- {event}: {date_str}\n"
    
    return response

# Function to handle form assistance
def get_form_assistance(query):
    query = query.lower()
    if "kyc" in query:
        return form_assistance["kyc"]
    elif "tax" in query:
        return form_assistance["tax"]
    elif "visa" in query:
        return form_assistance["visa"]
    else:
        return "I can help with KYC, tax, and visa forms. Please specify which one you need assistance with."

# Function to handle reminders
def set_reminder(query):
    # More sophisticated pattern matching for dates and tasks
    patterns = [
        r"remind me(?:[ ]?:about)?\s+(.*?)(?:by|on|at)\s+([A-Za-z]+\s+\d{1,2},\s*\d{4}(?:,?\s*\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)?)",
        r"remind me(?:[ ]?:about)?\s+(.*?)(?:by|on|at)\s+(\d{1,2}/\d{1,2}/\d{4}(?:\s*\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)?)",
        r"set a reminder(?:[ ]?:for)?\s+(.*?)(?:by|on|at)\s+([A-Za-z]+\s+\d{1,2},\s*\d{4}(?:,?\s*\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)?)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            task = match.group(1).strip()
            due_date = match.group(2).strip()
            
            # Try to parse the date
            try:
                # Handle multiple date formats
                date_formats = [
                    "%B %d, %Y, %I %p",
                    "%B %d, %Y, %I:%M %p",
                    "%B %d, %Y %I %p",
                    "%B %d, %Y %I:%M %p",
                    "%B %d, %Y",
                    "%m/%d/%Y, %I %p",
                    "%m/%d/%Y, %I:%M %p",
                    "%m/%d/%Y %I %p",
                    "%m/%d/%Y %I:%M %p",
                    "%m/%d/%Y"
                ]
                
                parsed_date = None
                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(due_date, fmt)
                        break
                    except ValueError:
                        continue
                
                if parsed_date:
                    # Create the reminder
                    reminder = {
                        "task": task,
                        "due_date": due_date,
                        "timestamp": parsed_date.timestamp(),
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.reminders.append(reminder)
                    return f"✅ Reminder set: {task} (Due: {due_date})"
            except Exception as e:
                pass  # Continue to next pattern if this one fails
    
    # If we get here, we couldn't parse the reminder
    return "I couldn't understand that reminder format. Try something like 'Remind me about my assignment by May 2, 2025, 10 PM'."

# Function to show reminders
def show_reminders():
    if not st.session_state.reminders:
        return "No reminders set. Use 'Remind me about...' to set some!"
    
    # Sort reminders by due date
    sorted_reminders = sorted(st.session_state.reminders, key=lambda x: x.get("timestamp", 0))
    
    response = "📅 **Your Reminders:**\n\n"
    for idx, r in enumerate(sorted_reminders, 1):
        response += f"{idx}. {r['task']} (Due: {r['due_date']})\n"
    
    return response

# Function to detect and handle chai breaks
def detect_chai_break(query):
    chai_keywords = ["chai", "tea", "coffee", "break", "tired", "rest", "caffeine", "need energy"]
    
    # Check if query contains chai break keywords
    if any(keyword in query.lower() for keyword in chai_keywords):
        current_time = datetime.now()
        
        # Check if this is the first chai break
        if st.session_state.last_chai_time is None:
            st.session_state.chai_break_count += 1
            st.session_state.last_chai_time = current_time
            return True, f"Chai break #{st.session_state.chai_break_count} detected! Taking a break is important for productivity. Enjoy your chai! ☕"
        
        # Check if enough time has passed since last chai break (at least 2 hours)
        time_since_last = current_time - st.session_state.last_chai_time
        if time_since_last > timedelta(hours=2):
            st.session_state.chai_break_count += 1
            st.session_state.last_chai_time = current_time
            return True, f"Chai break #{st.session_state.chai_break_count} detected! Taking a break is important for productivity. Enjoy your chai! ☕"
        else:
            minutes_left = 120 - (time_since_last.total_seconds() / 60)
            return False, f"You had a chai break recently. Consider waiting about {int(minutes_left)} more minutes for your next one. Too much caffeine might disrupt your sleep! 😊"
    
    return False, ""

# Function to get food recommendations
def get_food_recommendation(query):
    # Extract location from query or use default
    location_match = re.search(r"near\s+(\w+)", query, re.IGNORECASE)
    location = location_match.group(1) if location_match else "hostel"
    
    # Map locations to coordinates (simulated)
    location_coords = {
        "hostel": (12.9716, 77.5946),
        "library": (12.9720, 77.5950),
        "campus": (12.9718, 77.5948),
        "college": (12.9718, 77.5948)
    }
    
    lat, lng = location_coords.get(location.lower(), (12.9716, 77.5946))
    radius = 5000  # 5km
    
    # Extract food type from query
    food_types = {
        "dosa": "dosas",
        "coffee": "coffee",
        "pizza": "pizza",
        "burger": "burgers",
        "chinese": "chinese food",
        "indian": "indian food",
        "south indian": "south indian",
        "north indian": "north indian"
    }
    
    keyword = "food"  # default
    for food, search_term in food_types.items():
        if food in query.lower():
            keyword = search_term
            break
    
    # Simulate API call (in a real app, would use actual Google Places API)
    # For this demo, return mock data based on the food type
    mock_places = {
        "dosas": [
            {"name": "Udupi Grand", "rating": 4.5, "vicinity": "100m from hostel", "price_level": 2},
            {"name": "MTR Express", "rating": 4.7, "vicinity": "500m from hostel", "price_level": 3},
            {"name": "Shree Sagar", "rating": 4.2, "vicinity": "1km from hostel", "price_level": 1}
        ],
        "coffee": [
            {"name": "Third Wave Coffee", "rating": 4.6, "vicinity": "200m from hostel", "price_level": 3},
            {"name": "Café Coffee Day", "rating": 4.0, "vicinity": "300m from hostel", "price_level": 2},
            {"name": "Starbucks", "rating": 4.3, "vicinity": "1.2km from hostel", "price_level": 3}
        ],
        "food": [
            {"name": "Campus Canteen", "rating": 3.9, "vicinity": "50m from hostel", "price_level": 1},
            {"name": "Food Court", "rating": 4.1, "vicinity": "400m from hostel", "price_level": 2},
            {"name": "Bistro Bytes", "rating": 4.4, "vicinity": "800m from hostel", "price_level": 3}
        ],
        "pizza": [
            {"name": "Domino's Pizza", "rating": 4.2, "vicinity": "600m from hostel", "price_level": 2},
            {"name": "Pizza Hut", "rating": 4.0, "vicinity": "900m from hostel", "price_level": 2},
            {"name": "Italian Pizzeria", "rating": 4.6, "vicinity": "1.5km from hostel", "price_level": 3}
        ],
        "burgers": [
            {"name": "Burger King", "rating": 4.1, "vicinity": "700m from hostel", "price_level": 2},
            {"name": "McDonald's", "rating": 3.9, "vicinity": "850m from hostel", "price_level": 1},
            {"name": "Gourmet Burger Kitchen", "rating": 4.5, "vicinity": "1.3km from hostel", "price_level": 3}
        ]
    }
    
    # Get places for the requested food type, or default to generic food
    places = mock_places.get(keyword, mock_places["food"])
    
    if not places:
        return f"No {keyword} places found near {location}. Try something else!"
    
    # Format the response
    response = f"🍽️ **Best {keyword} near {location}:**\n\n"
    for idx, place in enumerate(places, 1):
        name = place.get("name")
        vicinity = place.get("vicinity")
        rating = place.get("rating", "N/A")
        price = "₹" * place.get("price_level", 1) if place.get("price_level") else "₹"
        response += f"{idx}. **{name}** ({rating}/5) - {price}\n   {vicinity}\n\n"
    
    return response

# Streamlit UI
def main():
    st.set_page_config(page_title="CampusCopilot", page_icon="🎓", layout="wide")
    
    # Sidebar for navigation
    st.sidebar.image("https://via.placeholder.com/150x150.png?text=CC", width=150)
    st.sidebar.title("CampusCopilot")
    st.sidebar.write("Your AI wingman for college life!")
    
    # Create tabs for different functionalities
    tab1, tab2, tab3, tab4 = st.tabs(["Chat", "Reminders", "Schedule", "About"])
    
    with tab1:
        st.header("Chat with CampusCopilot 🤖")
        st.write("Ask me about exams, deadlines, campus facilities, or nearby food options!")
        
        # Display conversation history
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("What's on your mind?"):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Process the query and get response
            with st.chat_message("assistant"):
                # Check for chai break
                is_chai_break, chai_message = detect_chai_break(prompt)
                if is_chai_break:
                    response = chai_message
                # Check for reminders
                elif any(word in prompt.lower() for word in ["remind me", "set a reminder", "new reminder"]):
                    response = set_reminder(prompt)
                # Check for viewing reminders
                elif any(phrase in prompt.lower() for phrase in ["show my reminders", "list reminders", "what are my reminders"]):
                    response = show_reminders()
                # Check for food recommendations
                elif any(word in prompt.lower() for word in ["food", "dosa", "coffee", "pizza", "burger", "restaurant", "eat"]):
                    response = get_food_recommendation(prompt)
                # General FAQ handling
                else:
                    response = answer_faq(prompt)
                
                st.markdown(response)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    with tab2:
        st.header("Your Reminders 📝")
        
        # Display existing reminders as a table
        if st.session_state.reminders:
            # Convert reminders to DataFrame for better display
            reminders_df = pd.DataFrame(st.session_state.reminders)
            reminders_df = reminders_df[["task", "due_date", "created_at"]]
            reminders_df.columns = ["Task", "Due Date", "Created"]
            st.dataframe(reminders_df, use_container_width=True)
            
            # Add button to clear reminders
            if st.button("Clear All Reminders"):
                st.session_state.reminders = []
                st.experimental_rerun()
        else:
            st.info("No reminders set. Chat with CampusCopilot to set reminders!")
            st.write("Try saying: 'Remind me to submit my assignment by May 5, 2025, 10 PM'")
    
    with tab3:
        st.header("Academic Schedule 📅")
        
        # Display the timetable
        st.subheader("Upcoming Deadlines & Exams")
        schedule_df = pd.DataFrame(list(timetable.items()), columns=["Event", "Date"])
        st.dataframe(schedule_df, use_container_width=True)
    
    with tab4:
        st.header("About CampusCopilot")
        st.write("""
        CampusCopilot is your AI assistant for college life! I can help you with:
        
        - 📚 Campus information and FAQs
        - ⏰ Setting reminders for assignments and exams
        - 🍽️ Finding food options near campus
        - ☕ Detecting when you need a chai break
        - 📝 Assistance with KYC, tax, and visa forms
        
        I'm still learning and improving. Let me know how I can be more helpful!
        """)
        
        st.subheader("Sample Questions")
        st.write("""
        Try asking me:
        - "When is the next exam?"
        - "Remind me to submit my assignment by May 5th, 2025 at 10 PM"
        - "Where's the best dosa near hostel?"
        - "I need a chai break"
        - "Help me with KYC form"
        """)

if __name__ == "__main__":
    main()
