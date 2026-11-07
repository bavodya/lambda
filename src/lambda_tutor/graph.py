from langgraph.graph import StateGraph, END
from lambda_tutor.state import TutorState
from lambda_tutor.agents.diagnostic import diagnose
from lambda_tutor.agents.methodist import retrieve
from lambda_tutor.agents.tutor import tutor


def diagnose_node(state: TutorState) -> dict:
    return diagnose(state)


def retrieve_node(state: TutorState) -> dict:
    return retrieve(state)


def tutor_node(state: TutorState) -> dict:
    return tutor(state)


def build_graph():
    graph = StateGraph(TutorState)

    graph.add_node("diagnose", diagnose_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("tutor", tutor_node)

    graph.set_entry_point("diagnose")
    graph.add_edge("diagnose", "retrieve")
    graph.add_edge("retrieve", "tutor")
    graph.add_edge("tutor", END)

    return graph.compile()