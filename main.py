import pygame
import csv
import sys
from pygame.locals import *
from PIL import Image
import os
from collections import deque
from datetime import datetime

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 102, 204)
TRANSPARENT = (255, 255, 255, 0)  # Fully transparent white
HOVER_COLOR = (0, 140, 255)
CLICK_COLOR = (0, 80, 160)

# Fonts
pygame.init()
FONT = pygame.font.Font(None, 18)
LARGE_FONT = pygame.font.Font(None, 24)

# CSV files
TIMETABLE_FILE = "C:/Users/Asus/OneDrive/Desktop/myenv/AIwithHome/AI_final.proj/timetable.csv"
ROOMS_FILE = "C:/Users/Asus/OneDrive/Desktop/myenv/AIwithHome/AI_final.proj/rooms.csv"

# Button dimensions
BUTTON_WIDTH = 200
BUTTON_HEIGHT = 40
BUTTON_SPACING = 20

# Room Coordinates (grid system)
ROOM_COORDINATES = {
    "START": (5, 13),  # Starting point
    "APP DEV 301": (4, 13),
    "BIZ LAB 201": (4, 13),
    "ICT 202": (4, 6),
    "ICT 203": (6, 13),
    "ICT 205": (14, 13),
    "ICT 206": (19, 6),
    "ICT 207": (19, 13),
    "ICT 302": (4, 6),
    "ICT 303": (6, 13),
    "ICT 305": (14, 13),
    "ICT 306": (19, 13),
    "ICT 307": (19, 6)
}

GRID_SIZE = 40  # A 10x10 grid for visualization

# Load CSV data
def load_csv(file_path):
    with open(file_path, mode="r") as file:
        reader = csv.DictReader(file)
        return [row for row in reader]

def bfs_csp_search(timetable, all_rooms, time, day):
    occupied_rooms = set()  # Set to store names of occupied rooms
    available_rooms = set(room["room"] for room in all_rooms)  # Set of all room names

    # Iterate through the timetable to find occupied rooms
    for entry in timetable:
        entry_time_range = entry["time"].split(" - ")
        if len(entry_time_range) == 2:
            start_time, end_time = entry_time_range
            # Ensure we check only the relevant day and time range
            if time >= start_time and time <= end_time and entry["day"].lower() == day.lower():
                occupied_rooms.add(entry["room"])  # Add room name as a string to the set

    # Remove occupied rooms from the available rooms
    available_rooms = list(available_rooms - occupied_rooms)  # Convert to list for the return
    return available_rooms


# Manhattan Distance Heuristic
def manhattan_distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


# A* Search Algorithm
def astar_search(start, goal):
    open_list = []
    closed_list = set()
    came_from = {}
    g_score = {start: 0}
    f_score = {start: manhattan_distance(start, goal)}
    open_list.append((f_score[start], start))

    while open_list:
        _, current = min(open_list, key=lambda x: x[0])
        open_list.remove((f_score[current], current))

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]  # Return reversed path

        closed_list.add(current)
        x, y = current
        neighbors = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
        for neighbor in neighbors:
            if neighbor in closed_list or not (0 <= neighbor[0] < GRID_SIZE and 0 <= neighbor[1] < GRID_SIZE):
                continue

            tentative_g_score = g_score[current] + 1
            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + manhattan_distance(neighbor, goal)
                if neighbor not in [item[1] for item in open_list]:
                    open_list.append((f_score[neighbor], neighbor))

    return []

# Draw text
def draw_text(surface, text, color, x, y, font=FONT):
    text_obj = font.render(text, True, color)
    surface.blit(text_obj, (x, y))

# Draw button
def draw_button(surface, rect, text, color, text_color):
    pygame.draw.rect(surface, color, rect)
    draw_text(surface, text, text_color, rect.x + 10, rect.y + 5)

def draw_grid(surface, grid_size):
    cell_size = 50
    transparent_surface = pygame.Surface((grid_size * cell_size, grid_size * cell_size), pygame.SRCALPHA)
    for x in range(0, grid_size * cell_size, cell_size):
        pygame.draw.line(transparent_surface, BLACK, (x, 0), (x, grid_size * cell_size), 1)
    for y in range(0, grid_size * cell_size, cell_size):
        pygame.draw.line(transparent_surface, BLACK, (0, y), (grid_size * cell_size, y), 1)
    surface.blit(transparent_surface, (0, 0))


def visualize_path(surface, path, start, destination, cell_size=50):
    """Visualize A* pathfinding with a moving line."""
    
    # Create a transparent surface
    transparent_surface = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
    
    for i, position in enumerate(path):
        pygame.time.delay(200)  # Delay for animation
        
        # Fill the transparent surface with transparency (not affecting grid)
        transparent_surface.fill((0, 0, 0, 0))  # Transparent fill (fully transparent)

        # Blit the transparent surface onto the main surface (clears it with transparency)
        surface.blit(transparent_surface, (0, 0))

        # Redraw the grid and path
        draw_grid(surface, GRID_SIZE)

        # Highlight start and destination
        pygame.draw.rect(surface, (0, 255, 0), (start[0] * cell_size, start[1] * cell_size, cell_size, cell_size))
        pygame.draw.rect(surface, (255, 0, 0), (destination[0] * cell_size, destination[1] * cell_size, cell_size, cell_size))

        # Draw the moving line (path)
        for j in range(i + 1):
            x, y = path[j]
            pygame.draw.circle(surface, BLUE, (x * cell_size + cell_size // 2, y * cell_size + cell_size // 2), 5)

        pygame.display.flip()

def show_map_window_with_guide(room_name):
    map_window = pygame.display.set_mode((1200, 700))
    pygame.display.set_caption(f"Map for {room_name}")
    map_window.fill(WHITE)

    start = ROOM_COORDINATES["START"]
    destination = ROOM_COORDINATES.get(room_name)

    if not destination:
        print("Room not found!")
        return

    path = astar_search(start, destination)

    try:
        # Load background image 
        background_image = pygame.image.load("C:/Users/Asus/OneDrive/Desktop/myenv/AIwithHome/AI_final.proj/mapict.jpg")
        background_image = pygame.transform.scale(background_image, (1200, 700))
    except Exception as e:
        print(f"Error loading image: {e}")
        return

    try:
        # Load the marker image to replace the dot
        marker_image = pygame.image.load("C:/Users/Asus/OneDrive/Desktop/myenv/AIwithHome/AI_final.proj/images.png")
        marker_image = pygame.transform.scale(marker_image, (40, 40))  # Resize to appropriate size
    except Exception as e:
        print(f"Error loading marker image: {e}")
        return

    # Return button setup
    button_width, button_height = 150, 50
    margin = 20
    return_button_rect = pygame.Rect(
        (1200 - button_width) // 2,  # Centered horizontally
        margin,  # Positioned with a margin from the top
        button_width,
        button_height
    )

    font = pygame.font.Font(None, 36)  # Define font for the button

    # Main loop
    waiting = True
    current_index = 0  # Index to track the progress of animated markers
    clock = pygame.time.Clock()

    while waiting:
        map_window.fill(WHITE)
        map_window.blit(background_image, (0, 0))

        # Highlight start and destination
        cell_size = 50
        pygame.draw.rect(map_window, (0, 255, 0), (start[0] * cell_size, start[1] * cell_size, cell_size, cell_size))
        pygame.draw.rect(map_window, (255, 0, 0), (destination[0] * cell_size, destination[1] * cell_size, cell_size, cell_size))

        # Draw the moving markers for the path
        for i in range(current_index + 1):
            x, y = path[i]
            # Blit the marker image instead of drawing a circle
            map_window.blit(marker_image, (x * cell_size + cell_size // 4, y * cell_size + cell_size // 4))

        # Increment the current index for animation
        if current_index < len(path) - 1:
            current_index += 1

        # Draw the "Return" button
        mouse_pos = pygame.mouse.get_pos()
        hover = return_button_rect.collidepoint(mouse_pos)
        draw_button_with_outline(
            map_window,
            return_button_rect,
            "Home",
            HOVER_COLOR if hover else BLUE,
            WHITE,
            outline_color=BLACK,
            font=font  # Ensure the font is included
        )

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                if return_button_rect.collidepoint(event.pos):
                    waiting = False
                    home_window()  # Return to the home window

        pygame.display.flip()
        clock.tick(10)  # Adjust the speed of the animation

def draw_button_with_outline(screen, rect, text, bg_color, text_color, outline_color, font):
    pygame.draw.rect(screen, bg_color, rect)
    pygame.draw.rect(screen, outline_color, rect, 2)
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=rect.center)
    screen.blit(text_surf, text_rect)

# Available Rooms Screen
def available_rooms_screen(available_rooms):
    screen_width, screen_height = 1200, 700
    available_window = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Available Rooms")
    
    # Load the background image
    bg_image = pygame.image.load("C:/Users/Asus/OneDrive/Desktop/myenv/AIwithHome/AI_final.proj/AI2.jpg").convert()
    bg_image = pygame.transform.scale(bg_image, (screen_width, screen_height))  # Scale to fit the screen

    button_width = 200
    button_height = 50
    button_spacing = 10
    font = pygame.font.Font(None, 36)

    running = True
    selected_room = None

    # Grid settings
    cols = 3  # Number of columns for the grid
    col_width = button_width + button_spacing
    row_height = button_height + button_spacing

    # Calculate grid start position to center the buttons
    start_x = (screen_width - (col_width * cols - button_spacing)) // 2
    start_y = (screen_height - (row_height * ((len(available_rooms) + cols - 1) // cols) - button_spacing)) // 2

    while running:
        available_window.blit(bg_image, (0, 0))  # Draw the background image
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()[0]
        
        # Event handling
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            # Handling room selection on click
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    for index, room in enumerate(available_rooms):
                        col = index % cols
                        row = index // cols
                        x_pos = start_x + col * col_width
                        y_pos = start_y + row * row_height
                        room_button_rect = pygame.Rect(x_pos, y_pos, button_width, button_height)
                        
                        # Check if the click is inside the button
                        if room_button_rect.collidepoint(mouse_pos):
                            selected_room = room  # Set the selected room
                            print(f"Selected room: {selected_room}")
                            show_map_window_with_guide(selected_room)  # Show the map with guide
                            running = False  # Stop the loop after selection

        # Draw each room button in a grid
        for index, room in enumerate(available_rooms):
            col = index % cols
            row = index // cols
            x_pos = start_x + col * col_width
            y_pos = start_y + row * row_height
            room_button_rect = pygame.Rect(x_pos, y_pos, button_width, button_height)
            hover = room_button_rect.collidepoint(mouse_pos)  # Check if the mouse is hovering
            draw_button_with_outline(
                available_window,
                room_button_rect,
                room,
                BLUE if not hover else (0, 0, 180),  # Change color on hover
                WHITE,
                outline_color=BLACK,
                font=font
            )

        pygame.display.flip()

    pygame.quit()

    # Handle user input for room selection
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    for i, room in enumerate(available_rooms):
                        room_button_rect = pygame.Rect(50, 100 + i * 60, 200, 40)
                        if room_button_rect.collidepoint(event.pos):
                            show_map_window_with_guide(room)

                    waiting = False  # Stop the loop after handling an event


# Draw Dropdown
def draw_dropdown(surface, rect, options, selected_value, border_color, bg_color, font=FONT):
    pygame.draw.rect(surface, border_color, rect, 2)
    draw_text(surface, selected_value, BLACK, rect.x + 10, rect.y + 5, font)

    if options:
        for i, option in enumerate(options):
            dropdown_rect = pygame.Rect(rect.x, rect.y + 40 + i * 40, rect.width, 40)
            pygame.draw.rect(surface, bg_color, dropdown_rect)
            draw_text(surface, option, BLACK, dropdown_rect.x + 10, dropdown_rect.y + 5, font)

def draw_error_message(screen, message):
    font = pygame.font.Font(None, 36)  # Default font and size 36
    text = font.render(message, True, (255, 0, 0))  # Red color for the error message
    screen.blit(text, (100, 250))  # Position the text at (100, 250)

# Function to draw modern buttons with rounded corners and an outline
def draw_button_with_outline(surface, rect, text, bg_color, text_color, outline_color=None, hover=False):
    if outline_color:
        pygame.draw.rect(surface, outline_color, rect, border_radius=10)  # Draw the outline
    pygame.draw.rect(surface, bg_color, rect.inflate(-4, -4), border_radius=10)  # Draw the button (slightly smaller for the outline effect)
    text_obj = FONT.render(text, True, text_color)
    text_rect = text_obj.get_rect(center=rect.center)
    surface.blit(text_obj, text_rect)


# Helper functions for loading GIF frames and drawing UI
def load_gif_frames(gif_path):
    """Load frames from a GIF and convert them to Pygame surfaces."""
    frames = []
    try:
        gif = Image.open(gif_path)
        while True:
            frame = gif.convert("RGBA")
            frame = frame.resize((screen_width, screen_height), Image.LANCZOS)  # Resize to fit the screen
            pygame_image = pygame.image.fromstring(frame.tobytes(), frame.size, frame.mode)
            frames.append(pygame_image)
            gif.seek(gif.tell() + 1)
    except EOFError:
        pass  # End of GIF frames
    return frames

def draw_text(surface, text, color, x, y, font):
    """Draw text on the surface at the specified position."""
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, (x, y))

def draw_button_with_outline(surface, rect, text, bg_color, text_color, outline_color, font=None):
    """Draw a button with an outline."""
    pygame.draw.rect(surface, outline_color, rect.inflate(4, 4))  # Outline
    pygame.draw.rect(surface, bg_color, rect)  # Button background
    if font:
        text_surface = font.render(text, True, text_color)
        surface.blit(text_surface, (rect.x + (rect.width - text_surface.get_width()) // 2,
                                    rect.y + (rect.height - text_surface.get_height()) // 2))

# Main home window function
def home_window():
    """Display the home screen with an animated background and a Get Started button."""
    pygame.init()
    screen_width, screen_height = 1200, 700
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Room Finder - Home")

    # Load GIF frames
    gif_path = "C:/Users/Asus/OneDrive/Desktop/myenv/AIwithHome/AI_final.proj/AI .gif"  # Path to your GIF
    gif_frames = load_gif_frames(gif_path)
    if not gif_frames:
        print("Failed to load GIF frames!")
        return

    current_frame = 0
    frame_delay = 50  # Delay in milliseconds between frames
    last_update = pygame.time.get_ticks()

    welcome_text = ""
    get_started_text = "Get Started"
    button_width, button_height = 200, 60
    LARGE_FONT = pygame.font.Font(None, 48)

    get_started_button_rect = pygame.Rect(
        (screen_width - button_width) // 2,
        (screen_height - button_height) // 2 + 50,
        button_width,
        button_height
    )

    running = True
    while running:
        # Update the frame if enough time has passed
        now = pygame.time.get_ticks()
        if now - last_update > frame_delay:
            current_frame = (current_frame + 1) % len(gif_frames)
            last_update = now

        # Draw the current frame of the GIF
        screen.blit(gif_frames[current_frame], (0, 0))

        # Draw welcome text and button
        draw_text(screen, welcome_text, (0, 0, 0), screen_width // 2 - 100, screen_height // 2 - 50, LARGE_FONT)

        mouse_pos = pygame.mouse.get_pos()
        hover = get_started_button_rect.collidepoint(mouse_pos)
        draw_button_with_outline(
            screen,
            get_started_button_rect,
            get_started_text,
            (173, 216, 230) if hover else (0, 0, 255),  # Hover color: light blue
            (255, 255, 255),
            (0, 0, 0),
            font=LARGE_FONT
        )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if hover:
                    running = False

        pygame.display.flip()

    main()

# Button sizes and positions
button_width = 250
button_height = 40
button_spacing = 40
screen_width, screen_height = 1200, 700

# Center the buttons at the top of the screen
time_button_rect = pygame.Rect((screen_width - button_width) // 2, 50, button_width, button_height)
day_button_rect = pygame.Rect((screen_width - button_width) // 2, time_button_rect.bottom + button_spacing, button_width, button_height)
submit_button_rect = pygame.Rect((screen_width - button_width) // 2, day_button_rect.bottom + button_spacing, button_width, button_height)


# Main program loop
def main():
    timetable = load_csv(TIMETABLE_FILE)
    all_rooms = load_csv(ROOMS_FILE)

    screen_width, screen_height = 1200, 700
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Room Finder")
    
    # Load the background image
    bg_image = pygame.image.load("C:/Users/Asus/OneDrive/Desktop/myenv/AIwithHome/AI_final.proj/AI2.jpg")  # bg image path
    bg_image = pygame.transform.scale(bg_image, (screen_width, screen_height))  # Scale to fit the screen

    # Dropdown options
    times = ["7:00 AM", "8:00 AM", "9:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM", "6:00 PM", "7:00 PM"]
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    selected_time = "Select Time"
    selected_day = "Select Day"

    time_dropdown_open = False
    day_dropdown_open = False

    # Button dimensions and placement
    button_width = 270
    button_height = 40
    button_spacing = 20  # Reduced spacing for top placement

    # Center top alignment
    center_x = screen_width // 2
    center_y = screen_height // 6  # Move elements closer to the top

    time_button_rect = pygame.Rect(center_x - button_width // 2, center_y, button_width, button_height)
    day_button_rect = pygame.Rect(center_x - button_width // 2, center_y + button_height + button_spacing, button_width, button_height)
    submit_button_rect = pygame.Rect(center_x - button_width // 2, center_y + 2 * (button_height + button_spacing), button_width, button_height)

    # Load a font
    font = pygame.font.Font(None, 36)

    running = True
    while running:
        screen.blit(bg_image, (0, 0))  # Draw the background image
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()[0]

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

            if event.type == MOUSEBUTTONDOWN:
                # Time dropdown logic
                if time_button_rect.collidepoint(event.pos):
                    time_dropdown_open = not time_dropdown_open
                    day_dropdown_open = False
                elif time_dropdown_open:
                    for i, time in enumerate(times):
                        dropdown_rect = pygame.Rect(time_button_rect.x, time_button_rect.bottom + i * button_height, button_width, button_height)
                        if dropdown_rect.collidepoint(event.pos):
                            selected_time = time
                            time_dropdown_open = False

                # Day dropdown logic
                if day_button_rect.collidepoint(event.pos):
                    day_dropdown_open = not day_dropdown_open
                    time_dropdown_open = False
                elif day_dropdown_open:
                    for i, day in enumerate(days):
                        dropdown_rect = pygame.Rect(day_button_rect.x, day_button_rect.bottom + i * button_height, button_width, button_height)
                        if dropdown_rect.collidepoint(event.pos):
                            selected_day = day
                            day_dropdown_open = False

        # Draw buttons
        draw_button_with_outline(screen, time_button_rect, selected_time, (0, 0, 255), (255, 255, 255), outline_color=(0, 0, 0), font=font)
        draw_button_with_outline(screen, day_button_rect, selected_day, (0, 0, 255), (255, 255, 255), outline_color=(0, 0, 0), font=font)
        draw_button_with_outline(screen, submit_button_rect, "Find Available Rooms", (0, 0, 255), (255, 255, 255), outline_color=(0, 0, 0), font=font)

        # Draw dropdowns if open
        if time_dropdown_open:
            for i, time in enumerate(times):
                dropdown_rect = pygame.Rect(time_button_rect.x, time_button_rect.bottom + i * button_height, button_width, button_height)
                hover = dropdown_rect.collidepoint(mouse_pos)
                draw_button_with_outline(screen, dropdown_rect, time, (173, 216, 230) if hover else (255, 255, 255), (0, 0, 0), outline_color=(0, 0, 0), font=font)

        if day_dropdown_open:
            for i, day in enumerate(days):
                dropdown_rect = pygame.Rect(day_button_rect.x, day_button_rect.bottom + i * button_height, button_width, button_height)
                hover = dropdown_rect.collidepoint(mouse_pos)
                draw_button_with_outline(screen, dropdown_rect, day, (173, 216, 230) if hover else (255, 255, 255), (0, 0, 0), outline_color=(0, 0, 0), font=font)

        # Submit button logic (moved outside of event handling)
        if submit_button_rect.collidepoint(mouse_pos) and mouse_click:
            if selected_time != "Select Time" and selected_day != "Select Day":
                available_rooms = bfs_csp_search(timetable, all_rooms, selected_time, selected_day)
                available_rooms_screen(available_rooms)
            else:
                print("Error: Please select both time and day.")

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    home_window()