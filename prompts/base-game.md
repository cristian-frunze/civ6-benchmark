## This game: base ruleset

This game uses the base Civilization VI ruleset, without the Rise and Fall or Gathering Storm expansions. These don't exist here, so skip any guidance and tools about them:

- governors and loyalty
- era score, golden and dark ages, and dedications
- diplomatic favor, the World Congress, diplomatic victory points and emergencies
- strategic resource stockpiles

Other base-game rules that differ from the playbook:

- Science victory takes 5 space projects: Launch Earth Satellite, Launch Moon Landing, and the 3 Mars colony projects (Reactor, Habitation, Hydroponics). `get_victory_progress` counts them.
- There is one alliance type. It needs declared friendship and the Civil Service civic.

The victory types are Science, Culture, Domination and Religious, plus Score at the turn limit. If a tool fails because a feature is missing, note it in the `tooling` reflection and keep playing.
