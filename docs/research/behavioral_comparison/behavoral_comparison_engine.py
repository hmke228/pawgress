from contextlib import closing
import sqlite3
from datetime import datetime
from pathlib import Path
from pprint import pprint
from uuid import uuid4

DB_NAME = Path(__file__).with_name("pawgress.db")

OBSERVATION_PATTERNS = {
                        "approaching another dog": [
                            "approached",
                            "approaching",
                            "approach"
                        ],

                        "barking": [
                            "barked",
                            "barking",
                            "bark"
                        ],

                        "jumping": [
                            "jumped",
                            "jumping",
                            "jump"
                        ],

                        "tail wagging": [
                            "tail wagging",
                            "wagging tail"
                        ],

                        "growling": [
                            "growling",
                            "growl"
                        ],

                        "relaxed posture": [
                            "relaxed",
                            "calm",
                            "calmly"
                        ],

                        "social interaction": [
                            "social",
                            "greeted",
                            "greeting",
                            "interacted"
                        ]
                    }


def initialize_database():
    """
    Initializes the database by creating the 'reports' table if it doesn't exist.
    """
    with closing(sqlite3.connect(DB_NAME)) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                report_id TEXT PRIMARY KEY,
                dog_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                scene_context TEXT,
                observations TEXT
            )
            """
        )
        connection.commit()


def save_report(report_id, dog_name, created_at, scene_context, observations):
    """
    Saves a report to the database.
    """
    with closing(sqlite3.connect(DB_NAME)) as connection:
        connection.execute(
            """
            INSERT INTO reports (
                report_id,
                dog_name,
                created_at,
                scene_context,
                observations
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (report_id, dog_name, created_at, scene_context, observations),
        )
        connection.commit()


def get_previous_reports(dog_name, current_report_id, limit=3):
    """
    Retrieves the previous reports for a given dog, excluding the current report.
    Returns a list of dictionaries containing the report details.
    """
    with closing(sqlite3.connect(DB_NAME)) as connection:
        rows = connection.execute(
            """
            SELECT report_id, created_at, scene_context, observations
            FROM reports
            WHERE dog_name = ? AND report_id != ?
            ORDER BY created_at DESC, report_id DESC
            LIMIT ?
            """,
            (dog_name, current_report_id, limit),
        ).fetchall()

    return [
        {
            "report_id": row[0],
            "created_at": row[1],
            "scene_context": row[2],
            "behavioral_observations": {"current": row[3]},
        }
        for row in rows
    ]


def is_negated(text, pattern):
    """
    Analyzes the text to determine if the given pattern is negated.
    Returns True if the pattern is negated, False otherwise.
    """

    text = text.lower()

    if f"{pattern} was not observed" in text:
        return True

    if f"{pattern} were not observed" in text:
        return True

    if f"no {pattern}" in text:
        return True

    if f"without {pattern}" in text:
        return True

    return False


def extract_observations(text):
    """
    Converts observation text into comparison themes.
    Returns a list of themes that are observed in the text.
    """
    text = text.lower()
    found = []

    for theme, patterns in OBSERVATION_PATTERNS.items():
        for pattern in patterns:

            if pattern in text:

                if is_negated(text, pattern):
                    continue

                found.append(theme)
                break

    return found


def compare_reports(current_observations, previous_reports):
    """
    Compares current observations against up to three
    previous reports and summarizes consistency and change.
    """

    if not previous_reports:
        return {
            "comparison_summary":
                "No previous reports were available for comparison. "
                "This report establishes a behavioral baseline.",
            "referenced_report_ids": []
        }

    current_themes = set(extract_observations(current_observations))

    historical_themes = set()
    referenced_ids = []

    for report in previous_reports:
        referenced_ids.append(report["report_id"])

        previous_text = (
            report["behavioral_observations"]["current"]
        )

        historical_themes.update(
            extract_observations(previous_text)
        )

    consistent = current_themes & historical_themes
    new = current_themes - historical_themes
    no_longer_observed = historical_themes - current_themes

    summary_parts = []

    if consistent:
        summary_parts.append(
            "Consistent observations include "
            + ", ".join(sorted(consistent))
            + "."
        )

    if new:
        summary_parts.append(
            "Newly observed behaviors include "
            + ", ".join(sorted(new))
            + "."
        )

    if no_longer_observed:
        summary_parts.append(
            "Previously observed behaviors not mentioned in the current report include "
            + ", ".join(sorted(no_longer_observed))
            + "."
        )

    if not summary_parts:
        summary_parts.append(
            "No meaningful similarities or differences were identified."
        )

    return {
        "comparison_summary": " ".join(summary_parts),
        "referenced_report_ids": referenced_ids
    }


def process_report(dog_name, scene_context, observations):
    """
    Processes a single report for a dog, including saving it to the database
    and comparing it with previous reports.
    """
    report_id = str(uuid4())
    created_at = datetime.now().isoformat()

    previous_reports = get_previous_reports(dog_name, report_id)
    comparison = compare_reports(observations, previous_reports)

    save_report(
        report_id,
        dog_name,
        created_at,
        scene_context,
        observations,
    )

    return {
        "report_id": report_id,
        **comparison,
    }


def prompt_required(prompt):
    while True:
        answer = input(prompt).strip()
        if answer:
            return answer
        print("Please enter a value.")


if __name__ == "__main__":
    initialize_database()

    dog_name = prompt_required("Dog's name: ")
    scene_context = prompt_required("Scene/context: ")
    observations = prompt_required("What behaviors did you observe? ")

    result = process_report(
        dog_name=dog_name,
        scene_context=scene_context,
        observations=observations,
    )

    print("\nReport saved. Comparison:")
    pprint(result)