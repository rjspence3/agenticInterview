# Demo Execution Commands for Chrome DevTools MCP

These are copy-paste ready prompts to execute the demo using Claude with Chrome DevTools MCP.

---

## Setup Verification

**Prompt 1: Initial Load**
```
Navigate to http://localhost:8501 and take a screenshot. Check the console for any JavaScript errors and report what you see on the page.
```

---

## Part 1: Admin Dashboard Demo

**Prompt 2: Admin View Overview**
```
Click on the sidebar element that says "Admin" to navigate to the Admin view. Wait for the page to load, then take a screenshot. Tell me what tabs you see at the top of the admin section.
```

**Prompt 3: People Management**
```
In the Admin view, click on the "People Management" tab if not already selected. Take a screenshot showing the list of people and the add person form. Then:
1. Find the "Name" input field and fill it with "Demo Candidate"
2. Find the "Email" input field and fill it with "demo@example.com"
3. Find the "Role" input field and fill it with "Software Engineer"
4. Find the "Department" input field and fill it with "Engineering"
5. Click the "Add Person" button
6. Take a screenshot of the result
```

**Prompt 4: Template Management**
```
Click on the "Template Management" tab in the Admin view. Take a screenshot showing the list of templates. Click to expand one of the templates to show its questions, then take another screenshot.
```

**Prompt 5: Lens Management**
```
Click on the "Lens Management" tab. Take a screenshot showing the available lenses. Find and expand the "Debugging Process" lens configuration, then take a screenshot showing its criteria.
```

**Prompt 6: Live Sessions Tab**
```
Click on the "Live Sessions" tab. Take a screenshot. Note whether there are any active sessions or if it shows an empty state message.
```

---

## Part 2: Interviewer View Demo

**Prompt 7: Question Bank**
```
Click on "Interviewer View" in the sidebar. Wait for the page to load and take a screenshot of the Question Bank Manager. Tell me how many questions are currently in the bank.
```

**Prompt 8: Create Question**
```
In the Interviewer View, find the "Add New Question" form and:
1. Fill the question text area with: "What is the difference between == and === in JavaScript?"
2. Select "JavaScript" from the competency dropdown (or type it if it's a text field)
3. Select "Easy" for difficulty
4. In the keypoints field, enter: "type coercion, strict equality, loose equality, type checking"
5. Click the "Add Question" button
6. Take a screenshot showing the result
```

---

## Part 3: Classic Interview Demo

**Prompt 9: Start Classic Interview**
```
Click on "Interviewee View" in the sidebar. On the interview setup page:
1. Select any person from the Person dropdown
2. Select "Python Developer L2" from the Template dropdown
3. Select "Classic Interview" for the interview mode
4. Click "Start Interview"
5. Wait for the first question to appear
6. Take a screenshot of the interview question display
```

**Prompt 10: Submit Answer**
```
In the active interview, find the answer text area and fill it with:
"Lists in Python are mutable sequences that use square brackets []. Tuples are immutable sequences that use parentheses (). Lists can be modified after creation but tuples cannot. Tuples are generally more memory efficient and faster to iterate."

Click the "Submit Answer" button. Wait for the evaluation to complete (look for a score to appear), then take a screenshot showing the evaluation results including score, mastery level, and feedback.
```

**Prompt 11: Continue Interview**
```
If there's a "Next Question" button, click it to proceed to the next question. Take a screenshot of the new question. You can submit a brief answer like "I would use proper error handling with try/except blocks." and take a screenshot of that evaluation too.
```

---

## Part 4: Chat Interview Demo

**Prompt 12: Start Chat Interview**
```
Click on "Interviewee View" in the sidebar. On the setup page:
1. Select any person
2. Select any template
3. Select "Chat Interview" for the interview mode
4. Click "Start Interview"
5. Wait for the chat interface to load
6. Take a screenshot showing the chat UI with the first question appearing as a message
```

**Prompt 13: Chat Interaction**
```
In the chat interview, find the chat input field at the bottom of the screen. Type:
"I would approach this problem by first understanding the requirements, then breaking it down into smaller components, and finally implementing each part with proper testing."

Press Enter or click send. Wait for the response to appear (including evaluation feedback), then take a screenshot showing the conversation flow.
```

---

## Part 5: Raise Hand Feature Demo

**Prompt 14: Raise Hand**
```
If you're in an active chat interview, look for a "Raise Hand" button (usually has a hand emoji). Click it. Take a screenshot showing the raised hand indicator and any status messages that appear.
```

**Prompt 15: Check Admin Live Sessions**
```
Open a new browser tab or navigate to Admin > Live Sessions. Take a screenshot showing the active sessions list. Look for any session with a "HAND" indicator showing someone has raised their hand.
```

**Prompt 16: Admin Join Session** (if there's an active session)
```
In the Live Sessions tab, if there's an active session with a "Join" button, click it. Take a screenshot of the admin session control interface showing:
- The transcript
- Message input field
- Control buttons (Skip Question, End Interview, Resume & Leave)
```

---

## Part 6: Reports Demo

**Prompt 17: Reports Overview**
```
Click on "Reports" in the sidebar navigation. Take a screenshot of the Reports dashboard showing:
- Any filter options at the top
- The list of completed sessions
- Any analytics charts if visible
```

**Prompt 18: Session Detail**
```
In the Reports view, click on any completed session to view its details. Take a screenshot showing the session detail page with transcript, evaluations, and any lens results.
```

**Prompt 19: Export Functionality**
```
Look for export buttons in the Reports view (either "Export CSV" or "Export JSON"). Take a screenshot showing these export options. If possible, click one to trigger a download.
```

---

## Part 7: Final Summary

**Prompt 20: Feature Summary**
```
Navigate back to the main page (click on the app title or refresh). Take a final screenshot and provide a summary of all the features you observed during this demo:
1. Admin capabilities
2. Interview modes
3. Real-time features
4. Reporting features
```

---

## Quick Reference: MCP Tool Names

| Action | MCP Tool |
|--------|----------|
| Go to URL | `navigate_page` |
| Click element | `click` |
| Type text | `fill` |
| Take screenshot | `take_screenshot` |
| Wait for element | `wait_for` |
| Run JavaScript | `evaluate_script` |
| Check console | `list_console_messages` |
| Get page snapshot | `take_snapshot` |

---

## Automated Full Demo (Single Prompt)

**Complete Demo Prompt:**
```
Run a comprehensive demo of the Agentic Interview System at http://localhost:8501.

Please execute the following steps, taking screenshots at each major step:

1. ADMIN FEATURES
   - Navigate to Admin view
   - Show all 4 tabs (People, Templates, Lenses, Live Sessions)
   - Create a test person named "Demo User" with email "demo@test.com"

2. INTERVIEWER VIEW
   - Navigate to Interviewer View
   - Show the question bank

3. CHAT INTERVIEW
   - Navigate to Interviewee View
   - Start a Chat Interview with any person/template
   - Answer one question in the chat interface
   - Click the Raise Hand button if visible

4. REPORTS
   - Navigate to Reports view
   - Show the session list and any analytics

Take screenshots at each step and summarize what you observe. Report any errors you encounter.
```

---

*These commands are designed for use with Claude and the Chrome DevTools MCP server.*
