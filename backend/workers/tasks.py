"""
Huey tasks for automation jobs.
Contains the main automation workflow executed by background workers.
"""

import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from core.queue import huey
from core.session_manager import GenerationsSession
from automation import selenium_helpers, data_processing
from automation.report_automation import (
    login_and_open_report_writer,
    find_client_notes_report,
    export_single_report
)
from automation.client_search import process_client_with_personal_data
from automation.mapping_excel import generate_excel_from_json
from db import crud
from core.config import settings
import os
import traceback


@huey.task()
def run_automation_job(job_id, credentials, date_range):
    """
    Main automation task executed by Huey worker.
    Handles complete workflow from login to Excel generation with session keep-alive.

    Args:
        job_id: Unique job identifier
        credentials: Dict with agency_id, email, password
        date_range: Dict with start and end dates (MM/DD/YYYY format)
    """
    crud.update_job_status(job_id, 'processing')
    crud.append_log(job_id, "Starting automation job...")

    session_dir = Path(settings.sessions_dir) / job_id
    downloads_dir = session_dir / "downloads"
    output_dir = session_dir / "output"

    downloads_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    driver = None
    session = None

    try:
        # Step 1: Initialize browser
        crud.append_log(job_id, "Initializing Chrome browser...")
        driver = selenium_helpers.build_driver(
            download_dir=str(downloads_dir),
            session_id=job_id,
            headless=True
        )
        crud.append_log(job_id, "Browser initialized successfully")

        # Step 2: Login to Generations
        crud.append_log(job_id, "Logging in to Generations system...")
        login_and_open_report_writer(
            driver,
            credentials['agency_id'],
            credentials['email'],
            credentials['password']
        )
        crud.append_log(job_id, "Login successful - Report Writer opened")

        # Step 3: Initialize session manager for keep-alive
        session = GenerationsSession(driver, credentials, job_id)
        crud.append_log(job_id, "Session manager initialized with idle timeout prevention")

        # Step 4: Find Client Notes report
        crud.append_log(job_id, "Locating Client Notes report...")
        option_value, option_text = find_client_notes_report(driver)
        crud.append_log(job_id, f"Found report: {option_text}")

        # Step 5: Export report
        crud.append_log(job_id, f"Exporting report for date range: {date_range['start']} to {date_range['end']}")
        session.keep_alive()  # Keep session alive before long operation

        json_file_path = export_single_report(
            driver=driver,
            download_dir=downloads_dir,  # Already a Path object
            option_value=option_value,
            option_text=option_text,
            start_str=date_range['start'],  # Correct parameter name
            end_str=date_range['end']  # Correct parameter name
        )

        if not json_file_path or not Path(json_file_path).exists():
            raise Exception("Report export failed - JSON file not created")

        crud.append_log(job_id, f"Report exported successfully: {Path(json_file_path).name}")
        session.update_activity()

        # Step 6: Get clients from JSON
        crud.append_log(job_id, "Extracting client list from report...")
        clients = data_processing.get_clients_from_json_file(json_file_path)
        total_clients = len(clients)
        crud.update_job_clients(job_id, total_clients, 0, 0)
        crud.append_log(job_id, f"Found {total_clients} unique clients to process")

        # Step 7: Process each client (limit from user config)
        processed = 0
        failed = 0
        client_limit = date_range.get('client_limit', 10)
        max_clients = min(total_clients, client_limit)

        if client_limit >= 999:
            crud.append_log(job_id, f"Processing ALL {total_clients} clients...")
        else:
            crud.append_log(job_id, f"Processing first {max_clients} of {total_clients} clients...")

        for idx, client in enumerate(clients[:max_clients], 1):
            try:
                # Keep session alive before each client
                session.keep_alive()
                session.update_activity()

                client_name = client.get('full_name', 'Unknown')
                crud.append_log(job_id, f"[{idx}/{max_clients}] Processing: {client_name}")

                # Search for client and extract personal data
                personal_data = process_client_with_personal_data(
                    driver=driver,
                    client_name=client['full_name'],
                    last_name=client['last_name'],
                    first_name=client['first_name'],
                    original_last_name=client.get('original_last_name')
                )

                # Update JSON with personal data
                data_processing.update_json_with_personal_data(
                    json_file_path,
                    client_name,
                    personal_data
                )

                processed += 1
                crud.update_job_clients(job_id, total_clients, processed, failed)
                crud.append_log(job_id, f"[{idx}/{max_clients}] Successfully processed: {client_name}")
                session.update_activity()

            except Exception as e:
                failed += 1
                crud.update_job_clients(job_id, total_clients, processed, failed)
                error_msg = str(e)[:200]  # Truncate long errors
                crud.append_log(job_id, f"[{idx}/{max_clients}] Failed to process {client_name}: {error_msg}")
                # Continue with next client instead of failing entire job

        # Step 8: Generate Excel from JSON
        session.keep_alive()
        crud.append_log(job_id, "Generating final Excel file with KP template...")

        excel_file_path = generate_excel_from_json(
            json_file_path,
            str(output_dir)
        )

        if not excel_file_path or not Path(excel_file_path).exists():
            raise Exception("Excel generation failed - file not created")

        crud.append_log(job_id, f"Excel file generated: {Path(excel_file_path).name}")

        # Step 9: Complete job
        crud.complete_job(job_id, str(json_file_path), str(excel_file_path))
        crud.append_log(job_id, f"Job completed successfully! Processed {processed}/{total_clients} clients ({failed} failed)")

    except Exception as e:
        error_message = str(e)
        crud.fail_job(job_id, error_message)
        crud.append_log(job_id, f"Job failed with error: {error_message}")

        # Log full traceback for debugging
        tb = traceback.format_exc()
        crud.append_log(job_id, f"Traceback:\n{tb}")

    finally:
        # Cleanup: close browser
        if driver:
            try:
                crud.append_log(job_id, "Closing browser...")
                driver.quit()
                crud.append_log(job_id, "Browser closed successfully")
            except Exception as e:
                crud.append_log(job_id, f"Error closing browser: {str(e)}")
