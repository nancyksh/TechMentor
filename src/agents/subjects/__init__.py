from .base import answer_question
from .os_agent import answer as os_answer
from .dbms_agent import answer as dbms_answer
from .cn_agent import answer as cn_answer
from .dsa_agent import answer as dsa_answer

AGENT_MAP = {
    "OS": os_answer,
    "DBMS": dbms_answer,
    "CN": cn_answer,
    "DSA": dsa_answer,
}

__all__ = ["answer_question", "AGENT_MAP"]
