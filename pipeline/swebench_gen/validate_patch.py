import subprocess
import sys
from pathlib import Path

def validate_patch(patch_file: str) -> bool:
    """
    Validate whether a given patch file is a valid git patch.

    Args:
        patch_file (str): Path to the patch file.

    Returns:
        bool: True if valid, False if invalid.
    """
    patch_path = Path(patch_file)
    if not patch_path.exists():
        print(f"❌ Patch file not found: {patch_file}")
        return False

    try:
        result = subprocess.run(
            ["git", "apply", "--check", "-v", str(patch_path)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ Valid patch: {patch_file}")
            return True
        else:
            print(f"❌ Invalid patch: {patch_file}")
            print("Reason:", result.stderr.strip())
            return False
    except Exception as e:
        print(f"⚠️ Error while validating patch {patch_file}: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate_patch.py <patch_file>")
        sys.exit(1)

    patch_file = sys.argv[1]
    validate_patch(patch_file)
