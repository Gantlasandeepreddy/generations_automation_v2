#!/usr/bin/env python3
"""
Script to migrate data from JSON files to SQLite database.

This script migrates:
1. audit_trail.json → runs and logs tables
2. schedule_config.json → schedule table

Usage:
    python migrate_json_to_db.py

The script will backup the JSON files after successful migration.
"""

import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

import json
from datetime import datetime
from db.database import SessionLocal, init_db
from db import models
from core.config import settings


def migrate_audit_trail(db):
    """Migrate audit_trail.json to runs and logs tables"""

    audit_file = Path(settings.audit_file)

    if not audit_file.exists():
        print(f"⚠️  No audit trail file found at {audit_file}")
        return 0, 0

    print(f"\nReading {audit_file}...")
    with open(audit_file, 'r', encoding='utf-8') as f:
        audit_data = json.load(f)

    if not audit_data:
        print("  No runs to migrate")
        return 0, 0

    print(f"  Found {len(audit_data)} runs to migrate")

    runs_count = 0
    logs_count = 0

    for entry in audit_data:
        try:
            # Create Run record
            run = models.Run(
                run_id=entry['run_id'],
                user_id=None,  # Legacy runs have no user
                type=entry['type'],
                status=entry['status'],
                start_time=datetime.fromisoformat(entry['start_time']) if entry.get('start_time') else datetime.utcnow(),
                end_time=datetime.fromisoformat(entry['end_time']) if entry.get('end_time') else None,
                start_date=entry['date_range'].get('start_date', ''),
                end_date=entry['date_range'].get('end_date', ''),
                max_clients=entry.get('max_clients', 10),
                clients_processed=entry.get('clients_processed', 0),
                file_path=entry.get('file_path'),
                file_size=entry.get('file_size'),
                error=entry.get('error')
            )

            db.add(run)
            db.flush()  # Get run.id for logs
            runs_count += 1

            # Create Log records
            for log_message in entry.get('logs', []):
                # Extract timestamp from log message if it has the format "[YYYY-MM-DD HH:MM:SS] message"
                timestamp = datetime.utcnow()
                message = log_message

                if log_message.startswith('[') and ']' in log_message:
                    try:
                        timestamp_str = log_message[1:log_message.index(']')]
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        message = log_message[log_message.index(']') + 1:].strip()
                    except:
                        pass  # Use default timestamp if parsing fails

                log = models.Log(
                    run_id=run.id,
                    timestamp=timestamp,
                    message=message
                )
                db.add(log)
                logs_count += 1

        except Exception as e:
            print(f"  ⚠️  Error migrating run {entry.get('run_id', 'unknown')}: {e}")
            continue

    db.commit()
    print(f"  ✓ Migrated {runs_count} runs and {logs_count} logs")

    return runs_count, logs_count


def migrate_schedule_config(db):
    """Migrate schedule_config.json to schedule table"""

    schedule_file = Path(settings.schedule_config_file)

    if not schedule_file.exists():
        print(f"\n⚠️  No schedule config file found at {schedule_file}")
        print("  Creating default schedule...")
        schedule = models.Schedule(
            id=1,
            weekly_enabled=False,
            weekly_day=1,
            weekly_hour=9,
            weekly_minute=0,
            monthly_enabled=False,
            monthly_day=1,
            monthly_hour=9,
            monthly_minute=0
        )
        db.add(schedule)
        db.commit()
        return True

    print(f"\nReading {schedule_file}...")
    with open(schedule_file, 'r', encoding='utf-8') as f:
        schedule_data = json.load(f)

    print("  Migrating schedule configuration...")

    schedule = models.Schedule(
        id=1,  # Single row table
        weekly_enabled=schedule_data.get('weekly_enabled', False),
        weekly_day=schedule_data.get('weekly_day', 1),
        weekly_hour=schedule_data.get('weekly_hour', 9),
        weekly_minute=schedule_data.get('weekly_minute', 0),
        monthly_enabled=schedule_data.get('monthly_enabled', False),
        monthly_day=schedule_data.get('monthly_day', 1),
        monthly_hour=schedule_data.get('monthly_hour', 9),
        monthly_minute=schedule_data.get('monthly_minute', 0)
    )

    db.add(schedule)
    db.commit()

    print("  ✓ Schedule configuration migrated")
    return True


def backup_json_files():
    """Create backups of JSON files"""

    print("\nBacking up JSON files...")

    audit_file = Path(settings.audit_file)
    schedule_file = Path(settings.schedule_config_file)

    files_backed_up = 0

    if audit_file.exists():
        backup_path = audit_file.with_suffix('.json.backup')
        audit_file.rename(backup_path)
        print(f"  ✓ Backed up {audit_file.name} → {backup_path.name}")
        files_backed_up += 1

    if schedule_file.exists():
        backup_path = schedule_file.with_suffix('.json.backup')
        schedule_file.rename(backup_path)
        print(f"  ✓ Backed up {schedule_file.name} → {backup_path.name}")
        files_backed_up += 1

    return files_backed_up


def main():
    """Main migration function"""

    print("=" * 70)
    print(" JSON to Database Migration")
    print("=" * 70)

    # Initialize database
    print("\nInitializing database...")
    init_db()
    print("✓ Database initialized")

    db = SessionLocal()

    try:
        # Check if migration already done
        existing_runs = db.query(models.Run).count()
        if existing_runs > 0:
            print(f"\n⚠️  Warning: Database already contains {existing_runs} runs")
            confirm = input("Continue migration anyway? This may create duplicates (y/N): ").strip().lower()
            if confirm != 'y':
                print("Migration cancelled")
                return

        # Migrate audit trail
        runs_count, logs_count = migrate_audit_trail(db)

        # Migrate schedule
        migrate_schedule_config(db)

        # Backup JSON files
        backed_up = backup_json_files()

        # Summary
        print("\n" + "=" * 70)
        print(" Migration Complete!")
        print("=" * 70)
        print(f"  Runs migrated: {runs_count}")
        print(f"  Logs migrated: {logs_count}")
        print(f"  Files backed up: {backed_up}")
        print("=" * 70)
        print("\nYou can now start the application with the new database.")
        print("JSON backups have been created with .backup extension.")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user")
        sys.exit(0)
