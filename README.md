# CampusCopilot: Your AI Wingman for College Life

CampusCopilot is an AI assistant designed specifically for college students. It helps with campus information, schedule management, finding food options, and even detects when you need a chai break!

## Features

- **FAQ Answering**: Get quick answers about college facilities, schedules, and policies
- **Smart Reminders**: Set and manage reminders for assignments, exams, and other deadlines
- **Food Recommendations**: Find the best food options near your campus location
- **Chai Break Detection**: Detects when you might need a break and suggests one
- **Form Assistance**: Helps with KYC, tax, and visa form requirements
- **Conversation Memory**: Remembers context from previous interactions

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/campuscopilot.git
cd campuscopilot
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with the following:
```
GOOGLE_API_KEY=your_google_api_key
HUGGINGFACE_API_KEY=your_huggingface_api_key
```

## Usage

1. Run the Streamlit app:
```bash
streamlit run enhanced_campus_copilot.py
```

2. Open your browser and go to `http://localhost:8501`

3. Start chatting with CampusCopilot!

## Example Queries

- "When is the next exam?"
- "Remind me to submit my assignment by May 5th at 10 PM"
- "Where's the best dosa near hostel?"
- "I need a chai break"
- "Help me with KYC form"
- "Show my reminders"

## Customization

You can customize CampusCopilot by editing the following data in `app.py`:

- `faq_data`: Add your college-specific FAQs
- `timetable`: Update with your actual academic schedule
- `form_assistance`: Modify form requirements based on your institution

## Future Enhancements

- Voice interaction using Whisper
- WhatsApp notifications via Twilio
- Integration with Google Calendar
- Support for college-specific APIs
- Personalized learning recommendations

## License

MIT

## Acknowledgements

- Built with Streamlit and LangChain
- Uses Mistral AI's Mixtral model for intelligence
