#!/usr/bin/env python3
"""
PRISM Development Progress Tracker
Interactive script to track and update development progress
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Color codes for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

# Priority and status icons
PRIORITY_ICONS = {
    "critical": "🔴",
    "high": "🟡",
    "medium": "🟢",
    "low": "⚪"
}

STATUS_ICONS = {
    "not_started": "⏳",
    "in_progress": "🚧",
    "completed": "✅",
    "blocked": "🚫",
    "on_hold": "⏸️"
}

PHASE_PROGRESS = {
    "phase1": {"total": 10, "completed": 0},
    "phase2": {"total": 8, "completed": 0},
    "phase3": {"total": 9, "completed": 0},
    "phase4": {"total": 8, "completed": 0}
}

class ProgressTracker:
    def __init__(self):
        self.data_file = Path("data/progress_tracking.json")
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data = self.load_data()
    
    def load_data(self) -> Dict:
        """Load progress data from JSON file"""
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return self.initialize_data()
    
    def initialize_data(self) -> Dict:
        """Initialize progress tracking data structure"""
        return {
            "project": {
                "name": "PRISM - Personal Agent Ecosystem",
                "start_date": datetime.now().isoformat(),
                "current_phase": "phase1",
                "overall_progress": 0
            },
            "phases": {
                "phase1": {
                    "name": "Foundation & Core Agents",
                    "status": "in_progress",
                    "progress": 0,
                    "total_tasks": 10,
                    "completed_tasks": 0,
                    "started": None,
                    "completed": None
                },
                "phase2": {
                    "name": "Learning & Personalization",
                    "status": "not_started",
                    "progress": 0,
                    "total_tasks": 8,
                    "completed_tasks": 0,
                    "started": None,
                    "completed": None
                },
                "phase3": {
                    "name": "Advanced Personal Capabilities",
                    "status": "not_started",
                    "progress": 0,
                    "total_tasks": 9,
                    "completed_tasks": 0,
                    "started": None,
                    "completed": None
                },
                "phase4": {
                    "name": "Polish & Advanced Integration",
                    "status": "not_started",
                    "progress": 0,
                    "total_tasks": 8,
                    "completed_tasks": 0,
                    "started": None,
                    "completed": None
                }
            },
            "tasks": {},
            "daily_logs": [],
            "metrics": {
                "total_time_spent": 0,
                "tasks_completed": 0,
                "bugs_fixed": 0,
                "features_added": 0
            }
        }
    
    def save_data(self):
        """Save progress data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def print_header(self):
        """Print colorful header"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}   PRISM DEVELOPMENT PROGRESS TRACKER{Colors.END}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.END}\n")
    
    def print_overall_status(self):
        """Display overall project status"""
        project = self.data["project"]
        current_phase = self.data["phases"][project["current_phase"]]
        
        print(f"{Colors.BOLD}Project Status:{Colors.END}")
        print(f"  Current Phase: {Colors.YELLOW}{current_phase['name']}{Colors.END}")
        print(f"  Overall Progress: {self.get_progress_bar(project['overall_progress'])} {project['overall_progress']}%")
        print()
    
    def print_phase_summary(self):
        """Display summary of all phases"""
        print(f"{Colors.BOLD}Phase Summary:{Colors.END}\n")
        
        for phase_id, phase in self.data["phases"].items():
            status_icon = STATUS_ICONS.get(phase["status"], "⏳")
            progress_bar = self.get_progress_bar(phase["progress"], width=20)
            
            print(f"  {status_icon} {Colors.BOLD}{phase['name']}{Colors.END}")
            print(f"     {progress_bar} {phase['progress']}% ({phase['completed_tasks']}/{phase['total_tasks']} tasks)")
        
        print()
    
    def print_active_tasks(self):
        """Display currently active tasks"""
        active_tasks = {tid: task for tid, task in self.data.get("tasks", {}).items() 
                       if task.get("status") == "in_progress"}
        
        if active_tasks:
            print(f"{Colors.BOLD}Active Tasks:{Colors.END}\n")
            for task_id, task in active_tasks.items():
                priority_icon = PRIORITY_ICONS.get(task.get("priority", "medium").lower(), "🟢")
                print(f"  {priority_icon} {Colors.CYAN}{task['name']}{Colors.END}")
                print(f"     Phase: {task.get('phase', 'N/A')} | Estimated: {task.get('estimated_time', 'N/A')}")
            print()
        else:
            print(f"{Colors.YELLOW}No active tasks. Start a new task to begin!{Colors.END}\n")
    
    def print_recent_activity(self, limit: int = 5):
        """Display recent activity log"""
        logs = self.data.get("daily_logs", [])
        if logs:
            print(f"{Colors.BOLD}Recent Activity:{Colors.END}\n")
            for log in logs[-limit:]:
                timestamp = datetime.fromisoformat(log["timestamp"]).strftime("%Y-%m-%d %H:%M")
                print(f"  {Colors.GREEN}[{timestamp}]{Colors.END} {log['message']}")
            print()
    
    def get_progress_bar(self, percentage: float, width: int = 30) -> str:
        """Generate a visual progress bar"""
        filled = int(width * percentage / 100)
        empty = width - filled
        
        bar = "█" * filled + "░" * empty
        
        if percentage < 30:
            color = Colors.RED
        elif percentage < 70:
            color = Colors.YELLOW
        else:
            color = Colors.GREEN
        
        return f"{color}{bar}{Colors.END}"
    
    def add_task(self, task_data: Dict):
        """Add a new task to tracking"""
        task_id = task_data.get("id", f"task_{len(self.data['tasks']) + 1}")
        self.data["tasks"][task_id] = {
            **task_data,
            "created": datetime.now().isoformat(),
            "status": task_data.get("status", "not_started")
        }
        self.log_activity(f"Added task: {task_data['name']}")
        self.save_data()
    
    def update_task_status(self, task_id: str, new_status: str):
        """Update task status"""
        if task_id in self.data["tasks"]:
            old_status = self.data["tasks"][task_id]["status"]
            self.data["tasks"][task_id]["status"] = new_status
            self.data["tasks"][task_id]["updated"] = datetime.now().isoformat()
            
            # Update metrics
            if new_status == "completed" and old_status != "completed":
                self.data["metrics"]["tasks_completed"] += 1
                phase_id = self.data["tasks"][task_id].get("phase")
                if phase_id and phase_id in self.data["phases"]:
                    self.data["phases"][phase_id]["completed_tasks"] += 1
                    self.update_phase_progress(phase_id)
            
            self.log_activity(f"Updated task '{self.data['tasks'][task_id]['name']}' status: {old_status} → {new_status}")
            self.calculate_overall_progress()
            self.save_data()
            return True
        return False
    
    def update_phase_progress(self, phase_id: str):
        """Recalculate phase progress"""
        phase = self.data["phases"].get(phase_id)
        if phase:
            completed = phase["completed_tasks"]
            total = phase["total_tasks"]
            phase["progress"] = int((completed / total) * 100) if total > 0 else 0
    
    def calculate_overall_progress(self):
        """Calculate overall project progress"""
        total_tasks = sum(phase["total_tasks"] for phase in self.data["phases"].values())
        completed_tasks = sum(phase["completed_tasks"] for phase in self.data["phases"].values())
        
        if total_tasks > 0:
            self.data["project"]["overall_progress"] = int((completed_tasks / total_tasks) * 100)
    
    def log_activity(self, message: str):
        """Log an activity"""
        self.data["daily_logs"].append({
            "timestamp": datetime.now().isoformat(),
            "message": message
        })
        
        # Keep only last 100 logs
        if len(self.data["daily_logs"]) > 100:
            self.data["daily_logs"] = self.data["daily_logs"][-100:]
    
    def interactive_menu(self):
        """Show interactive menu"""
        while True:
            self.print_header()
            self.print_overall_status()
            self.print_phase_summary()
            self.print_active_tasks()
            
            print(f"{Colors.BOLD}Actions:{Colors.END}")
            print("  1. Start a task")
            print("  2. Complete a task")
            print("  3. View all tasks")
            print("  4. Add new task")
            print("  5. Log work session")
            print("  6. View detailed phase info")
            print("  7. Export progress report")
            print("  8. View metrics")
            print("  0. Exit")
            print()
            
            choice = input(f"{Colors.CYAN}Select an option: {Colors.END}").strip()
            
            if choice == "1":
                self.start_task()
            elif choice == "2":
                self.complete_task()
            elif choice == "3":
                self.view_all_tasks()
            elif choice == "4":
                self.add_new_task()
            elif choice == "5":
                self.log_work_session()
            elif choice == "6":
                self.view_phase_details()
            elif choice == "7":
                self.export_report()
            elif choice == "8":
                self.view_metrics()
            elif choice == "0":
                print(f"\n{Colors.GREEN}Progress saved. Keep building! 🚀{Colors.END}\n")
                break
            else:
                print(f"{Colors.RED}Invalid option. Try again.{Colors.END}")
            
            input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.END}")
    
    def start_task(self):
        """Mark a task as in progress"""
        print(f"\n{Colors.BOLD}Available Tasks:{Colors.END}")
        
        not_started = {tid: task for tid, task in self.data.get("tasks", {}).items() 
                      if task.get("status") == "not_started"}
        
        if not not_started:
            print(f"{Colors.YELLOW}No tasks available to start. Add a new task first!{Colors.END}")
            return
        
        for i, (task_id, task) in enumerate(not_started.items(), 1):
            print(f"  {i}. {task['name']} ({task.get('phase', 'N/A')})")
        
        try:
            choice = int(input(f"\n{Colors.CYAN}Select task number: {Colors.END}").strip())
            task_id = list(not_started.keys())[choice - 1]
            self.update_task_status(task_id, "in_progress")
            print(f"{Colors.GREEN}✅ Task started!{Colors.END}")
        except (ValueError, IndexError):
            print(f"{Colors.RED}Invalid selection.{Colors.END}")
    
    def complete_task(self):
        """Mark a task as completed"""
        print(f"\n{Colors.BOLD}In Progress Tasks:{Colors.END}")
        
        in_progress = {tid: task for tid, task in self.data.get("tasks", {}).items() 
                      if task.get("status") == "in_progress"}
        
        if not in_progress:
            print(f"{Colors.YELLOW}No tasks in progress.{Colors.END}")
            return
        
        for i, (task_id, task) in enumerate(in_progress.items(), 1):
            print(f"  {i}. {task['name']}")
        
        try:
            choice = int(input(f"\n{Colors.CYAN}Select task number to complete: {Colors.END}").strip())
            task_id = list(in_progress.keys())[choice - 1]
            self.update_task_status(task_id, "completed")
            print(f"{Colors.GREEN}🎉 Task completed! Great work!{Colors.END}")
        except (ValueError, IndexError):
            print(f"{Colors.RED}Invalid selection.{Colors.END}")
    
    def view_all_tasks(self):
        """Display all tasks grouped by phase"""
        print(f"\n{Colors.BOLD}All Tasks by Phase:{Colors.END}\n")
        
        for phase_id, phase in self.data["phases"].items():
            print(f"{Colors.BOLD}{phase['name']}:{Colors.END}")
            
            phase_tasks = {tid: task for tid, task in self.data.get("tasks", {}).items() 
                          if task.get("phase") == phase_id}
            
            if phase_tasks:
                for task_id, task in phase_tasks.items():
                    status_icon = STATUS_ICONS.get(task["status"], "⏳")
                    priority_icon = PRIORITY_ICONS.get(task.get("priority", "medium").lower(), "🟢")
                    print(f"  {status_icon} {priority_icon} {task['name']}")
            else:
                print(f"  {Colors.YELLOW}No tasks defined yet{Colors.END}")
            print()
    
    def add_new_task(self):
        """Add a new task interactively"""
        print(f"\n{Colors.BOLD}Add New Task:{Colors.END}")
        
        name = input(f"{Colors.CYAN}Task name: {Colors.END}").strip()
        if not name:
            print(f"{Colors.RED}Task name cannot be empty.{Colors.END}")
            return
        
        print("\nPhases:")
        for i, (phase_id, phase) in enumerate(self.data["phases"].items(), 1):
            print(f"  {i}. {phase['name']}")
        
        try:
            phase_choice = int(input(f"{Colors.CYAN}Select phase: {Colors.END}").strip())
            phase_id = list(self.data["phases"].keys())[phase_choice - 1]
        except (ValueError, IndexError):
            print(f"{Colors.RED}Invalid phase selection.{Colors.END}")
            return
        
        priority = input(f"{Colors.CYAN}Priority (critical/high/medium/low): {Colors.END}").strip().lower()
        if priority not in ["critical", "high", "medium", "low"]:
            priority = "medium"
        
        estimated_time = input(f"{Colors.CYAN}Estimated time (e.g., '2-3 days'): {Colors.END}").strip()
        
        task_data = {
            "id": f"task_{len(self.data['tasks']) + 1}",
            "name": name,
            "phase": phase_id,
            "priority": priority,
            "estimated_time": estimated_time,
            "status": "not_started"
        }
        
        self.add_task(task_data)
        self.data["phases"][phase_id]["total_tasks"] += 1
        print(f"{Colors.GREEN}✅ Task added successfully!{Colors.END}")
    
    def log_work_session(self):
        """Log a work session"""
        print(f"\n{Colors.BOLD}Log Work Session:{Colors.END}")
        
        hours = input(f"{Colors.CYAN}Hours worked: {Colors.END}").strip()
        notes = input(f"{Colors.CYAN}What did you accomplish?: {Colors.END}").strip()
        
        try:
            hours_float = float(hours)
            self.data["metrics"]["total_time_spent"] += hours_float
            self.log_activity(f"Work session: {hours} hours - {notes}")
            print(f"{Colors.GREEN}✅ Work session logged!{Colors.END}")
        except ValueError:
            print(f"{Colors.RED}Invalid hours format.{Colors.END}")
    
    def view_phase_details(self):
        """View detailed phase information"""
        print(f"\n{Colors.BOLD}Select Phase:{Colors.END}")
        for i, (phase_id, phase) in enumerate(self.data["phases"].items(), 1):
            print(f"  {i}. {phase['name']}")
        
        try:
            choice = int(input(f"\n{Colors.CYAN}Select phase: {Colors.END}").strip())
            phase_id = list(self.data["phases"].keys())[choice - 1]
            phase = self.data["phases"][phase_id]
            
            print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
            print(f"{Colors.BOLD}{phase['name']}{Colors.END}")
            print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")
            print(f"Status: {STATUS_ICONS.get(phase['status'], '⏳')} {phase['status']}")
            print(f"Progress: {self.get_progress_bar(phase['progress'])} {phase['progress']}%")
            print(f"Tasks: {phase['completed_tasks']}/{phase['total_tasks']}")
            if phase.get("started"):
                print(f"Started: {datetime.fromisoformat(phase['started']).strftime('%Y-%m-%d')}")
            if phase.get("completed"):
                print(f"Completed: {datetime.fromisoformat(phase['completed']).strftime('%Y-%m-%d')}")
        except (ValueError, IndexError):
            print(f"{Colors.RED}Invalid selection.{Colors.END}")
    
    def view_metrics(self):
        """Display project metrics"""
        metrics = self.data["metrics"]
        
        print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}Project Metrics{Colors.END}")
        print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")
        
        print(f"  📊 Total Time Spent: {Colors.CYAN}{metrics['total_time_spent']} hours{Colors.END}")
        print(f"  ✅ Tasks Completed: {Colors.GREEN}{metrics['tasks_completed']}{Colors.END}")
        print(f"  🐛 Bugs Fixed: {Colors.YELLOW}{metrics['bugs_fixed']}{Colors.END}")
        print(f"  ✨ Features Added: {Colors.MAGENTA}{metrics['features_added']}{Colors.END}")
        
        total_tasks = sum(phase["total_tasks"] for phase in self.data["phases"].values())
        completed = sum(phase["completed_tasks"] for phase in self.data["phases"].values())
        remaining = total_tasks - completed
        
        print(f"\n  📈 Overall Progress:")
        print(f"     Total Tasks: {total_tasks}")
        print(f"     Completed: {completed}")
        print(f"     Remaining: {remaining}")
        
        if metrics["total_time_spent"] > 0 and completed > 0:
            avg_time = metrics["total_time_spent"] / completed
            print(f"\n  ⏱️  Average Time per Task: {avg_time:.1f} hours")
            
            if remaining > 0:
                estimated_remaining = avg_time * remaining
                print(f"  🎯 Estimated Time Remaining: {estimated_remaining:.1f} hours")
    
    def export_report(self):
        """Export progress report to markdown"""
        report_path = Path("data/progress_report.md")
        
        with open(report_path, 'w') as f:
            f.write("# PRISM Development Progress Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Overall Status\n\n")
            f.write(f"- **Overall Progress:** {self.data['project']['overall_progress']}%\n")
            f.write(f"- **Current Phase:** {self.data['phases'][self.data['project']['current_phase']]['name']}\n\n")
            
            f.write("## Phase Progress\n\n")
            for phase_id, phase in self.data["phases"].items():
                f.write(f"### {phase['name']}\n")
                f.write(f"- Status: {phase['status']}\n")
                f.write(f"- Progress: {phase['progress']}%\n")
                f.write(f"- Tasks: {phase['completed_tasks']}/{phase['total_tasks']}\n\n")
            
            f.write("## Metrics\n\n")
            metrics = self.data["metrics"]
            f.write(f"- Total Time Spent: {metrics['total_time_spent']} hours\n")
            f.write(f"- Tasks Completed: {metrics['tasks_completed']}\n")
            f.write(f"- Bugs Fixed: {metrics['bugs_fixed']}\n")
            f.write(f"- Features Added: {metrics['features_added']}\n\n")
            
            f.write("## Recent Activity\n\n")
            for log in self.data.get("daily_logs", [])[-10:]:
                timestamp = datetime.fromisoformat(log["timestamp"]).strftime("%Y-%m-%d %H:%M")
                f.write(f"- **{timestamp}:** {log['message']}\n")
        
        print(f"{Colors.GREEN}✅ Report exported to {report_path}{Colors.END}")

def main():
    """Main entry point"""
    tracker = ProgressTracker()
    tracker.interactive_menu()

if __name__ == "__main__":
    main()

