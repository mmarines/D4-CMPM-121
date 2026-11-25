extends "res://tests/test_case.gd"


func test_a_tick_moves_the_dragon_head() -> void:
	var session := Session.new(Vector2i(10, 10))
	session.start(Vector2i.RIGHT)
	session.tick()
	assert_eq(session.dragon.body[0], Vector2i(6, 5))


func test_the_dragon_starts_on_open_floor_inside_a_wall() -> void:
	var session := Session.new(Vector2i(10, 10))
	assert_true(session.board.is_solid(Vector2i(0, 0)))
	assert_true(not session.board.is_solid(session.dragon.body[0]))


func test_eating_grows_and_scores() -> void:
	var session := Session.new(Vector2i(10, 10))
	var initial_size := session.dragon.body.size()
	session.start(Vector2i.RIGHT)
	session.food = session.dragon.body[0] + session.dragon.heading

	session.tick()

	assert_eq(session.dragon.body.size(), initial_size + 1)
	assert_eq(session.score, 1)


func test_new_food_never_appears_on_the_body() -> void:
	var session := Session.new(Vector2i(10, 10))
	session.start(Vector2i.RIGHT)
	session.food = session.dragon.body[0] + session.dragon.heading

	session.tick()

	assert_true(not session.food in session.dragon.body)


func test_waits_for_the_first_arrow_key() -> void:
	var session := Session.new(Vector2i(10, 10))
	var head := session.dragon.body[0]

	session.tick()

	assert_eq(session.dragon.body[0], head)


func test_wall_collision_stops_the_run() -> void:
	var session := Session.new(Vector2i(10, 10))
	session.started = true
	session.board.tiles[session.dragon.body[0] + Vector2i.RIGHT] = "wall"

	session.tick()

	assert_true(not session.running)


func test_moving_into_the_tail_is_safe() -> void:
	var session := Session.new(Vector2i(10, 10))
	session.started = true
	session.dragon.body = [
		Vector2i(5, 5),
		Vector2i(5, 6),
		Vector2i(5, 4),
	]
	session.dragon.heading = Vector2i.UP
	session.food = Vector2i(8, 8)

	session.tick()
	assert_true(session.running)


func test_biting_the_body_ends_the_run() -> void:
	var session := Session.new(Vector2i(10, 10))
	session.started = true
	session.dragon.body = [
		Vector2i(5, 5),
		Vector2i(6, 5),
		Vector2i(7, 5),
	]
	session.dragon.heading = Vector2i.RIGHT
	session.food = Vector2i(8, 8)

	session.tick()

	assert_true(not session.running)
