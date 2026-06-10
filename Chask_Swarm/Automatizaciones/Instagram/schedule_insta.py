import os
import subprocess

def schedule_tasks():
    times = ["08:00", "14:00", "22:00"]
    script_path = r"C:\Users\fnora\Desktop\do_instagram_api.py"
    
    # Check python executable path
    python_exe = "python.exe"
    
    # We will pass the Instagram image folder to the script so it can pick randomly later?
    # Wait, the user wanted dynamic images or I can generate them on the fly?
    # Actually, the user hasn't approved the plan yet, they were interrupted by the login issue.
    # So I shouldn't execute the scheduling yet until they approve the plan.
    pass

if __name__ == "__main__":
    schedule_tasks()
