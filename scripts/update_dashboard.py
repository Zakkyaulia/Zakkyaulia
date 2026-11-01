"""
update_dashboard.py - Main entry point for the GitHub Profile Dashboard automation pipeline.
Executes data fetching, statistics processing, and SVG rendering sequentially.
"""

import sys
import time
from pathlib import Path

# Add scripts directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

from fetch_github_data import fetch_all_data
from process_statistics import process_stats
from generate_dashboard import generate_svg


def run_pipeline():
    start_time = time.time()
    print("=" * 60)
    print("  GITHUB PROFILE DASHBOARD REGENERATION PIPELINE")
    print("=" * 60)

    try:
        # Step 1: Fetch raw data from GitHub APIs
        print("\n[1/3] Fetching data from GitHub REST & GraphQL APIs...")
        raw_data = fetch_all_data()

        # Step 2: Calculate metrics, heatmaps, and language activity
        print("\n[2/3] Processing metrics and statistical models...")
        stats = process_stats(raw_data)

        # Step 3: Generate pixel-perfect SVG dashboard
        print("\n[3/3] Generating SVG dashboard asset...")
        svg_file = generate_svg(stats)

        elapsed = time.time() - start_time
        print("\n" + "=" * 60)
        print(f" Dashboard successfully regenerated in {elapsed:.2f}s!")
        print(f" Asset: {svg_file}")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"\n Pipeline failed with error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)
