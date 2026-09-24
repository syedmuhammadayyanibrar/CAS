import subprocess
import sys
import os

def run_step(command: str, description: str):
    print(f"==> {description}...")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"Error: Step '{description}' failed with exit code {result.returncode}")
        sys.exit(result.returncode)

def main():
    print("========================================")
    print("CAS Frontend & Asset Build for Vercel")
    print("========================================")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(base_dir, "frontend")

    if not os.path.exists(frontend_dir):
        print("Frontend directory not found, skipping frontend build.")
        return

    # Install frontend dependencies
    run_step("npm --prefix frontend install", "Installing frontend dependencies")

    # Build Vite production assets
    run_step("npm --prefix frontend run build", "Compiling frontend SPA bundle")

    dist_index = os.path.join(frontend_dir, "dist", "index.html")
    if os.path.exists(dist_index):
        print(f"SUCCESS: Frontend bundle ready at {dist_index}")
    else:
        print(f"WARNING: Expected frontend build at {dist_index} was not found.")

    print("========================================")
    print("Build script finished successfully.")
    print("========================================")

if __name__ == "__main__":
    main()
