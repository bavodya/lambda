from lambda_tutor.graph import build_graph
from lambda_tutor.state import make_initial_state

app = build_graph()
state = make_initial_state(task="Решите log(x-1) = 2", steps=["x - 1 = 100", "x = 101"])
result = app.invoke(state)
print(result)