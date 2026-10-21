# CLI

## Goal

What is this component responsible for?

- Collect user input, validate it, and pass it to the shared pipeline
- Receive and display generated reports and comparisons
- Provide user with menu options for app navigation

## Research & Design Ideas

Record findings, possible approaches, and design considerations.

- Allow user to preview and edit submissions before analysis ocurrs
- Allow user to navigate app freely (interactive menus, command arguments)
- Interactive prompts guide user through app use (clear instructions, error messaging, troubleshooting)
- Allow user to view/update established dog profiles
- Allow user to upload multiple images and specify the intended order
- Display a status indicator (e.g. 'AI Analysis in Progress,' 'Generating Report')
- Format report output with distinct sections
- Simplify error recovery (e.g. prompt for replacement of invalid image paths without requiring re-entry of background context)
- Preserve user's input to allow for easy resubmission in the event of backend failure


## Proposed Schema / Structure

Outline proposed data structures, interfaces, or workflows.

- `cli.py` handles terminal interaction, input validation, and output display.
- `__main__.py` serves as the application entry point.
- `cli.py` sends and receives information from the backend.
- Potential Menu Options:

    1. Create or view/edit dog profile
    2. Submit images/scenarios for analysis
    3. View previous reports
    4. Exit


## Open Questions

List questions that need team discussion.

- Plan for shared main program - How will CLI call the backend? (e.g. function input/output parameters)
- What are the required and optional fields for user input (e.g. dog profile creation, image upload)
- What is the criteria for image acceptance? (i.e. What will the AI component support?)
- What is the AI report structure?
- How should backend errors be conveyed by the CLI?

## References

Add useful documentation or resources.
