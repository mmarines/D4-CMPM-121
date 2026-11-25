extends "res://tests/test_case.gd"


func test_a_tick_moves_the_dragon_head() -> void:
	var session := Session.new(Vector2i(10, 10))
	session.tick()
	assert_eq(session.dragon.body[0], Vector2i(6, 5))


func test_the_dragon_starts_on_open_floor_inside_a_wall() -> void:
	var session := Session.new(Vector2i(10, 10))
	assert_true(session.board.is_solid(Vector2i(0, 0)))
	assert_true(not session.board.is_solid(session.dragon.body[0]))


func test_eating_grows_and_scores() -> void:
	var session := Session.new(Vector2i(10, 10))
	var initial_size := session.dragon.body.size()
	session.food = session.dragon.body[0] + session.dragon.heading

	session.tick()

	assert_eq(session.dragon.body.size(), initial_size + 1)
	assert_eq(session.score, 1)


func test_new_food_never_appears_on_the_body() -> void:
	var session := Session.new(Vector2i(10, 10))
	session.food = session.dragon.body[0] + session.dragon.heading

	session.tick()

	assert_true(not session.food in session.dragon.body)
