# Inconspicuous

Inconspicuous is a lightweight, stealth-focused desktop AI assistant built in Python and powered by the Groq API. It is designed to provide fast responses through a clean and minimal interface while remaining unobtrusive during your workflow.

One of its primary features is that the chat window becomes invisible during screen sharing, allowing presentations and demonstrations without exposing the assistant on the shared screen.

The application intentionally avoids unnecessary complexity such as persistent chat history or additional workspace management, focusing solely on delivering a fast and seamless conversational experience.

## Features

- Built entirely in Python
- Powered by the Groq API
- Minimal and responsive interface
- No persistent chat history
- Automatically invisible during screen sharing
- System tray integration
- Session restoration when reopened from the system tray

---

## Prerequisites

Before running the application, you will need:

- Python 3.10 or newer
- A Groq API Key

---

## Getting a Groq API Key

1. Visit the Groq Console:

   https://console.groq.com/

2. Sign in or create an account.

3. Generate a new API key.

4. In the project root directory, create a file named:

```
.env
```

5. Add the following line to the file:

```env
GROQ_API_KEY=your_api_key_here
```

Replace `your_api_key_here` with your actual Groq API key.

The application will automatically load the API key during startup.

---

## Installation

Clone the repository.

```bash
git clone https://github.com/mejatinrajani/Inconspicious.git
```

Move into the project directory.

```bash
cd Inconspicuous
```

Install the required dependencies.

```bash
pip install -r requirements.txt
```

Run the application.

```bash
python main.py
```

---

## Using the Application

After launching the application, it minimizes to the system tray.

As shown in the screenshot below, locate the upward arrow (`^`) on the Windows taskbar to open the hidden system tray icons.

Inside the tray, a green shoe icon represents Inconspicuous.

Click the green shoe icon to reopen the application at any time.

When you close the window using the application's **Cut** button, the application is **not terminated**. Instead, it minimizes back to the system tray while preserving your current chat session.

Reopening the application from the tray restores the conversation exactly as you left it.

If the application is terminated forcefully, or the background process is stopped, the session ends and the chat history is discarded. The next launch starts a fresh conversation.

---

## Screen Sharing

Inconspicuous is designed to remain invisible during screen sharing, allowing you to present or share your screen without displaying the assistant window.

---

## Project Structure

```
.
├── assets/
├── components/
├── core/
├── ui/
├── main.py
├── requirements.txt
└── .env
```

---

## Notes

- Chat sessions exist only while the application is running.
- Closing the window using the **Cut** button preserves the current session.
- Forcefully terminating the application clears the session.
- Ensure your `.env` file contains a valid Groq API key before launching the application.

---

## License

This project is intended for educational and personal use unless otherwise specified.