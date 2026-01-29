# Agentic Interview System - Demo Script

**Duration:** ~15-20 minutes
**Prerequisites:**
- App running: `streamlit run app.py --server.port 8501`
- Chrome with remote debugging: `/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222`
- Chrome DevTools MCP enabled

---

## Demo Overview

This demo showcases all features of the Agentic Interview System:
1. **Admin Dashboard** - People, Templates, Lenses, Live Sessions
2. **Interviewer View** - Question bank management
3. **Interviewee View** - Classic and Chat interview modes
4. **Raise Hand Feature** - Real-time admin assistance
5. **Reports** - Analytics and export

---

## Part 1: Initial Setup & Navigation

### 1.1 Launch and Take Screenshot
```
Navigate to http://localhost:8501 and take a screenshot to verify the app loads correctly.
Check the console for any errors.
```

### 1.2 Explore Sidebar Navigation
```
Take a screenshot showing the sidebar with all navigation options:
- Interviewer View
- Interviewee View
- Reports
- Admin

Also note the Evaluator Mode toggle (Heuristic vs LLM-Powered).
```

---

## Part 2: Admin Dashboard

### 2.1 Navigate to Admin View
```
Click on "Admin" in the sidebar navigation.
Take a screenshot of the Admin view showing the 4 tabs:
- People Management
- Template Management
- Lens Management
- Live Sessions
```

### 2.2 People Management
```
In the Admin view, ensure the "People Management" tab is selected.
Take a screenshot showing:
- The list of existing people
- The "Add New Person" form

Then fill out the form to create a new person:
- Name: "Demo Candidate"
- Email: "demo@example.com"
- Role: "Software Engineer"
- Department: "Engineering"

Click the "Add Person" button and verify the success message.
Take a screenshot of the updated people list.
```

### 2.3 Template Management
```
Click on the "Template Management" tab.
Take a screenshot showing:
- List of existing templates
- Template creation form

Click to expand one of the existing templates (e.g., "Python Developer L2").
Take a screenshot showing the questions within the template.
```

### 2.4 Lens Management
```
Click on the "Lens Management" tab.
Take a screenshot showing:
- List of configured lenses
- The lens configuration interface

Click to expand the "Debugging Process" lens to show its criteria configuration.
Take a screenshot of the lens criteria.
```

### 2.5 Live Sessions (Empty State)
```
Click on the "Live Sessions" tab.
Take a screenshot showing the empty state or any active sessions.
Note: This tab will show active interviews in real-time later in the demo.
```

---

## Part 3: Interviewer View

### 3.1 Navigate to Interviewer View
```
Click on "Interviewer View" in the sidebar.
Take a screenshot of the Question Bank Manager interface.
```

### 3.2 Create a New Question
```
Fill out the "Add New Question" form:
- Question Text: "Explain the difference between a list and a tuple in Python."
- Competency: Select "Python"
- Difficulty: Select "Easy"
- Keypoints: Enter "immutable, mutable, syntax brackets, performance"

Click "Add Question" and take a screenshot showing the question was added.
```

### 3.3 View Question Bank
```
Scroll down to view the question bank.
Take a screenshot showing all questions with their competencies and difficulties.
```

---

## Part 4: Classic Interview Flow

### 4.1 Start Classic Interview
```
Click on "Interviewee View" in the sidebar.
Take a screenshot of the interview setup page.

Select the following:
- Person: Choose any person from the dropdown
- Interview Template: Select "Python Developer L2"
- Interview Mode: Select "Classic Interview"

Click "Start Interview" button.
Take a screenshot of the first question displayed.
```

### 4.2 Answer a Question
```
In the answer text area, enter:
"A list in Python is mutable, meaning you can change its contents after creation.
It uses square brackets []. A tuple is immutable - once created, it cannot be modified.
It uses parentheses (). Tuples are generally faster for iteration due to their immutability."

Click "Submit Answer" and wait for the evaluation.
Take a screenshot showing:
- The score (0-100)
- Mastery label (strong/mixed/weak)
- Feedback text
- Keypoint coverage indicators
```

### 4.3 Progress Through Interview
```
Click "Next Question" to proceed.
Answer 1-2 more questions briefly to show the flow.
Take screenshots of each evaluation result.
```

### 4.4 View Completion Summary
```
After completing all questions (or click through quickly), take a screenshot of:
- The completion page
- Overall score
- Summary of all questions
- Option to run lens analysis
```

---

## Part 5: Chat Interview Mode

### 5.1 Start Chat Interview
```
Click on "Interviewee View" in the sidebar.
Select:
- Person: Choose a person
- Interview Template: Select any template
- Interview Mode: Select "Chat Interview"

Click "Start Interview".
Take a screenshot of the chat interface showing:
- Chat message area
- The first question as a system message
- Chat input at the bottom
- Progress indicator
```

### 5.2 Answer in Chat Mode
```
Type in the chat input:
"I would start by understanding the requirements, then break down the problem into smaller components."

Press Enter or click send.
Take a screenshot showing:
- Your message appearing as a user bubble
- Loading indicator while evaluation runs
- Evaluation feedback appearing in chat
```

### 5.3 Show Chat Flow
```
Answer 1-2 more questions in the chat.
Take a screenshot showing the conversational flow with multiple messages.
Note the automatic scrolling to latest messages.
```

---

## Part 6: Raise Hand Feature (Two-Window Demo)

**Note:** This requires two browser windows to demonstrate effectively.

### 6.1 Setup - Window 1 (Interviewee)
```
In Window 1, start a new Chat Interview.
Navigate to the active interview state.
Take a screenshot showing the "Raise Hand" button at the bottom.
```

### 6.2 Raise Hand
```
In Window 1, click the "Raise Hand" button.
Take a screenshot showing:
- The hand raised indicator
- The "Lower Hand" button that replaced it
```

### 6.3 Admin Sees Raised Hand - Window 2
```
In Window 2, navigate to Admin > Live Sessions tab.
Take a screenshot showing:
- The active session in the list
- The "HAND" indicator highlighted
- The "Join" button
```

### 6.4 Admin Joins Session
```
In Window 2, click "Join" on the session with raised hand.
Take a screenshot of the admin session view showing:
- Full transcript
- Admin message input
- Control buttons (Skip Question, End Interview, Resume & Leave)
- Session status showing "LIVE"
```

### 6.5 Admin Sends Message
```
In Window 2 (Admin), type a message:
"Hi! I see you raised your hand. How can I help you?"

Click Send.
Take a screenshot showing the message in the transcript.
```

### 6.6 Interviewee Sees Paused State
```
In Window 1 (Interviewee), take a screenshot showing:
- The "Interview Paused" banner
- The admin message appearing
- Disabled chat input
```

### 6.7 Admin Resumes Interview
```
In Window 2 (Admin), click "Resume & Leave".
Take a screenshot of Window 1 showing:
- Interview resumed notification
- Chat input re-enabled
```

---

## Part 7: Reports & Analytics

### 7.1 Navigate to Reports
```
Click on "Reports" in the sidebar.
Take a screenshot of the Reports dashboard showing:
- Filter options (date range, person, template)
- Session list
- Analytics section
```

### 7.2 View Analytics Charts
```
Scroll to the analytics section.
Take a screenshot showing:
- Score distribution histogram
- Department breakdown chart (if data available)
```

### 7.3 Session Detail View
```
Click on any completed session in the list.
Take a screenshot of the session detail page showing:
- Session metadata (person, template, date)
- Full transcript
- Question-by-question evaluations
- Lens analysis results (if available)
```

### 7.4 Export Data
```
Back on the Reports main page:
1. Click "Export CSV" button and note the download
2. Click "Export JSON" button on a session detail and note the download

Take a screenshot showing the export buttons.
```

---

## Part 8: Feature Highlights Recap

### 8.1 Evaluator Mode Toggle
```
In the sidebar, toggle between "Heuristic" and "LLM-Powered" evaluator modes.
Take a screenshot showing the toggle and explain:
- Heuristic: Fast, offline, keyword matching
- LLM-Powered: Semantic understanding, requires API key
```

### 8.2 Final Dashboard Overview
```
Take a final screenshot of the main dashboard/landing page.
Summarize the key features demonstrated:
1. Multi-role support (Interviewer, Interviewee, Admin, Analyst)
2. Dual interview modes (Classic and Chat)
3. Real-time admin supervision (Raise Hand + Live Sessions)
4. Flexible evaluation (Heuristic or LLM)
5. Lens-based analysis
6. Comprehensive reporting and export
```

---

## Quick Demo Commands Reference

### Navigation
```
Navigate to http://localhost:8501
Click on element with text "Admin"
Click on element with text "Interviewee View"
Click on element with text "Reports"
```

### Form Interactions
```
Fill the input with placeholder "Enter name" with "Demo User"
Fill the textarea with placeholder "Type your answer" with "My answer text"
Click on button with text "Submit"
Select option "Python" from dropdown
```

### Screenshots & Verification
```
Take a screenshot
Get console logs
Check for element with text "Success"
Wait for element with text "Score:"
```

### Timing
```
Wait for 3 seconds (for animations/loading)
Wait for element with class "stSpinner" to disappear
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Page not loading | Verify `streamlit run app.py` is running |
| Elements not found | Use `take_screenshot` to see current state |
| Slow responses | Increase wait times, check network tab |
| LLM evaluation fails | Switch to Heuristic mode or check API key |

---

## Demo Script Execution Checklist

- [ ] App running on localhost:8501
- [ ] Chrome launched with --remote-debugging-port=9222
- [ ] MCP connection established
- [ ] Initial screenshot captured
- [ ] Admin features demonstrated
- [ ] Classic interview completed
- [ ] Chat interview demonstrated
- [ ] Raise Hand flow shown
- [ ] Reports and export demonstrated
- [ ] Final summary screenshot

---

*Last Updated: 2025-11-26*
