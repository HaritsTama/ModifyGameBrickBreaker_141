import random
import tkinter as tk

class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


class Ball(GameObject):
    def __init__(self, canvas, x, y):
        self.radius = 5
        self.direction = [1, -1]
        self.speed = 10
        self.damage = 1  # Normal damage
        self.original_color = "white"
        item = canvas.create_oval(x - self.radius, y - self.radius,
                                  x + self.radius, y + self.radius,
                                  fill=self.original_color)
        super(Ball, self).__init__(canvas, item)

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
        if coords[1] <= 0:
            self.direction[1] *= -1
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            coords = game_object.get_position()
            if x > coords[2]:
                self.direction[0] = 1
            elif x < coords[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1
        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit(self.damage)

    def activate_power_up(self):
        self.damage = 2
        self.canvas.itemconfig(self.item, fill="red")
        self.canvas.after(8000, self.deactivate_power_up)  # Revert after 8 seconds

    def deactivate_power_up(self):
        self.damage = 1
        self.canvas.itemconfig(self.item, fill=self.original_color)


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 80
        self.height = 10
        self.ball = None
        self.speed = 20
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 1.5,
                                       x + self.width / 2,
                                       y + self.height / 1.5,
                                       fill='#FFB643')
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)


class Brick(GameObject):
    COLORS = {1: '#4535AA', 2: '#ED639E', 3: '#8FE1A2'}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        color = Brick.COLORS[hits]
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=color, tags='brick')
        super(Brick, self).__init__(canvas, item)

    def hit(self, damage):
        self.hits -= damage
        if self.hits <= 0:
            if random.random() < 0.25:  # 25% chance to drop power-up
                self.drop_power_up()
            self.delete()
        else:
            self.canvas.itemconfig(self.item, fill=Brick.COLORS[self.hits])

    def drop_power_up(self):
        x, y, _, _ = self.get_position()
        power_up = PowerUp(self.canvas, x, y)
        self.canvas.master.power_ups.append(power_up)


class PowerUp(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 20
        self.height = 20
        self.y_velocity = 5
        item = canvas.create_rectangle(x - self.width / 2, y - self.height / 2,
                                       x + self.width / 2, y + self.height / 2,
                                       fill="yellow", tags="powerup")
        super(PowerUp, self).__init__(canvas, item)

    def update(self):
        self.move(0, self.y_velocity)


class Game(tk.Frame):
    def __init__(self, master):
        super(Game, self).__init__(master)
        self.lives = 3
        self.width = 610
        self.height = 400
        self.canvas = tk.Canvas(self, bg='black', width=self.width, height=self.height)
        self.canvas.pack()
        self.pack()

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width / 2, 326)
        self.items[self.paddle.item] = self.paddle

        for x in range(5, self.width - 5, 75):
            self.add_brick(x + 37.5, 50, 3)
            self.add_brick(x + 37.5, 70, 2)
            self.add_brick(x + 37.5, 90, 1)

        self.hud = None
        self.power_ups = []
        self.setup_game()
        self.canvas.focus_set()

        self.moving_left = False
        self.moving_right = False
        self.canvas.bind('<Left>', lambda event: self.start_move_left())
        self.canvas.bind('<Right>', lambda event: self.start_move_right())
        self.canvas.bind('<KeyRelease-Left>', lambda event: self.stop_move_left())
        self.canvas.bind('<KeyRelease-Right>', lambda event: self.stop_move_right())

    def start_move_left(self):
        self.moving_left = True

    def start_move_right(self):
        self.moving_right = True

    def stop_move_left(self):
        self.moving_left = False

    def stop_move_right(self):
        self.moving_right = False

    def game_loop(self):
        self.check_collisions()
        for power_up in self.power_ups[:]:
            power_up.update()
            if self.is_collision(self.paddle, power_up):
                power_up.delete()
                self.power_ups.remove(power_up)
                self.ball.activate_power_up()

        if self.ball.get_position()[3] >= self.height:
            self.ball.speed = None
            self.lives -= 1
            if self.lives < 0:
                self.draw_text(300, 200, 'You Lose! Game Over!')
            else:
                self.after(1000, self.setup_game)
        else:
            self.ball.update()

            if self.moving_left:
                self.paddle.move(-self.paddle.speed)
            elif self.moving_right:
                self.paddle.move(self.paddle.speed)

            self.after(50, self.game_loop)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        self.ball.collide(objects)

    def is_collision(self, obj1, obj2):
        x1, y1, x2, y2 = obj1.get_position()
        x3, y3, x4, y4 = obj2.get_position()
        return not (x2 < x3 or x4 < x1 or y2 < y3 or y4 < y1)

    def setup_game(self):
        self.add_ball()
        self.update_lives_text()
        self.text = self.draw_text(300, 200, 'Press Space to start', size='40', fill='white')
        self.canvas.bind('<space>', lambda _: self.start_game())

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, 310)
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size='40', fill='white'):
        font = ('Forte', size)
        return self.canvas.create_text(x, y, text=text, font=font, fill=fill)

    def update_lives_text(self):
        text = 'Lives: %s' % self.lives
        if self.hud is None:
            self.hud = self.draw_text(50, 20, text, 15, fill='white')
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def start_game(self):
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        self.paddle.ball = None
        self.game_loop()


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Break those Bricks!')
    game = Game(root)
    game.mainloop()

