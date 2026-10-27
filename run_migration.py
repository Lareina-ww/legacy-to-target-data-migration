from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from data_migration.pipeline import run_migration  # noqa: E402


if __name__ == "__main__":
    summary = run_migration(PROJECT_ROOT)
    print("Migration completed successfully.")
    print(f"Customers migrated: {summary['customers']['migrated_rows']}")
    print(f"Transactions migrated: {summary['transactions']['migrated_rows']}")
    print(f"Target transaction total: EUR {summary['transactions']['target_total_eur']:.2f}")
    print(f"Exceptions recorded: {summary['exceptions']['total']}")
    print(f"Reports written to: {PROJECT_ROOT / 'outputs'}")

