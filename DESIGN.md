# Design

## Target

A sushi snake made of connected pieces of salmon nigiri wrapped in nori that travels along a wooden serving board. It eats sushi ingredients to grow longer and increase its score. We want the game to feel cozy, playful, and increasingly challenging as the snake grows.

Our grid is 48 × 28.

## Menu choices

| Item | Group | Done when (in your words) |
| --- | --- | --- |
| Dynamic Sushi Segments | Propose your own (pending approval) | At least four different ingredients can spawn on the board. Collecting an ingredient adds a corresponding sushi model to the snake's body. Each segment retains its sushi type during movement and turns. Tests verify that segment types are preserved during movement and growth. |
| Wasabi Powerup | Powerups | Wasabi occasionally spawns on an unoccupied cell. When the player collects it, the snake temporarily moves at half its normal speed, giving the player more time to react. Normal speed returns after five seconds. Tests verify that the powerup activates and expires correctly. |

### Menu Item A — Dynamic Sushi Segments

Instead of having every body segment look identical, the snake's appearance changes based on the ingredients it collects.

We plan to introduce four sushi varieties:

- Salmon nigiri
- Tuna nigiri
- Tamago (egg) nigiri
- Ebi (shrimp) nigiri

Each ingredient has a corresponding procedurally generated 3D model. As the player collects different ingredients, the snake gradually becomes an assorted sushi platter.

The core tracks the ingredient type of each body segment, while the application layer selects and displays the corresponding model.

### Menu Item B — Wasabi Powerup

Wasabi occasionally appears on the sushi board as a special collectible. Unlike regular ingredients, collecting wasabi does not increase the snake's length. Instead, it temporarily slows down the snake's movement, giving the player more time to navigate obstacles and avoid collisions.

- Effect: Reduces movement speed by 50%.
- Duration: Five seconds.
- Appearance: A small green pile of wasabi generated through Blender Python.
- Visual feedback: An on-screen indicator shows when the powerup is active.
- Expiration: The snake automatically returns to its normal movement speed.

The core manages the powerup's state and duration, while the application handles its visual representation and movement timing.


## Words we use

| Word | Meaning | In code |
| --- | --- | --- |
| cell | One square of the grid. | `Vector2i` |
| session | One run of the game, from the first tick until it ends; owns the board and the snake. | `Session` in `core/session.gd` |
| tick | One step of the rules; the snake moves one cell. | `Session.tick()`, `Dragon.tick()` |
| tile kind | What a cell is made of, such as floor or wall. | `Board.TILES`, `TILES` in `tools/build_art.py` |
| piece | One sushi model in the kit: head, straight, turn, or tail. | `Kit.Piece`, `PIECES` in `tools/build_art.py` |
| snake | The player-controlled chain of sushi pieces. | `core/dragon.gd` |
| ingredient | A collectible salmon piece that makes the snake grow. | `core/session.gd`, `tools/build_art.py` |
| kit | The collection of procedurally generated 3D models. | `art/dragon_kit.glb`, `core/kit.gd` |
| nori | The dark seaweed wrapping around each sushi piece. | `tools/build_art.py` |
| opening | The direction in which a body piece connects to another piece. | `Kit.OPENINGS` in `core/kit.gd` |
| voxel | A small 3D cube used to construct models. | `tools/build_art.py` |
| seed | A value used to make random food placement reproducible. | `core/session.gd` |

## Where things live

The gameplay rules are separated from rendering and input.

- `core/dragon.gd` handles snake movement, body positions, and direction changes.
- `core/session.gd` manages the overall game state, food, growth, score, and collision rules.
- `core/board.gd` defines the grid and its tile properties.
- `core/kit.gd` determines which body pieces are used and how they connect.
- `app/main.gd` handles player input, rendering, and displaying gameplay information.
- `app/stage.gd` handles the environment, lighting, and camera.
- `tools/build_art.py` generates all sushi models and materials using Blender Python.
- `art/dragon_kit.glb` stores the exported models loaded by Godot.
- `tests/` contains automated tests for the gameplay rules.

Player input is passed from the application layer to the core. The core updates the game state, and the application uses that state to update the displayed models and score. This keeps gameplay rules independent of the visual presentation.

## Adding a tile kind

1. Open `core/board.gd` and add a new tile kind to `Board.TILES`, including its collision properties.
2. Open `tools/build_art.py` and create a builder function for the new tile's geometry.
3. Add any necessary materials to the material palette.
4. Register the builder in the `TILES` dictionary using the same tile name as the core.
5. Run `deno task art` to regenerate the asset kit.
6. Use the new tile kind when constructing the board.
7. Run `deno task kit` to inspect the model.
8. Run `deno task dev` to check the tile in the game.
9. Run `deno task fmt` and `deno task ci` to verify that everything still works.

## Patterns, and what they bought us

### Separation of concerns

The core contains gameplay rules, while the application handles rendering and input. This allows us to change the original dragon into a sushi snake without rewriting the movement system. It also makes gameplay rules easier to test independently.

### Single Responsibility Principle

The dragon, board, session, and asset builders each have their own responsibilities. This makes the project easier to maintain and allows both team members to work on different parts of the game without constantly modifying the same files.

### Data-driven content

The asset builders are registered in the `PIECES` and `TILES` dictionaries in `tools/build_art.py`. Each model has a specific name that Godot uses to locate it.

This supports the Open/Closed Principle because new models and tile kinds can be introduced through additional builders and registry entries without rewriting the entire asset generation pipeline.

### Command queue

The snake uses a turn queue to handle directional input between movement ticks. This prevents multiple quick key presses from incorrectly changing the snake's direction during a single tick.

## One idea we carried over

- **The problem:** When gameplay logic and rendering are mixed together, changing visuals can accidentally affect gameplay, and testing individual rules becomes difficult.

- **The practice:** In our earlier TypeScript projects, we separated gameplay logic from presentation. We continue using this approach so that gameplay rules can be tested independently.

- **The mechanism:** Instead of TypeScript modules, we now use GDScript files inside `core/` and `app/`. We also use Blender Python to generate the visual assets independently of the gameplay code. This makes it easier to replace the original dragon with our sushi models while preserving the movement system. However, we also have to manage an additional asset generation and export pipeline.

## Sources we relied on

| Claim | Source (link) | How we checked it |
| --- | --- | --- |
| The glTF exporter preserves the Base Color input from the Principled BSDF material node. | [Blender 5.2 Manual — glTF Base Color](https://docs.blender.org/manual/en/5.2/addons/scene_gltf2.html#base-color) | We created custom salmon, rice, nori, and wood materials in `tools/build_art.py`, ran `deno task art`, and inspected the exported models using `deno task kit`. The custom colors remained visible in Godot. |
| The asset kit can be generated using Python rather than manually modeling each object in Blender. | [D4 asset builder](https://github.com/mmarines/D4-CMPM-121/blob/main/tools/build_art.py) | We replaced the original dragon builders with custom sushi builders and regenerated the GLB and Blender files using `deno task art`. |
| Each body piece must have matching openings to connect with neighboring pieces. | [D4 Kit](https://github.com/mmarines/D4-CMPM-121/blob/main/core/kit.gd) | We designed the head, straight, turn, and tail models around the existing connection directions while adding individual seaweed wraps to make each sushi piece visually distinct. |
