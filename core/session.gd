## One run at the game: the board and the dragon on it, from the first tick until the
## run ends. Rules that involve more than the dragon (food, score, what the dragon can
## run into) belong here, so Dragon stays about movement and app/ only draws.
class_name Session
extends RefCounted

var board: Board
var dragon: Dragon
var food := Vector2i(-1, -1)
var score := 0
var rng := RandomNumberGenerator.new()
var started := false
var running := true


func _init(grid_size: Vector2i) -> void:
	board = Board.bordered(grid_size)
	dragon = Dragon.new(grid_size)
	rng.seed = 12345
	spawn_food()


## One step of the rules. TODO for D4: food, growth, and collisions with the dragon's
## own body and with solid tiles (board.is_solid). Each needs the dragon and something
## else, which is why they go here rather than in Dragon.tick.
func tick() -> void:
	if not started or not running:
		return

	var candidate := dragon.next_head()
	if board.is_solid(candidate):
		running = false
		return

	var tail_is_leaving: bool = candidate == dragon.body.back()
	if candidate in dragon.body and not tail_is_leaving:
		running = false
		return

	var eating := candidate == food
	dragon.tick(eating)
	if eating:
		score += 1
		spawn_food()


func spawn_food() -> void:
	var free_cells: Array[Vector2i] = []
	for cell in board.tiles:
		if not board.is_solid(cell) and not cell in dragon.body:
			free_cells.append(cell)
	if free_cells.is_empty():
		food = Vector2i(-1, -1)
	else:
		food = free_cells[rng.randi_range(0, free_cells.size() - 1)]


func start(direction: Vector2i) -> void:
	if running:
		started = true
		dragon.turn(direction)


func restart() -> void:
	var grid_size := board.size
	board = Board.bordered(grid_size)
	dragon = Dragon.new(grid_size)
	score = 0
	started = false
	running = true
	rng.seed = 12345
	spawn_food()
