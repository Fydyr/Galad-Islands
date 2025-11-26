"""Simple gamepad test script for Galad Islands.

This script helps you test if your gamepad is properly detected
and working with the game.
"""

import pygame
import sys

def test_gamepad():
    """Test gamepad detection and input."""
    print("=" * 60)
    print("GALAD ISLANDS - GAMEPAD TEST")
    print("=" * 60)
    print()

    # Initialize pygame
    pygame.init()
    pygame.joystick.init()

    # Check for joysticks
    joystick_count = pygame.joystick.get_count()
    print(f"Number of gamepads detected: {joystick_count}")
    print()

    if joystick_count == 0:
        print("❌ No gamepad detected!")
        print()
        print("Troubleshooting:")
        print("1. Make sure your controller is properly connected")
        print("2. Try a different USB port")
        print("3. Check if your controller works in other games")
        print("4. Update your controller drivers")
        return

    # Initialize all joysticks
    joysticks = []
    for i in range(joystick_count):
        joystick = pygame.joystick.Joystick(i)
        joystick.init()
        joysticks.append(joystick)

        print(f"✓ Gamepad {i}: {joystick.get_name()}")
        print(f"  - Buttons: {joystick.get_numbuttons()}")
        print(f"  - Axes: {joystick.get_numaxes()}")
        print(f"  - Hats: {joystick.get_numhats()}")
        print()

    if joysticks:
        active_joystick = joysticks[0]
        print("=" * 60)
        print(f"Testing with: {active_joystick.get_name()}")
        print("=" * 60)
        print()
        print("Press buttons, move sticks, and press triggers.")
        print("Press the START button or Ctrl+C to exit.")
        print()

        # Create a small window
        screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Gamepad Test - Galad Islands")
        clock = pygame.time.Clock()
        font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 20)

        running = True

        try:
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.JOYBUTTONDOWN:
                        print(f"Button {event.button} pressed")
                        # Check for START button (usually button 6)
                        if event.button == 6:
                            print("START button detected - exiting test")
                            running = False
                    elif event.type == pygame.JOYBUTTONUP:
                        print(f"Button {event.button} released")
                    elif event.type == pygame.JOYHATMOTION:
                        print(f"D-Pad: {event.value}")

                # Clear screen
                screen.fill((30, 30, 40))

                # Display title
                title = font.render("Gamepad Test - Galad Islands", True, (255, 255, 255))
                screen.blit(title, (20, 20))

                # Display controller name
                name_text = small_font.render(f"Controller: {active_joystick.get_name()}", True, (200, 200, 200))
                screen.blit(name_text, (20, 60))

                # Display axes (sticks and triggers)
                y_offset = 100
                for i in range(active_joystick.get_numaxes()):
                    value = active_joystick.get_axis(i)
                    axis_names = ["Left X", "Left Y", "Right X", "Right Y", "LT", "RT"]
                    axis_name = axis_names[i] if i < len(axis_names) else f"Axis {i}"

                    # Color code based on value
                    if abs(value) > 0.5:
                        color = (255, 100, 100)  # Red for high values
                    elif abs(value) > 0.2:
                        color = (255, 255, 100)  # Yellow for medium values
                    else:
                        color = (100, 255, 100)  # Green for low values (in deadzone)

                    text = small_font.render(f"{axis_name}: {value:6.3f}", True, color)
                    screen.blit(text, (20, y_offset + i * 25))

                # Display buttons
                y_offset = 100
                button_names = ["A", "B", "X", "Y", "Back", "Guide", "Start",
                               "L-Stick", "R-Stick", "LB", "RB"]

                for i in range(min(active_joystick.get_numbuttons(), 11)):
                    pressed = active_joystick.get_button(i)
                    button_name = button_names[i] if i < len(button_names) else f"Btn {i}"

                    color = (100, 255, 100) if pressed else (150, 150, 150)
                    status = "PRESSED" if pressed else "---"

                    text = small_font.render(f"{button_name:8s}: {status}", True, color)
                    screen.blit(text, (300, y_offset + i * 25))

                # Display D-pad
                if active_joystick.get_numhats() > 0:
                    hat = active_joystick.get_hat(0)
                    hat_text = small_font.render(f"D-Pad: {hat}", True, (255, 255, 100))
                    screen.blit(hat_text, (300, y_offset + 275))

                # Display instructions
                instructions = small_font.render("Press START button or close window to exit", True, (150, 150, 150))
                screen.blit(instructions, (20, 550))

                pygame.display.flip()
                clock.tick(60)

        except KeyboardInterrupt:
            print("\nTest interrupted by user")

        print()
        print("=" * 60)
        print("Test completed!")
        print("=" * 60)

    pygame.quit()


if __name__ == "__main__":
    try:
        test_gamepad()
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

    input("\nPress Enter to exit...")
