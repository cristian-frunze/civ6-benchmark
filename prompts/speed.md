## Faster turns

Each of your steps takes far longer than a tool call, so do more per step:

- Start each turn with `get_turn_briefing`: overview, units, cities and notifications in one call.
- Give the turn's routine orders (moves, unit actions, production, purchases, research, policies) in one `issue_orders` call, then check each result.
- When you need several independent reads (a few map areas, advisors, diplomacy), call them in parallel in one step.
