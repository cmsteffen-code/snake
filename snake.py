#!/usr/bin/env python3
"""Snake, implemented with curses."""

# TODO: Adjust the food values based on the size of the board.

import argparse
import curses
import math
import random
import textwrap
from curses import textpad


class SnakeGame:
    """Implement Snake in Curses."""

    def __init__(self, stdscr, borderless=False):
        """Spawn Snake."""
        # Important variables.
        self.score = 0.0
        self.int_score = -1
        self.padding = 3
        self.food = dict()
        self.stdscr = stdscr
        self.snake_length = 3
        self.game_over = False
        self.borderless = borderless
        self.direction = curses.KEY_RIGHT
        # Define the arena boundaries.
        self.max_rows, self.max_cols = self.stdscr.getmaxyx()
        padding = 2 * self.padding + 2
        self.arena_rows = self.max_rows - padding
        self.arena_cols = self.max_cols - padding
        self.perimeter = 2 * (self.arena_rows + self.arena_cols)
        self.snake_length = self._multiply_growth(self.snake_length)
        top_border = self.padding
        left_border = self.padding
        bottom_border = self.max_rows - (self.padding + 1)
        right_border = self.max_cols - (self.padding + 1)
        self.row_borders = {top_border, bottom_border}
        self.col_borders = {left_border, right_border}
        # Curses configuration.
        curses.curs_set(0)
        self.stdscr.nodelay(1)
        self.stdscr.timeout(100)
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_RED)
        self.color_red = 1
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)
        self.color_yellow = 2
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_GREEN)
        self.color_green = 3
        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)
        self.color_white = 4
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)
        self.color_default = 5
        curses.init_pair(6, curses.COLOR_BLACK, curses.COLOR_BLUE)
        self.color_blue = 6
        # Prepare the arena.
        self._draw_arena()
        self._spawn_snake()
        self._drop_food()

    def _multiply_growth(self, units):
        """Calculate the growth multiplier."""
        polarity = -1 if abs(units) != units else 1
        units = abs(units)
        try:
            inverse_curve = 1.0 - (1.0 / self.snake_length)
            scale_multiplier = math.sqrt(self.perimeter / 4)
            return polarity * max(
                [int(units * scale_multiplier * inverse_curve), 1]
            )
        except ZeroDivisionError:
            self.game_over = True
            return 0

    def _check_loss_conditions(self):
        """Check whether we've lost."""
        (row, col) = self.snake[-1]
        if (
            (row, col) in self.snake[:-1]  # Snake ate itself.
            or row in self.row_borders  # Snake hit row border.
            or col in self.col_borders  # Snake hit col border.
        ):
            self.game_over = True

    def _check_shrink(self):
        """Check to see if the snake has shrunk."""
        if random.randint(1, self.perimeter * 2) <= self.snake_length:
            # Shrink the snake sometimes.
            self.snake_length -= self._multiply_growth(0.25)

    def _draw_arena(self):
        """Draw the initial game screen."""
        self.stdscr.clear()
        self._draw_box(
            (self.padding, self.padding),
            (
                self.max_rows - (self.padding + 1),
                self.max_cols - (self.padding + 1),
            ),
        )

    def _draw_box(self, top_left, bottom_right):
        """Draw a box on the screen."""
        textpad.rectangle(
            self.stdscr,
            top_left[0],
            top_left[1],
            bottom_right[0],
            bottom_right[1],
        )

    def _draw_object(self, coords, color=None):
        """Place an object on the screen. Coords can be tuple or list."""
        color = self.color_default if not color else color
        if isinstance(coords, tuple):
            coords = [coords]
        for (row, col) in coords:
            self.stdscr.addstr(row, col, " ", curses.color_pair(color))

    def _drop_food(self, special=False):
        """Drop some food for the snake."""
        new_food = self._random_coords()
        while new_food in self.snake or new_food in self.food:
            new_food = self._random_coords()
        index = (
            0
            if not special
            else 1
            if random.randint(1, 100) > 33
            else 2
            if random.randint(1, 100) > 33
            else 3
        )
        self.food[new_food] = self._multiply_growth([1, -1, 3, 9][index])
        food_color = [
            self.color_blue,
            self.color_red,
            self.color_green,
            self.color_yellow,
        ][index]
        self._draw_object(new_food, food_color)

    def _eat_food(self):
        """Check whether the snake ate the food."""
        snake_head = self.snake[-1]
        if snake_head in self.food:
            value = self.food[snake_head]
            del self.food[snake_head]
            self.snake_length += value
            self.score += self.snake_length
            self._drop_food()
            if random.randint(1, 100) > 66:
                self._drop_food(special=True)

    def _end_game(self):
        """Show the final score and exit the game."""
        self.stdscr.nodelay(0)
        messages = [
            "GAME OVER",
            f"Final Score: {self.int_score}",
            "<press enter>",
        ]
        max_length = max(len(message) for message in messages)
        row = self.max_rows // 2 - len(messages) // 2
        col = self.max_cols // 2 - max_length // 2
        self._draw_box(
            (row - 1, col - 1), (row + len(messages), col + max_length)
        )
        for index, message in enumerate(messages):
            self.stdscr.addstr(row + index, col, " " * max_length)
            self.stdscr.addstr(
                row + index, self.max_cols // 2 - len(message) // 2, message
            )
        key = self.stdscr.getch()
        while key != curses.KEY_ENTER and key not in [10, 13]:
            key = self.stdscr.getch()

    def _move_snake(self):
        """Move the snake."""
        # Calculate the new head position.
        (row, col) = self.snake[-1]
        if self.direction in [curses.KEY_UP, curses.KEY_DOWN]:
            inc = 1 if self.direction == curses.KEY_DOWN else -1
            row += inc
            self.stdscr.timeout(150)
        elif self.direction in [curses.KEY_LEFT, curses.KEY_RIGHT]:
            inc = 1 if self.direction == curses.KEY_RIGHT else -1
            col += inc
            self.stdscr.timeout(100)
        if self.borderless:
            row -= (inc * self.arena_rows) if row in self.row_borders else 0
            col -= (inc * self.arena_cols) if col in self.col_borders else 0
        # Move the snake's head.
        self.snake.append((row, col))
        self._draw_object((row, col), self.color_white)

    def _parse_input(self):
        """Receive and process user input."""
        key = self.stdscr.getch()
        if key in [ord("q"), ord("Q")]:
            self.game_over = True
        elif key in [ord("p"), ord("P")]:
            self.stdscr.nodelay(0)
            self.stdscr.addstr(0, 0, "Paused!")
            self.stdscr.getch()
            self.stdscr.addstr(0, 0, " " * 7)
            self.stdscr.nodelay(1)
        elif key in [
            curses.KEY_UP,
            curses.KEY_DOWN,
            curses.KEY_LEFT,
            curses.KEY_RIGHT,
        ]:
            row_moves = [curses.KEY_UP, curses.KEY_DOWN]
            col_moves = [curses.KEY_LEFT, curses.KEY_RIGHT]
            self.direction = (
                key
                if not (
                    (key in row_moves and self.direction in row_moves)
                    or (key in col_moves and self.direction in col_moves)
                )
                else self.direction
            )

    def _random_coords(self):
        """Generate random coordinates within the arena."""
        return (
            random.randint(
                self.padding + 2, self.max_rows - (self.padding + 3)
            ),
            random.randint(
                self.padding + 2, self.max_cols - (self.padding + 3)
            ),
        )

    def _spawn_snake(self):
        """Spawn the snake."""
        self.snake = [
            (
                self.max_rows // 2,
                self.max_cols // 2 - self.snake_length // 2 + index,
            )
            for index in range(self.snake_length)
        ]
        # Draw the snake.
        self._draw_object(self.snake, self.color_white)

    def _trim_tail(self):
        """Trim the snake's tail."""
        while len(self.snake) > self.snake_length:
            self._draw_object(self.snake.pop(0))

    def _update_score(self):
        """Increment the user's score."""
        points = 10 / self.perimeter * self.snake_length
        self.score += points
        last_score = int(self.int_score)
        self.int_score = int(self.score)
        if self.int_score != last_score:
            score_text = f"Score: {self.int_score}"
            col = self.max_cols // 2 - len(score_text) // 2
            self._draw_box(
                (self.padding - 3, col - 1),
                (self.padding - 1, col + len(score_text)),
            )
            self.stdscr.addstr(self.padding - 2, col, score_text)

    def run(self):
        """Execute the game loop."""
        while not self.game_over:
            try:
                self.stdscr.refresh()
                self._parse_input()
                self._move_snake()
                self._eat_food()
                self._check_shrink()
                self._trim_tail()
                self._check_loss_conditions()
                self._update_score()
            except IndexError:
                self.game_over = True
        self._end_game()


def main(stdscr):
    """Run the Snake game."""
    snake = SnakeGame(stdscr, args.borderless)
    snake.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Eat food, stay alive, get the high score!",
        epilog=textwrap.dedent(
            """\
        Eat food to stay alive and grow longer.
        Gain points for survival.
        Don't hit the borders, starve to death, or eat yourself!

        Food Types:
        - Blue:  Grow by 1
        - Green: Grow by 3
        - Gold:  Grow by 9
        - Red:   Poison! Shrink by 3
        """
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-b",
        "--borderless",
        action="store_true",
        help="enable wrap-around at arena borders",
    )
    args = parser.parse_args()
    curses.wrapper(main)
