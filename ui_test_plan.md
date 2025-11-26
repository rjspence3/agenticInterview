# UI Test Plan - Agentic Interview System

## Overview

This test plan uses [Chrome DevTools MCP](https://github.com/ChromeDevTools/chrome-devtools-mcp) to verify all UI components work correctly for all user types. The MCP server enables automated browser testing with capabilities like DOM inspection, network analysis, console log access, and user interaction simulation.

## Setup

### 1. Install Chrome DevTools MCP

```bash
# For Claude Code
claude mcp add chrome-devtools npx chrome-devtools-mcp@latest

# For VS Code / Copilot
code --add-mcp '{"name":"chrome-devtools","command":"npx","args":["chrome-devtools-mcp@latest"]}'
```

### 2. Start the Application

```bash
streamlit run app.py --server.port 8501
```

### 3. Launch Chrome with Debugging

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# Or use the MCP server's auto-launch feature
```

---

## User Types

| User Type | View | Primary Functions |
|-----------|------|-------------------|
| **Interviewer** | Interviewer View | Create/edit questions, manage question bank |
| **Interviewee** | Interviewee View | Take interviews (classic or chat), raise hand for help |
| **Admin** | Admin View | Manage people, templates, lenses, monitor live sessions |
| **Analyst** | Reports View | View session history, export data |

---

## Test Suites

### Suite 1: Navigation & Layout Tests

**Objective:** Verify main navigation works and views render correctly.

| ID | Test Case | Steps | Expected Result | MCP Commands |
|----|-----------|-------|-----------------|--------------|
| NAV-001 | App loads successfully | Navigate to localhost:8501 | Page loads without errors | `navigate_to`, `get_console_logs` |
| NAV-002 | Sidebar renders | Check sidebar visibility | Sidebar with navigation options visible | `take_screenshot`, `get_page_info` |
| NAV-003 | View switching - Interviewer | Click "Interviewer View" | Interviewer view content displays | `click_element`, `wait_for_navigation` |
| NAV-004 | View switching - Interviewee | Click "Interviewee View" | Interviewee view content displays | `click_element`, `wait_for_navigation` |
| NAV-005 | View switching - Reports | Click "Reports" | Reports view content displays | `click_element`, `wait_for_navigation` |
| NAV-006 | View switching - Admin | Click "Admin" | Admin view content displays | `click_element`, `wait_for_navigation` |
| NAV-007 | Evaluator mode toggle | Toggle between Heuristic/LLM | Mode indicator updates | `click_element`, `get_page_info` |

---

### Suite 2: Interviewer View Tests

**Objective:** Verify question creation and management functionality.

| ID | Test Case | Steps | Expected Result | MCP Commands |
|----|-----------|-------|-----------------|--------------|
| INT-001 | View loads | Navigate to Interviewer View | "Question Bank Manager" header visible | `navigate_to`, `get_page_info` |
| INT-002 | Empty state display | View with no questions | "No questions" message shown | `get_page_info` |
| INT-003 | Add question form visibility | Check form elements | Text area, competency, difficulty, keypoints fields visible | `take_screenshot` |
| INT-004 | Create question - valid | Fill all fields, submit | Question added to list, success message | `fill_input`, `click_element`, `wait_for_element` |
| INT-005 | Create question - empty text | Submit without question text | Error message "required" displayed | `click_element`, `get_page_info` |
| INT-006 | Create question - no keypoints | Submit without keypoints | Question created (keypoints optional) | `fill_input`, `click_element` |
| INT-007 | Question list display | After adding questions | Questions shown in expandable list | `get_page_info` |
| INT-008 | Edit question | Click edit, modify, save | Question updated in list | `click_element`, `fill_input`, `click_element` |
| INT-009 | Delete question | Click delete on question | Question removed from list | `click_element`, `wait_for_element` |
| INT-010 | Competency options | Check competency dropdown | Options: Python, System Design, etc. | `get_select_options` |
| INT-011 | Difficulty options | Check difficulty dropdown | Options: Easy, Medium, Hard | `get_select_options` |

---

### Suite 3: Interviewee View Tests - Setup

**Objective:** Verify interview setup and session creation.

| ID | Test Case | Steps | Expected Result | MCP Commands |
|----|-----------|-------|-----------------|--------------|
| IEE-001 | View loads | Navigate to Interviewee View | "Start New Interview" header visible | `navigate_to`, `get_page_info` |
| IEE-002 | Person dropdown populated | Check person selector | List of available people shown | `get_select_options` |
| IEE-003 | Template dropdown populated | Check template selector | List of available templates shown | `get_select_options` |
| IEE-004 | Start interview - valid | Select person, template, start | Interview session created, first question displays | `fill_input`, `click_element`, `wait_for_navigation` |
| IEE-005 | Start interview - no person | Click start without person | Error message displayed | `click_element`, `get_page_info` |
| IEE-006 | Start interview - no template | Click start without template | Error message displayed | `click_element`, `get_page_info` |

---

### Suite 4: Interviewee View Tests - Active Interview

**Objective:** Verify interview Q&A flow works correctly.

| ID | Test Case | Steps | Expected Result | MCP Commands |
|----|-----------|-------|-----------------|--------------|
| IEE-010 | Question display | During active interview | Question text, competency, difficulty visible | `get_page_info`, `take_screenshot` |
| IEE-011 | Progress indicator | Check progress bar | Progress shows "Question X of Y" | `get_page_info` |
| IEE-012 | Answer input | Check answer field | Text area visible with placeholder | `get_page_info` |
| IEE-013 | Submit answer - valid | Enter answer, submit | Answer evaluated, next question or complete | `fill_input`, `click_element`, `wait_for_element` |
| IEE-014 | Submit answer - empty | Submit without answer | Error "Please provide an answer" | `click_element`, `get_page_info` |
| IEE-015 | Evaluation display | After submitting answer | Score, feedback, keypoint coverage shown | `get_page_info`, `take_screenshot` |
| IEE-016 | Next question navigation | After evaluation | Auto-advances or shows next button | `wait_for_element`, `get_page_info` |
| IEE-017 | Question sequence | Complete multiple questions | Questions served in correct order | Repeat IEE-013 |

---

### Suite 5: Interviewee View Tests - Completion

**Objective:** Verify interview completion and results display.

| ID | Test Case | Steps | Expected Result | MCP Commands |
|----|-----------|-------|-----------------|--------------|
| IEE-020 | Completion detection | Answer all questions | "Interview Complete" header appears | `wait_for_element`, `get_page_info` |
| IEE-021 | Summary display | On completion page | Overall summary text visible | `get_page_info` |
| IEE-022 | Detailed results | Check results section | Expandable sections per question | `get_page_info` |
| IEE-023 | Score display | In results | Score shown as X/100 with mastery label | `get_page_info` |
| IEE-024 | Keypoint coverage | In results | Green checkmarks for covered, red X for missed | `take_screenshot` |
| IEE-025 | Start new interview button | Click "Start New Interview" | Returns to setup page | `click_element`, `wait_for_navigation` |
| IEE-026 | Lens analysis button | If LLM mode enabled | "Run Lens Analysis" button visible | `get_page_info` |

---

### Suite 6: Admin View Tests - People Management

**Objective:** Verify person CRUD operations.

| ID | Test Case | Steps | Expected Result | MCP Commands |
|----|-----------|-------|-----------------|--------------|
| ADM-001 | People tab visible | Navigate to Admin | "People Management" tab available | `get_page_info` |
| ADM-002 | People list display | View people section | Table of existing people shown | `get_page_info` |
| ADM-003 | Add person form | Check form fields | Name, email, role, department fields | `get_page_info` |
| ADM-004 | Create person - valid | Fill form, submit | Person added to list | `fill_input`, `click_element`, `wait_for_element` |
| ADM-005 | Create person - invalid email | Enter bad email format | Validation error shown | `fill_input`, `click_element`, `get_page_info` |
| ADM-006 | Create person - missing name | Submit without name | "Name is required" error | `click_element`, `get_page_info` |
| ADM-007 | Edit person | Click edit, modify, save | Person details updated | `click_element`, `fill_input`, `click_element` |
| ADM-008 | Deactivate person | Click deactivate | Person marked inactive | `click_element`, `get_page_info` |

---

### Suite 7: Admin View Tests - Template Management

**Objective:** Verify template CRUD operations.

| ID | Test Case | Steps | Expected Result | MCP Commands |
|----|-----------|-------|-----------------|--------------|
| ADM-010 | Templates tab visible | Navigate to Admin | "Template Management" tab available | `get_page_info` |
| ADM-011 | Template list display | View templates section | List of existing templates | `get_page_info` |
| ADM-012 | Create template form | Check form fields | Name, description, questions fields | `get_page_info` |
| ADM-013 | Create template - valid | Fill form with questions | Template created with questions | `fill_input`, `click_element`, `wait_for_element` |
| ADM-014 | Create template - no name | Submit without name | Validation error | `click_element`, `get_page_info` |
| ADM-015 | Add question to template | Click add question button | New question row appears | `click_element`, `get_page_info` |
| ADM-016 | Remove question from template | Click remove on question | Question row removed | `click_element`, `get_page_info` |
| ADM-017 | Question ordering | Drag/reorder questions | Order index updates | `drag_element`, `get_page_info` |
| ADM-018 | Edit template | Click edit, modify, save | Template updated | `click_element`, `fill_input`, `click_element` |
| ADM-019 | Version template | Edit existing template | New version created | `click_element`, `get_page_info` |

---

### Suite 8: Admin View Tests - Lens Management

**Objective:** Verify lens configuration functionality.

| ID | Test Case | Steps | Expected Result | MCP Commands |
|----|-----------|-------|-----------------|--------------|
| ADM-020 | Lens tab visible | Navigate to Admin | "Lens Management" tab available | `get_page_info` |
| ADM-021 | Lens list display | View lens section | List of configured lenses | `get_page_info` |
| ADM-022 | Create lens form | Check form fields | Name, description, criteria fields | `get_page_info` |
| ADM-023 | Create lens - valid | Fill form with criteria | Lens created | `fill_input`, `click_element` |
| ADM-024 | Add criterion | Click add criterion | New criterion row appears | `click_element`, `get_page_info` |
| ADM-025 | Criterion validation | Submit with invalid criterion | Validation error shown | `click_element`, `get_page_info` |
| ADM-026 | Edit lens | Click edit, modify, save | Lens config updated | `click_element`, `fill_input`, `click_element` |
| ADM-027 | Toggle lens active | Click toggle | Active status changes | `click_element`, `get_page_info` |
| ADM-028 | Example lens configs | Click example buttons | Pre-filled config loaded | `click_element`, `get_page_info` |

---

### Suite 9: Reports View Tests

**Objective:** Verify session history and export functionality.

| ID | Test Case | Steps | Expected Result | MCP Commands |
|----|-----------|-------|-----------------|--------------|
| RPT-001 | Reports view loads | Navigate to Reports | Session history visible | `navigate_to`, `get_page_info` |
| RPT-002 | Session list display | View sessions section | Table of past sessions | `get_page_info` |
| RPT-003 | Session filtering | Apply date filter | Filtered results shown | `fill_input`, `click_element`, `get_page_info` |
| RPT-004 | Session detail view | Click on session row | Detailed session view opens | `click_element`, `wait_for_navigation` |
| RPT-005 | Session detail content | In detail view | Q&A transcript, scores visible | `get_page_info` |
| RPT-006 | Export CSV | Click "Export CSV" | CSV file downloads | `click_element`, `check_download` |
| RPT-007 | Export JSON | Click "Export JSON" | JSON file downloads | `click_element`, `check_download` |
| RPT-008 | Lens results display | In session with lens results | Lens analysis shown | `get_page_info` |

---

### Suite 10: Error Handling & Edge Cases

**Objective:** Verify graceful error handling.

| ID | Test Case | Steps | Expected Result | MCP Commands |
|----|-----------|-------|-----------------|--------------|
| ERR-001 | Network error handling | Disconnect network during action | User-friendly error message | `get_console_logs`, `get_page_info` |
| ERR-002 | Session timeout | Let session expire | Graceful redirect/message | `wait`, `get_page_info` |
| ERR-003 | Invalid form XSS | Enter `<script>` in input | Input sanitized, no XSS | `fill_input`, `click_element`, `get_page_info` |
| ERR-004 | Long text input | Enter 10000+ chars | Input truncated or rejected | `fill_input`, `get_page_info` |
| ERR-005 | Database unavailable | Test with DB disabled | Fallback to legacy mode | `get_page_info` |
| ERR-006 | Concurrent session | Open in two tabs | Consistent state handling | `get_page_info` in both tabs |
| ERR-007 | Console errors | Throughout all tests | No JavaScript errors | `get_console_logs` |

---

### Suite 11: Responsive Design & Accessibility

**Objective:** Verify UI works across viewport sizes.

| ID | Test Case | Steps | Expected Result | MCP Commands |
|----|-----------|-------|-----------------|--------------|
| RES-001 | Desktop viewport | Set 1920x1080 | Layout correct | `set_viewport`, `take_screenshot` |
| RES-002 | Tablet viewport | Set 768x1024 | Layout adapts | `set_viewport`, `take_screenshot` |
| RES-003 | Mobile viewport | Set 375x667 | Mobile-friendly layout | `set_viewport`, `take_screenshot` |
| RES-004 | Focus indicators | Tab through elements | Visible focus rings | `keyboard_input`, `take_screenshot` |
| RES-005 | Color contrast | Analyze page | Sufficient contrast ratios | `accessibility_audit` |

---

### Suite 12: Performance Tests

**Objective:** Verify acceptable performance metrics.

| ID | Test Case | Steps | Expected Result | MCP Commands |
|----|-----------|-------|-----------------|--------------|
| PRF-001 | Initial load time | Navigate to app | < 3 seconds to interactive | `performance_start_trace`, `performance_end_trace` |
| PRF-002 | View switch time | Switch between views | < 500ms transition | `performance_measure` |
| PRF-003 | Form submission time | Submit question form | < 2 seconds response | `performance_measure` |
| PRF-004 | Large session load | Load session with 50+ Q&A | < 5 seconds render | `performance_measure` |
| PRF-005 | Memory usage | Extended session | No memory leaks | `performance_trace` |

---

### Suite 13: Chat Interview Tests

**Objective:** Verify chat-based interview flow works correctly.

| ID | Test Case | Steps | Expected Result | MCP Commands |
|----|-----------|-------|-----------------|--------------|
| CHT-001 | Chat mode selection | Select "Chat Interview" mode | Chat interface displays | `click_element`, `wait_for_element` |
| CHT-002 | Chat message display | Start chat interview | Messages appear as chat bubbles | `get_page_info`, `take_screenshot` |
| CHT-003 | Question as system message | View first question | Question appears with system avatar | `get_page_info` |
| CHT-004 | Answer submission | Type answer, press Enter | Answer appears in chat, evaluation starts | `fill_input`, `press_key`, `wait_for_element` |
| CHT-005 | Loading indicator | During LLM evaluation | "Evaluating..." spinner visible | `get_page_info`, `take_screenshot` |
| CHT-006 | Evaluation feedback | After evaluation | Score and feedback appear in chat | `wait_for_element`, `get_page_info` |
| CHT-007 | Auto-scroll | After new message | Chat scrolls to latest message | `evaluate_script` |
| CHT-008 | Progress indicator | During interview | "Question X of Y" visible in header | `get_page_info` |
| CHT-009 | Chat completion | Answer all questions | Completion message displays | `wait_for_element` |
| CHT-010 | Message persistence | Refresh page | Messages reload from transcript | `navigate_to`, `get_page_info` |

---

### Suite 14: Raise Hand Tests

**Objective:** Verify Raise Hand feature for interviewees.

| ID | Test Case | Steps | Expected Result | MCP Commands |
|----|-----------|-------|-----------------|--------------|
| RH-001 | Raise Hand button visible | During active interview | "Raise Hand" button visible | `get_page_info` |
| RH-002 | Raise hand action | Click "Raise Hand" | Hand raised indicator appears | `click_element`, `wait_for_element` |
| RH-003 | Hand raised indicator | After raising hand | "You've raised your hand" message | `get_page_info` |
| RH-004 | Lower hand button | When hand is raised | "Lower Hand" button visible | `get_page_info` |
| RH-005 | Lower hand action | Click "Lower Hand" | Hand indicator disappears | `click_element`, `wait_for_element` |
| RH-006 | Paused state | When admin joins | "Interview Paused" banner shows | `wait_for_element`, `get_page_info` |
| RH-007 | Chat disabled when paused | When admin present | Chat input is disabled | `get_page_info` |
| RH-008 | Admin message display | Admin sends message | Message appears with admin avatar | `wait_for_element`, `get_page_info` |
| RH-009 | Resume notification | Admin resumes interview | "Interview resumed" message | `wait_for_element` |
| RH-010 | Hand not visible when paused | When admin present | Raise Hand button hidden | `get_page_info` |

---

### Suite 15: Live Sessions Admin Tests

**Objective:** Verify Live Sessions admin functionality.

| ID | Test Case | Steps | Expected Result | MCP Commands |
|----|-----------|-------|-----------------|--------------|
| LS-001 | Live Sessions tab visible | Navigate to Admin | "Live Sessions" tab available | `get_page_info` |
| LS-002 | Active sessions list | View Live Sessions | Table of in-progress sessions | `get_page_info` |
| LS-003 | Hand raised indicator | When interviewee raises hand | "HAND" indicator visible | `wait_for_element`, `get_page_info` |
| LS-004 | Session details display | In sessions list | Person, template, question number shown | `get_page_info` |
| LS-005 | Join button | For each active session | "Join" button visible | `get_page_info` |
| LS-006 | Join session | Click "Join" | Session view opens, interview pauses | `click_element`, `wait_for_element` |
| LS-007 | Transcript display | After joining | Full transcript visible | `get_page_info`, `take_screenshot` |
| LS-008 | Admin message input | In joined session | Message input field visible | `get_page_info` |
| LS-009 | Send message | Type message, send | Message appears in transcript | `fill_input`, `click_element`, `wait_for_element` |
| LS-010 | Skip question button | In session control | "Skip Question" button visible | `get_page_info` |
| LS-011 | Skip question action | Click "Skip Question" | Next question loaded | `click_element`, `wait_for_element` |
| LS-012 | End interview button | In session control | "End Interview" button visible | `get_page_info` |
| LS-013 | Resume & Leave button | In session control | "Resume & Leave" button visible | `get_page_info` |
| LS-014 | Resume & Leave action | Click "Resume & Leave" | Returns to dashboard, interview resumes | `click_element`, `wait_for_navigation` |
| LS-015 | No duplicate join | Session already joined | Second admin can't join | `get_page_info` |

---

## Execution Commands

### Sample MCP Test Execution

```
# Navigate and verify page loads
Navigate to http://localhost:8501 and take a screenshot to verify the page loads correctly.

# Check console for errors
Get console logs and report any errors or warnings.

# Test form submission
Fill the "question_text" input with "What is recursion?",
select "Python" for competency,
select "Medium" for difficulty,
then click the submit button.
Wait for the success message to appear.

# Verify network requests
Check network requests for any failed API calls.

# Take screenshot of final state
Take a screenshot of the current page state.
```

### Running Full Test Suite

1. Start the application: `streamlit run app.py`
2. Open Claude Code with Chrome DevTools MCP enabled
3. Execute test cases by providing prompts like:
   - "Navigate to localhost:8501 and verify the Interviewer View loads correctly"
   - "Test the question creation flow by filling out the form and submitting"
   - "Check for any console errors on the current page"

---

## Test Data Requirements

### Pre-populated Data

Before running tests, ensure:

1. **People**: At least 3 people in database
   - Active interviewer
   - Active candidate
   - Inactive person (for filter testing)

2. **Templates**: At least 2 templates
   - Template with 3+ questions
   - Template with 1 question (edge case)

3. **Lenses**: At least 2 lens configurations
   - Debugging lens (default config)
   - Communication lens

4. **Sessions**: At least 3 sessions
   - Completed session with all questions answered
   - Completed session with lens analysis
   - In-progress session (for Live Sessions testing)

5. **Active Session for Live Tests**: At least 1 in-progress session
   - Person and template assigned
   - At least 1 question answered
   - Hand raised state (for Raise Hand testing)

---

## Success Criteria

- All test cases pass without errors
- No console errors during any test
- All user flows complete successfully
- Performance metrics within acceptable thresholds
- No visual regressions in screenshots

---

## Sources

- [Chrome DevTools MCP - Official Repository](https://github.com/ChromeDevTools/chrome-devtools-mcp)
- [Chrome DevTools MCP - Chrome for Developers Blog](https://developer.chrome.com/blog/chrome-devtools-mcp)
- [Chrome DevTools MCP - Addy Osmani's Blog](https://addyosmani.com/blog/devtools-mcp/)
- [Awesome MCP Servers - Chrome DevTools](https://mcpservers.org/servers/github-com-chromedevtools-chrome-devtools-mcp)

---

*Last updated: 2025-11-26*
