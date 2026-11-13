"""Collect owner-provided input for the Epic 2 workflow."""

from pathlib import Path


def prompt_required_text(prompt: str) -> str:
    """Prompt until the user provides non-empty text input."""
    while True:
        user_input = input(prompt).strip()
        if user_input:
            return user_input
        print("Please enter a non-empty value. This field is required.")


def prompt_optional_text(prompt: str) -> str | None:
    """Return trimmed text or None if the user leaves it blank."""
    user_input = input(prompt).strip()
    return user_input if user_input else None


def collect_situation(*, has_previous_reports: bool) -> str | None:
    """Require situational context for a first analysis; allow omission on later runs."""
    if has_previous_reports:
        return prompt_optional_text(
            "Situation Description (optional - press Enter to skip): "
        )
    return prompt_required_text("Describe the situation: ")


def collect_image_paths(*, minimum_count: int) -> list[str]:
    """Collect ordered, readable file paths without checking image contents."""
    if minimum_count < 1:
        raise ValueError("At least one image is required.")

    image_paths: list[str] = []

    while True:
        entered_path = input("Image Path (or 'done' to finish): ").strip()

        if entered_path.lower() == "done":
            if len(image_paths) >= minimum_count:
                return image_paths
            print(f"Please provide at least {minimum_count} image file(s).")
            continue

        if not entered_path:
            print("Please enter a file path.")
            continue

        try:
            path = Path(entered_path).expanduser()

            if not path.is_file():
                print("The provided path does not point to a file.")
                continue

            with path.open("rb") as image_file:
                image_file.read(1)

            resolved_path = str(path.resolve())
        except (OSError, ValueError, RuntimeError):
            print(
                "The provided file could not be read. Please check the path and permissions."
            )
            continue

        if resolved_path in image_paths:
            print("The provided file has already been added.")
            continue

        image_paths.append(resolved_path)
