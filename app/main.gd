## Engine adapter: keeps the clock, passes keys to the Session, and draws the sushi snake.
## It never decides rules: those live in core/session.gd.
extends Node3D

const GRID := Vector2i(48, 28)  # a finer grid makes the sushi snake feel more precise
const TICK_SECONDS := 0.1
const CAMERA_OFFSET := Vector3(0, 11, 7.5)  # above and behind the head
const DIRECTIONS := {
	"ui_up": Vector2i.UP,
	"ui_down": Vector2i.DOWN,
	"ui_left": Vector2i.LEFT,
	"ui_right": Vector2i.RIGHT,
}

var session := Session.new(GRID)
var meshes := {}  # kit piece name -> Mesh, shared by everything that shows it (Flyweight)
var segments: Array[MeshInstance3D] = []
var food := MeshInstance3D.new()
var camera := Camera3D.new()
var score_label := Label.new()
var _clock := 0.0


func _ready() -> void:
	meshes = Stage.load_kit()
	_build_stage()
	_draw_snake()
	_draw_food()
	var hud := CanvasLayer.new()
	add_child(hud)
	score_label.text = "Score: 0"
	score_label.position = Vector2(16, 12)
	score_label.add_theme_font_size_override("font_size", 18)
	score_label.add_theme_color_override("font_color", Color("fff8e7"))
	score_label.add_theme_color_override("font_outline_color", Color("4a2e22"))
	score_label.add_theme_constant_override("outline_size", 3)
	hud.add_child(score_label)


## Input arrives as events, so even a tap shorter than one frame is never missed.
func _unhandled_input(event: InputEvent) -> void:
	for action in DIRECTIONS:
		if event.is_action_pressed(action):
			session.dragon.turn(DIRECTIONS[action])


func _process(delta: float) -> void:
	_clock += delta
	while _clock >= TICK_SECONDS:
		_clock -= TICK_SECONDS
		session.tick()
		_draw_snake()
		_draw_food()
		score_label.text = "Score: %d" % session.score
	_follow(delta)


## Sky, light, and tiles live in app/stage.gd; the camera follows the head.
func _build_stage() -> void:
	add_child(Stage.new(session.board.tiles, meshes))
	add_child(camera)
	camera.position = _center(session.dragon.body[0]) + CAMERA_OFFSET


## Ease toward the head each frame, so the camera glides while the dragon steps.
func _follow(delta: float) -> void:
	var target := _center(session.dragon.body[0]) + CAMERA_OFFSET
	camera.position = camera.position.lerp(target, 1 - exp(-3 * delta))
	camera.look_at(camera.position - CAMERA_OFFSET)


func _draw_snake() -> void:
	var body := session.dragon.body
	while segments.size() < body.size():
		var segment := MeshInstance3D.new()
		add_child(segment)
		segments.append(segment)
	var placed := Kit.layout(body)
	for i in segments.size():
		var segment := segments[i]
		segment.visible = i < body.size()
		if not segment.visible:
			continue
		var cell := body[i]
		segment.mesh = meshes[Kit.Piece.keys()[placed[i][0]].to_lower()]
		segment.position = _center(cell)
		segment.rotation.y = placed[i][1] * PI / 2


func _center(cell: Vector2i) -> Vector3:
	return Vector3(cell.x + 0.5, 0, cell.y + 0.5)


func _draw_food() -> void:
	if food.get_parent() == null:
		add_child(food)
	food.visible = session.board.tiles.has(session.food)
	if food.visible:
		food.mesh = meshes["food"]
		food.position = _center(session.food)
