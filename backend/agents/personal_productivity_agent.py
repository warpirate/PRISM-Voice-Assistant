"""
Personal Productivity Agent
Handles focus sessions, habits, routines, and productivity optimization
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from loguru import logger

from backend.agents.base_agent import BaseAgent, AgentCapability
from backend.agents.agent_response import AgentResponse, ResponseStatus


class PersonalProductivityAgent(BaseAgent):
    """
    Agent for personal productivity management
    
    Capabilities:
    - Daily routine optimization
    - Focus session management (Pomodoro-style)
    - Habit tracking
    - Break suggestions
    - Productivity analytics
    """
    
    def __init__(self):
        super().__init__(
            name="PersonalProductivityAgent",
            capabilities=[AgentCapability.PRODUCTIVITY]
        )
        
        self.habits: List[Dict[str, Any]] = []
        self.focus_sessions: List[Dict[str, Any]] = []
        self.routines: List[Dict[str, Any]] = []
        self.current_session: Optional[Dict[str, Any]] = None
    
    async def initialize(self) -> bool:
        """Initialize productivity agent"""
        try:
            # Load default routines
            self._load_default_routines()
            
            logger.info("PersonalProductivityAgent initialized")
            return True
            
        except Exception as e:
            logger.error(f"PersonalProductivityAgent initialization failed: {str(e)}")
            return False
    
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Execute productivity task
        
        Supported tasks:
        - "start focus session"
        - "track habit [habit_name]"
        - "suggest break"
        - "optimize routine"
        - "show productivity stats"
        - "open_app" (with parameters from context)
        """
        task_lower = task.lower()
        
        try:
            # Check for structured task from context (agent coordinator)
            if context and 'task_type' in context:
                task_type = context['task_type']
                params = context.get('parameters', {})
                
                if task_type == 'open_app':
                    return await self._handle_open_app(params)
            
            if 'focus' in task_lower and 'start' in task_lower:
                duration = self._extract_duration(task, default=25)
                return await self._start_focus_session(duration)
            
            elif 'focus' in task_lower and 'end' in task_lower:
                return await self._end_focus_session()
            
            elif 'habit' in task_lower:
                habit_name = self._extract_habit_name(task)
                return await self._track_habit(habit_name)
            
            elif 'break' in task_lower:
                return await self._suggest_break()
            
            elif 'routine' in task_lower:
                return await self._optimize_routine()
            
            elif 'stats' in task_lower or 'productivity' in task_lower:
                return await self._get_productivity_stats()
            
            else:
                return AgentResponse.failure(
                    message=f"Unknown productivity operation: {task}",
                    agent_name=self.name,
                    error="Task not recognized"
                )
                
        except Exception as e:
            logger.error(f"Productivity agent execution error: {str(e)}")
            return AgentResponse.failure(
                message=f"Productivity operation failed: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    async def _start_focus_session(self, duration_minutes: int = 25) -> AgentResponse:
        """Start a focus session (Pomodoro-style)"""
        if self.current_session:
            return AgentResponse.failure(
                message="A focus session is already in progress",
                agent_name=self.name,
                error="Session already active",
                data={'current_session': self.current_session}
            )
        
        try:
            self.current_session = {
                'started': datetime.now(),
                'duration_minutes': duration_minutes,
                'end_time': datetime.now() + timedelta(minutes=duration_minutes),
                'status': 'active'
            }
            
            return AgentResponse.success(
                message=f"Focus session started for {duration_minutes} minutes",
                agent_name=self.name,
                data=self.current_session,
                actions_taken=[f"Started {duration_minutes}-minute focus session"],
                suggestions=[
                    "Minimize distractions",
                    "Turn off notifications",
                    "Focus on one task at a time"
                ]
            )
            
        except Exception as e:
            return AgentResponse.failure(
                message=f"Failed to start focus session: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    async def _end_focus_session(self) -> AgentResponse:
        """End current focus session"""
        if not self.current_session:
            return AgentResponse.failure(
                message="No active focus session",
                agent_name=self.name,
                error="No session active"
            )
        
        try:
            ended = datetime.now()
            duration = (ended - self.current_session['started']).total_seconds() / 60
            
            session_record = {
                **self.current_session,
                'ended': ended,
                'actual_duration': duration,
                'completed': duration >= self.current_session['duration_minutes'] * 0.9
            }
            
            self.focus_sessions.append(session_record)
            self.current_session = None
            
            return AgentResponse.success(
                message=f"Focus session completed ({duration:.1f} minutes)",
                agent_name=self.name,
                data=session_record,
                actions_taken=["Ended focus session"],
                suggestions=["Take a 5-minute break before next session"]
            )
            
        except Exception as e:
            return AgentResponse.failure(
                message=f"Failed to end focus session: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    async def _track_habit(self, habit_name: str) -> AgentResponse:
        """Track a habit completion"""
        if not habit_name:
            return AgentResponse.failure(
                message="No habit name specified",
                agent_name=self.name,
                error="Missing habit name"
            )
        
        try:
            # Find or create habit
            habit = next((h for h in self.habits if h['name'] == habit_name), None)
            
            if not habit:
                habit = {
                    'name': habit_name,
                    'created': datetime.now().isoformat(),
                    'completions': [],
                    'streak': 0
                }
                self.habits.append(habit)
            
            # Record completion
            today = datetime.now().date().isoformat()
            if today not in habit['completions']:
                habit['completions'].append(today)
                habit['streak'] += 1
            
            return AgentResponse.success(
                message=f"Habit '{habit_name}' tracked (Streak: {habit['streak']} days)",
                agent_name=self.name,
                data=habit,
                actions_taken=[f"Tracked habit: {habit_name}"],
                suggestions=["Keep up the streak!" if habit['streak'] >= 3 else "Stay consistent!"]
            )
            
        except Exception as e:
            return AgentResponse.failure(
                message=f"Failed to track habit: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    async def _suggest_break(self) -> AgentResponse:
        """Suggest a break based on work patterns"""
        try:
            # Calculate time since last break
            if self.focus_sessions:
                last_session = self.focus_sessions[-1]
                last_end = datetime.fromisoformat(last_session['ended']) if 'ended' in last_session else datetime.now()
                time_since = (datetime.now() - last_end).total_seconds() / 60
            else:
                time_since = 60  # Default to suggesting break
            
            if time_since < 15:
                suggestion = "You just took a break recently. Keep working!"
            elif time_since < 60:
                suggestion = "Consider a 5-minute break soon"
            else:
                suggestion = "Time for a break! You've been working hard."
            
            break_activities = [
                "Stretch your body",
                "Get some water",
                "Look away from screen (20-20-20 rule)",
                "Take a short walk",
                "Do some deep breathing"
            ]
            
            return AgentResponse.success(
                message=suggestion,
                agent_name=self.name,
                data={
                    'time_since_break': time_since,
                    'break_activities': break_activities
                },
                suggestions=break_activities[:3]
            )
            
        except Exception as e:
            return AgentResponse.failure(
                message=f"Failed to suggest break: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    async def _optimize_routine(self) -> AgentResponse:
        """Optimize daily routine based on patterns"""
        try:
            # Analyze focus sessions to find optimal work times
            if len(self.focus_sessions) < 5:
                return AgentResponse.success(
                    message="Need more data to optimize routine",
                    agent_name=self.name,
                    data={'sessions_needed': 5 - len(self.focus_sessions)},
                    suggestions=["Complete more focus sessions to get personalized insights"]
                )
            
            # Calculate average productivity by time of day
            morning_sessions = [s for s in self.focus_sessions 
                              if 6 <= datetime.fromisoformat(s['started']).hour < 12]
            afternoon_sessions = [s for s in self.focus_sessions 
                                 if 12 <= datetime.fromisoformat(s['started']).hour < 18]
            
            insights = {
                'total_sessions': len(self.focus_sessions),
                'morning_sessions': len(morning_sessions),
                'afternoon_sessions': len(afternoon_sessions),
                'best_time': 'morning' if len(morning_sessions) > len(afternoon_sessions) else 'afternoon'
            }
            
            return AgentResponse.success(
                message="Routine optimization complete",
                agent_name=self.name,
                data=insights,
                suggestions=[
                    f"Your most productive time is {insights['best_time']}",
                    "Schedule important tasks during peak hours",
                    "Take regular breaks to maintain focus"
                ]
            )
            
        except Exception as e:
            return AgentResponse.failure(
                message=f"Failed to optimize routine: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    async def _get_productivity_stats(self) -> AgentResponse:
        """Get productivity statistics"""
        try:
            today = datetime.now().date()
            week_ago = today - timedelta(days=7)
            
            # Calculate stats
            total_sessions = len(self.focus_sessions)
            total_minutes = sum(s.get('actual_duration', 0) for s in self.focus_sessions)
            
            recent_sessions = [s for s in self.focus_sessions 
                             if datetime.fromisoformat(s['started']).date() >= week_ago]
            
            stats = {
                'total_sessions': total_sessions,
                'total_focus_hours': total_minutes / 60,
                'sessions_this_week': len(recent_sessions),
                'active_habits': len(self.habits),
                'average_session_length': total_minutes / total_sessions if total_sessions > 0 else 0
            }
            
            return AgentResponse.success(
                message="Productivity statistics",
                agent_name=self.name,
                data=stats,
                suggestions=[
                    "Keep tracking your focus sessions",
                    "Maintain your habits consistently"
                ]
            )
            
        except Exception as e:
            return AgentResponse.failure(
                message=f"Failed to get stats: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    def _load_default_routines(self):
        """Load default routine templates"""
        self.routines = [
            {
                'name': 'Morning Routine',
                'time': '08:00',
                'activities': ['Review goals', 'Plan day', 'First focus session']
            },
            {
                'name': 'Afternoon Routine',
                'time': '14:00',
                'activities': ['Review progress', 'Second focus session', 'Break']
            }
        ]
    
    def _extract_duration(self, task: str, default: int = 25) -> int:
        """Extract duration in minutes from task"""
        import re
        match = re.search(r'(\d+)\s*(?:minute|min)', task.lower())
        if match:
            return int(match.group(1))
        return default
    
    def _extract_habit_name(self, task: str) -> str:
        """Extract habit name from task"""
        task_lower = task.lower()
        if 'track habit' in task_lower:
            habit = task_lower.split('track habit', 1)[1].strip()
            return habit.strip('"\'')
        return task
    
    async def _handle_open_app(self, params: Dict[str, Any]) -> AgentResponse:
        """Handle opening application - delegate to system control"""
        return AgentResponse.failure(
            message="Application opening should be handled by system control",
            agent_name=self.name,
            error="Wrong agent - use system_control capability",
            data={'redirect_to': 'system_control', 'parameters': params}
        )
    
    async def shutdown(self) -> bool:
        """Cleanup and shutdown"""
        if self.current_session:
            await self._end_focus_session()
        
        logger.info(f"PersonalProductivityAgent shutting down (sessions: {len(self.focus_sessions)}, habits: {len(self.habits)})")
        return True
