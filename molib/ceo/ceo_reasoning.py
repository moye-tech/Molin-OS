"""
Hermes OS — 多轮推理循环
"""
import uuid
from .ceo import CEO

class CEOReasoningLoop:
    def __init__(self):
        self.sessions = {}
    
    async def run(self, session_id: str, user_input: str, budget=None, timeline=None):
        """多轮推理对话"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {"history": [], "ceo": CEO()}
        
        session = self.sessions[session_id]
        result = await session["ceo"].run_async(user_input, budget, timeline)
        session["history"].append({"role": "user", "content": user_input})
        session["history"].append({"role": "assistant", "content": str(result)})
        
        return {
            "session_id": session_id,
            "response": result,
            "history_length": len(session["history"]),
        }
