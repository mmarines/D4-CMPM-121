## The dragon's rules on the grid: no Nodes, no engine callbacks, testable headless.
class_name Dragon
extends RefCounted

const MAX_QUEUED_TURNS := 2

var size: Vector2i
var body: Array[Vector2i] = []  # head first
var heading := Vector2i.RIGHT
var _turns: Array[Vector2i] = []  # turns wait here until the next tick (Command)


func _init(grid_size: Vector2i, length := 4) -> void:
	size = grid_size
	@warning_ignore("integer_division")  # the middle cell, rounded down, on purpose
	var start := grid_size / 2
	for i in length:
		body.append(start - heading * i)


## Queue a turn. Ignored if it would reverse into the neck or repeat the last turn,
## so two quick key presses within one tick still behave.
func turn(direction: Vector2i) -> void:
	var last: Vector2i = heading if _turns.is_empty() else _turns.back()
	if direction == last or direction == -last or _turns.size() >= MAX_QUEUED_TURNS:
		return
	_turns.append(direction)


## Return the head position for the next tick without changing the body.
func next_head() -> Vector2i:
	var next_heading := heading
	if not _turns.is_empty():
		next_heading = _turns.front()
	return body[0] + next_heading


## Advance one cell, taking the next queued turn first. The Session decides whether
## the destination is legal before this movement is applied.
func tick(grow := false) -> void:
	if not _turns.is_empty():
		heading = _turns.pop_front()
	body.push_front(body[0] + heading)
	if not grow:
		body.pop_back()
