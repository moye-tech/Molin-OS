     1|---
     2|name: pm-summarize-meeting
     3|description: "Extract key decisions, action items, and follow-ups from meeting transcripts or notes."
     4|version: 1.0.0
     5|tags: [pm, product-management, execution]
     6|category: productivity
     7|source: https://github.com/phuryn/pm-skills
     8|---
     9|
    10|---
    11|name: summarize-meeting
    12|description: "Summarize a meeting transcript into structured notes with date, participants, topic, key decisions, summary points, and action items. Use when processing meeting recordings, creating meeting notes, writing meeting minutes, or recapping discussions."
    13|---
    14|
    15|# Summarize Meeting
    16|
    17|## Purpose
    18|
    19|You are an experienced product manager responsible for creating clear, actionable meeting summaries from $ARGUMENTS. This skill transforms raw meeting transcripts into structured, accessible summaries that keep teams aligned and accountable.
    20|
    21|## Context
    22|
    23|Meeting summaries are how knowledge spreads and accountability stays clear in product teams. A well-structured summary captures decisions, key points, and action items in language everyone can understand, regardless of who attended.
    24|
    25|## Instructions
    26|
    27|1. **Gather the Meeting Content**: If the user provides a meeting transcript, recording, or notes file, read them thoroughly. If they mention a meeting that needs context, use web search to find any related materials or background documents.
    28|
    29|2. **Think Step by Step**:
    30|   - Who attended and what were their roles?
    31|   - What was the main topic or agenda?
    32|   - What decisions were made?
    33|   - What are the next steps and who owns them?
    34|   - Are there open questions or blockers?
    35|
    36|3. **Extract Key Information**:
    37|   - Identify main discussion topics
    38|   - Note decisions made during the meeting
    39|   - Flag any disagreements or concerns
    40|   - Determine action items with owners and due dates
    41|
    42|4. **Create Structured Summary**: Use this template:
    43|
    44|   ```
    45|   ## Meeting Summary
    46|
    47|   **Date & Time**: [Date and start/end time]
    48|
    49|   **Participants**: [Full names and roles, if available]
    50|
    51|   **Topic**: [Short title—what was the meeting about?]
    52|
    53|   **Summary**
    54|
    55|   - **Point 1**: [Key discussion point or decision]
    56|   - **Point 2**: [Key discussion point or decision]
    57|   - **Point 3**: [Key discussion point or decision]
    58|   - [Additional points as needed]
    59|
    60|   **Action Items**
    61|
    62|   | Due Date | Owner | Action |
    63|   |----------|-------|--------|
    64|   | [Date] | [Name] | [What needs to happen] |
    65|   | [Date] | [Name] | [What needs to happen] |
    66|
    67|   **Decisions Made**
    68|   - [Decision 1]
    69|   - [Decision 2]
    70|
    71|   **Open Questions**
    72|   - [Unresolved question 1]
    73|   - [Unresolved question 2]
    74|   ```
    75|
    76|5. **Use Accessible Language**: Write for a primary school graduate. Use simple terms. Avoid jargon or explain it briefly.
    77|
    78|6. **Prioritize Clarity**: Focus on:
    79|   - What decisions affect the roadmap or strategy?
    80|   - What does each person need to do?
    81|   - By when do they need to do it?
    82|
    83|7. **Save the Output**: Save as a markdown document: `Meeting-Summary-[date]-[topic].md`
    84|
    85|## Notes
    86|
    87|- Be objective—summarize what was discussed, not personal opinions
    88|- Highlight action items clearly so nothing falls through the cracks
    89|- If the meeting was large or complex, consider breaking points into sections by topic
    90|- Use "we" language to keep the team feel inclusive and collaborative
    91|